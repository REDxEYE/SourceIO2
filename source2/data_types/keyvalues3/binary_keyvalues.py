from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Union, Any

import numpy as np

from SourceIO2.source2.data_types.keyvalues3.enums import *
from SourceIO2.source2.data_types.keyvalues3.types import *
from SourceIO2.utils.file_utils import IBuffer, MemoryBuffer, FileBuffer
from SourceIO2.utils.pylib_loader import pylib
from SourceIO2.utils.thirdparty.zstandard import ZstdDecompressor, ZstdCompressor

lz4_decompress = pylib.lz4.decompress
lz4_compress = pylib.lz4.compress
LZ4ChainDecoder = pylib.lz4.LZ4ChainDecoder


class UnsupportedVersion(Exception):
    pass


@dataclass(slots=True)
class BufferGroup:
    byte_buffer: IBuffer
    int_buffer: IBuffer
    double_buffer: IBuffer
    type_buffer: IBuffer
    blocks_buffer: Optional[IBuffer]


def _block_decompress(in_buffer: IBuffer) -> IBuffer:
    out_buffer = MemoryBuffer()
    flags = in_buffer.read(4)
    if flags[3] & 0x80:
        out_buffer.write(in_buffer.read(-1))
    working = True
    while in_buffer.tell() != in_buffer.size() and working:
        block_mask = in_buffer.read_uint16()
        for i in range(16):
            if block_mask & (1 << i) > 0:
                offset_and_size = in_buffer.read_uint16()
                offset = ((offset_and_size & 0xFFF0) >> 4) + 1
                size = (offset_and_size & 0x000F) + 3
                lookup_size = offset if offset < size else size

                entry = out_buffer.tell()
                out_buffer.seek(entry - offset)
                data = out_buffer.read(lookup_size)
                out_buffer.seek(entry)
                while size > 0:
                    out_buffer.write(data[:lookup_size if lookup_size < size else size])
                    size -= lookup_size
            else:
                data = in_buffer.read_int8()
                out_buffer.write_int8(data)
            if out_buffer.size() == (flags[2] << 16) + (flags[1] << 8) + flags[0]:
                working = False
                break
    out_buffer.seek(0)
    return out_buffer


def _decompress_lz4(in_buffer: IBuffer) -> IBuffer:
    decompressed_size = in_buffer.read_uint32()
    compressed_size = in_buffer.size() - in_buffer.tell()
    return MemoryBuffer(lz4_decompress(in_buffer.read(-1), compressed_size, decompressed_size))


class BinaryKeyValues:
    def __init__(self, version: KV3Signatures):
        self.version = version
        self.format = KV3Formats.KV3_FORMAT_GENERIC
        self.root = Object()

    def __str__(self) -> str:
        return f'<KV3 {self.version.name}>({self.root!s})'

    @classmethod
    def from_file(cls, buffer: IBuffer):
        sig = buffer.read(4)
        if not KV3Signatures.is_valid(sig):
            raise BufferError("Not a KV3 buffer")
        sig = KV3Signatures(sig)
        self = cls(sig)
        if sig == KV3Signatures.V2:
            self._read_v2(buffer)
        elif sig == KV3Signatures.V3:
            self._read_v3(buffer)
        elif sig == KV3Signatures.V1:
            self._read_v1(buffer)
        return self

    def to_file(self, buffer: IBuffer, version: Optional[KV3Signatures] = None, **kwargs):
        version = version or self.version or KV3Signatures.V3
        if version == KV3Signatures.V1:
            self._write_v1(buffer, **kwargs)
        elif version == KV3Signatures.V2:
            raise NotImplementedError
            # self._write_v2(buffer, **kwargs)
        elif version == KV3Signatures.V3:
            self._write_v3(buffer, **kwargs)
        else:
            raise UnsupportedVersion()

    @staticmethod
    def _read_type(buffer: IBuffer) -> Tuple[KV3Type, KV3TypeFlag]:
        data_type = buffer.read_uint8()

        if data_type & 0x80:
            data_type &= 0x7F
            flag = KV3TypeFlag(buffer.read_uint8())
        else:
            flag = KV3TypeFlag.NONE
        return KV3Type(data_type), flag

    def _read_array(self, size: int, buffers: BufferGroup,
                    strings: List[str], block_sizes: List[int],
                    data_type: Optional[KV3Type], data_flag: Optional[KV3TypeFlag]):
        if data_type == KV3Type.DOUBLE_ZERO:
            return np.zeros(size, np.float64)
        elif data_type == KV3Type.DOUBLE_ONE:
            return np.ones(size, np.float64)
        elif data_type == KV3Type.INT64_ZERO:
            return np.zeros(size, np.int64)
        elif data_type == KV3Type.INT64_ONE:
            return np.ones(size, np.int64)
        elif data_type == KV3Type.DOUBLE:
            return np.frombuffer(buffers.double_buffer.read(8 * size), np.float64)
        elif data_type == KV3Type.INT64:
            return np.frombuffer(buffers.double_buffer.read(8 * size), np.int64)
        elif data_type == KV3Type.UINT64:
            return np.frombuffer(buffers.double_buffer.read(8 * size), np.uint64)
        elif data_type == KV3Type.INT32:
            return np.frombuffer(buffers.int_buffer.read(4 * size), np.int32)
        elif data_type == KV3Type.UINT32:
            return np.frombuffer(buffers.int_buffer.read(4 * size), np.uint32)
        else:
            return TypedArray(data_type, data_flag, [
                self._read_value(buffers, strings, block_sizes, data_type, data_flag) for _ in range(size)])

    def _read_value(self, buffers: BufferGroup, strings: List[str], block_sizes: List[int],
                    data_type: Optional[KV3Type], data_flag: Optional[KV3TypeFlag]):

        if data_type == KV3Type.NULL:
            return NullObject()
        elif data_type == KV3Type.OBJECT:
            attribute_count = buffers.int_buffer.read_uint32()
            obj = Object()
            for _ in range(attribute_count):
                name_id = buffers.int_buffer.read_int32()
                name = strings[name_id] if name_id != -1 else ""
                obj[name] = self._read_value(buffers, strings, block_sizes, *self._read_type(buffers.type_buffer))
            return obj
        elif data_type == KV3Type.STRING:
            str_id = buffers.int_buffer.read_int32()
            string = String(strings[str_id]) if str_id >= 0 else String("")
            string.flag = data_flag
            return string
        elif data_type == KV3Type.INT32:
            return Int32(buffers.int_buffer.read_int32())
        elif data_type == KV3Type.ARRAY_TYPED:
            size = buffers.int_buffer.read_uint32()
            return self._read_array(size, buffers, strings, block_sizes, *self._read_type(buffers.type_buffer))
        elif data_type == KV3Type.ARRAY:
            size = buffers.int_buffer.read_uint32()
            return Array(
                [self._read_value(buffers, strings, block_sizes, *self._read_type(buffers.type_buffer)) for _ in
                 range(size)])
        elif data_type == KV3Type.DOUBLE_ZERO:
            return Double(0)
        elif data_type == KV3Type.DOUBLE_ONE:
            return Double(1)
        elif data_type == KV3Type.DOUBLE:
            return Double(buffers.double_buffer.read_double())
        elif data_type == KV3Type.INT64_ZERO:
            return Int64(0)
        elif data_type == KV3Type.INT64_ONE:
            return Int64(1)
        elif data_type == KV3Type.INT64:
            return Int64(buffers.double_buffer.read_uint64())
        elif data_type == KV3Type.BOOLEAN_FALSE:
            return Bool(False)
        elif data_type == KV3Type.BOOLEAN_TRUE:
            return Bool(True)
        elif data_type == KV3Type.BOOLEAN:
            return Bool(buffers.byte_buffer.read_uint8() == 1)
        elif data_type == KV3Type.BINARY_BLOB:
            if buffers.blocks_buffer:
                return BinaryBlob(buffers.blocks_buffer.read(block_sizes.pop(0)))
            else:
                return BinaryBlob(buffers.byte_buffer.read(buffers.int_buffer.read_int32()))
        else:
            raise NotImplementedError(f'Data type: {data_type!r}:{data_flag!r} not implemented')

    def _read_v1(self, buffer: IBuffer):
        encoding = buffer.read(16)
        if not KV3Encodings.is_valid(encoding):
            raise BufferError(f'Buffer contains unknown encoding: {encoding!r}')
        encoding = KV3Encodings(encoding)
        self.format = buffer.read(16)
        # assert fmt in KV3Formats
        if encoding == KV3Encodings.KV3_ENCODING_BINARY_UNCOMPRESSED:
            data_buffer = MemoryBuffer(buffer.read())
        elif encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_COMPRESSED:
            data_buffer = _block_decompress(buffer)
        elif encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_LZ4:
            data_buffer = _decompress_lz4(buffer)
        else:
            raise Exception('Should not reach here')
        del buffer
        string_count = data_buffer.read_uint32()
        strings = [data_buffer.read_ascii_string() for _ in range(string_count)]

        bg = BufferGroup(data_buffer, data_buffer, data_buffer, data_buffer, None)

        self.root = self._read_value(bg, strings, [], *self._read_type(data_buffer))

    def _read_v2(self, buffer: IBuffer):
        self.format = buffer.read(16)
        # assert fmt in KV3Formats

        compression_method = buffer.read_uint32()

        bin_blob_count = buffer.read_uint32()
        int_count = buffer.read_uint32()
        double_count = buffer.read_uint32()

        uncompressed_size = buffer.read_uint32()

        if compression_method == 0:
            data_buffer = MemoryBuffer(buffer.read(uncompressed_size))
        elif compression_method == 1:
            compressed_size = buffer.size() - buffer.tell()
            data = buffer.read(compressed_size)
            u_data = lz4_decompress(data, compressed_size, uncompressed_size)
            assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
            data_buffer = MemoryBuffer(u_data)
            del u_data, data
        else:
            raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

        byte_buffer = MemoryBuffer(data_buffer.read(bin_blob_count))
        data_buffer.align(4)

        int_buffer = MemoryBuffer(data_buffer.read(int_count * 4))

        data_buffer.align(8)

        double_buffer = MemoryBuffer(data_buffer.read(double_count * 8))

        strings = [data_buffer.read_ascii_string() for _ in range(int_buffer.read_uint32())]
        # noinspection PyTypeChecker
        types_buffer = MemoryBuffer(data_buffer.read())

        bg = BufferGroup(byte_buffer, int_buffer, double_buffer, types_buffer, None)
        self.root = self._read_value(bg, strings, [], *self._read_type(types_buffer))

    def _read_v3(self, buffer: IBuffer):
        self.format = buffer.read(16)
        # assert fmt in KV3Formats

        compression_method = buffer.read_uint32()
        compression_dict_id = buffer.read_uint16()
        compression_frame_size = buffer.read_uint16()

        bin_blob_count = buffer.read_uint32()
        int_count = buffer.read_uint32()
        double_count = buffer.read_uint32()

        strings_types_size, object_count, array_count = buffer.read_fmt('I2H')

        uncompressed_size = buffer.read_uint32()
        compressed_size = buffer.read_uint32()
        block_count = buffer.read_uint32()
        block_total_size = buffer.read_uint32()

        if compression_method == 0:
            if compression_dict_id != 0:
                raise NotImplementedError('Unknown compression method in KV3 v2 block')
            if compression_frame_size != 0:
                raise NotImplementedError('Unknown compression method in KV3 v2 block')
            data_buffer = MemoryBuffer(buffer.read(compressed_size))
        elif compression_method == 1:

            if compression_dict_id != 0:
                raise NotImplementedError('Unknown compression method in KV3 v2 block')

            if compression_frame_size != 16384:
                raise NotImplementedError('Unknown compression method in KV3 v2 block')

            data = buffer.read(compressed_size)
            u_data = lz4_decompress(data, compressed_size, uncompressed_size)
            assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
            data_buffer = MemoryBuffer(u_data)
            del u_data, data
        elif compression_method == 2:
            data = buffer.read(compressed_size)
            decompressor = ZstdDecompressor()
            tmp = MemoryBuffer()
            decompressor.copy_stream(MemoryBuffer(data), tmp, compressed_size, uncompressed_size)
            tmp.seek(0)
            u_data = tmp.read()
            assert len(
                u_data) == uncompressed_size + block_total_size, "Decompressed data size does not match expected size"
            data_buffer = MemoryBuffer(u_data)
            del u_data, data
        else:
            raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

        byte_buffer = MemoryBuffer(data_buffer.read(bin_blob_count))
        data_buffer.align(4)

        int_buffer = MemoryBuffer(data_buffer.read(int_count * 4))

        data_buffer.align(8)

        double_buffer = MemoryBuffer(data_buffer.read(double_count * 8))

        string_start = data_buffer.tell()

        strings = [data_buffer.read_ascii_string() for _ in range(int_buffer.read_uint32())]
        # noinspection PyTypeChecker
        types_buffer = MemoryBuffer(
            data_buffer.read(strings_types_size - (data_buffer.tell() - string_start)))

        if block_count == 0:
            block_sizes = []
            assert data_buffer.read_uint32() == 0xFFEEDD00
            block_reader = None

        else:
            block_sizes = [data_buffer.read_uint32() for _ in range(block_count)]
            assert data_buffer.read_uint32() == 0xFFEEDD00
            block_data = b''
            if compression_method == 0:
                for uncompressed_block_size in block_sizes:
                    block_data += buffer.read(uncompressed_block_size)
            elif compression_method == 1:
                cd = LZ4ChainDecoder(block_total_size, 0)
                for uncompressed_block_size in block_sizes:
                    compressed_block_size = data_buffer.read_uint16()
                    block_data += cd.decompress(buffer.read(compressed_block_size), uncompressed_block_size)
            elif compression_method == 2:
                block_data += data_buffer.read()
            else:
                raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")
            block_reader = MemoryBuffer(block_data)

        bg = BufferGroup(byte_buffer, int_buffer, double_buffer, types_buffer, block_reader)
        self.root = self._read_value(bg, strings, block_sizes, *self._read_type(types_buffer))

    def _collect_data(self, node: Union[Object, Array, TypedArray]):
        strings = set()
        objects = 0
        arrays = 0

        def get_strings(node: Any):
            if isinstance(node, str):
                if len(node) == 0:
                    return set(), 0, 0
                return {node}, 0, 0
            elif isinstance(node, Object):
                return self._collect_data(node)
            elif isinstance(node, Array):
                return self._collect_data(node)
            elif isinstance(node, TypedArray):
                return self._collect_data(node)
            elif isinstance(node, np.ndarray):
                return set(), 0, 1
            else:
                return set(), 0, 0

        if isinstance(node, Object):
            objects += 1
            for k, v in node.items():
                strings.add(k)
                s, o, a = get_strings(v)
                strings.update(s)
                objects += o
                arrays += a
        elif isinstance(node, (Array, TypedArray)):
            arrays += 1
            for i in node:
                s, o, a = get_strings(i)
                strings.update(s)
                objects += o
                arrays += a
        return list(strings), objects, arrays

    @staticmethod
    def _write_type(buffer: IBuffer, type: KV3Type, flag: KV3TypeFlag = KV3TypeFlag.NONE):
        if flag == KV3TypeFlag.NONE:
            buffer.write_uint8(type.value)
        else:
            buffer.write_uint8(type.value | 0x80)
            buffer.write_uint8(flag)

    @staticmethod
    def _write_string(buffer: IBuffer, strings, string):
        if len(string) == 0:
            buffer.write_int32(-1)
        else:
            buffer.write_int32(strings.index(string))

    def _write_value(self, buffers: BufferGroup, strings: List[str], value: BaseType, write_type_id=True):
        if isinstance(value, (String, str)):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.STRING, value.flag)
            self._write_string(buffers.int_buffer, strings, value)
        elif isinstance(value, Object):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.OBJECT)
            buffers.int_buffer.write_int32(len(value))
            for k, v in value.items():
                self._write_string(buffers.int_buffer, strings, k)
                self._write_value(buffers, strings, v)
                pass
        elif isinstance(value, Int32):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.INT32)
            buffers.int_buffer.write_int32(value)
        elif isinstance(value, UInt32):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.UINT32)
            buffers.int_buffer.write_uint32(value)
        elif isinstance(value, np.ndarray):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.ARRAY_TYPED)
            buffers.int_buffer.write_int32(value.size)
            if value.dtype == np.float64:
                is_zeros = (value == 0.0).all()
                is_ones = (value == 1.0).all()
                if is_zeros:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE_ZERO)
                elif is_ones:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE_ONE)
                else:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE)
                    buffers.double_buffer.write(value.tobytes())
            elif value.dtype == np.int64:
                is_zeros = (value == 0).all()
                is_ones = (value == 1).all()
                if is_zeros:
                    self._write_type(buffers.type_buffer, KV3Type.INT64_ZERO)
                elif is_ones:
                    self._write_type(buffers.type_buffer, KV3Type.INT64_ONE)
                else:
                    self._write_type(buffers.type_buffer, KV3Type.INT64)
                    buffers.double_buffer.write(value.tobytes())
            elif value.dtype == np.uint64:
                self._write_type(buffers.type_buffer, KV3Type.UINT64)
                buffers.double_buffer.write(value.tobytes())
            elif value.dtype == np.int32:
                self._write_type(buffers.type_buffer, KV3Type.INT32)
                buffers.int_buffer.write(value.tobytes())
            elif value.dtype == np.uint32:
                self._write_type(buffers.type_buffer, KV3Type.UINT32)
                buffers.int_buffer.write(value.tobytes())
            else:
                raise NotImplementedError(f'Numpy type: {value.dtype} is not implemented')
        elif isinstance(value, Int64):
            if write_type_id:
                if value == 0:
                    self._write_type(buffers.type_buffer, KV3Type.INT64_ZERO)
                    return
                elif value == 1:
                    self._write_type(buffers.type_buffer, KV3Type.INT64_ONE)
                    return
                else:
                    self._write_type(buffers.type_buffer, KV3Type.INT64)
            buffers.double_buffer.write_int64(value)
        elif isinstance(value, Double):
            if write_type_id:
                if value == 0.0:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE_ZERO)
                    return
                elif value == 1.0:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE_ONE)
                    return
                else:
                    self._write_type(buffers.type_buffer, KV3Type.DOUBLE)
            buffers.double_buffer.write_double(value)
        elif isinstance(value, Array):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.ARRAY)
            buffers.int_buffer.write_int32(len(value))
            [self._write_value(buffers, strings, v) for v in value]
        elif isinstance(value, TypedArray):
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.ARRAY_TYPED)
            buffers.int_buffer.write_int32(len(value))
            self._write_type(buffers.type_buffer, value.data_type)
            [self._write_value(buffers, strings, v, False) for v in value]
        elif isinstance(value, NullObject) or value is None:
            if write_type_id:
                self._write_type(buffers.type_buffer, KV3Type.NULL)
        else:
            raise NotImplementedError(f'Type: {type(value)} is not implemented')

    def _write_v1(self, buffer: IBuffer, encoding=KV3Encodings.KV3_ENCODING_BINARY_UNCOMPRESSED):
        assert encoding.value in KV3Encodings
        buffer.write(KV3Signatures.V1.value)
        buffer.write(encoding.value)
        buffer.write(self.format or KV3Formats.KV3_FORMAT_GENERIC.value)
        if encoding == KV3Encodings.KV3_ENCODING_BINARY_UNCOMPRESSED:
            tmp_buff = buffer
        elif encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_COMPRESSED:
            raise NotImplementedError(f'Encoding {encoding!r} is not supported')
        else:
            tmp_buff = MemoryBuffer()

        strings, object_count, array_count = self._collect_data(self.root)
        tmp_buff.write_int32(len(strings))
        [tmp_buff.write_ascii_string(s, True) for s in strings]

        bg = BufferGroup(tmp_buff, tmp_buff, tmp_buff, tmp_buff, None)

        self._write_value(bg, strings, self.root)

        if encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_LZ4:
            buffer.write_uint32(tmp_buff.size())
            tmp_buff.seek(0)
            buffer.write(lz4_compress(tmp_buff.read()))

    def _write_v2(self, buffer: IBuffer, compression_method: KV3CompressionMethod = KV3CompressionMethod.UNCOMPRESSED):
        buffer.write(KV3Signatures.V2.value)
        buffer.write(KV3Formats.KV3_FORMAT_GENERIC.value)
        if compression_method.value > 1:
            raise NotImplementedError(f'Compression {compression_method!r} not supported by V2 format')
        buffer.write_uint32(compression_method.value)

        tmp_buff = MemoryBuffer()
        byte_buff = MemoryBuffer()
        int_buff = MemoryBuffer()
        double_buff = MemoryBuffer()
        type_buff = MemoryBuffer()

        strings, object_count, array_count = self._collect_data(self.root)
        int_buff.write_uint32(len(strings))

        bg = BufferGroup(byte_buff, int_buff, double_buff, type_buff, None)
        self._write_value(bg, strings, self.root)

        buffer.write_uint32(byte_buff.size())
        buffer.align(4)
        buffer.write_uint32(int_buff.size() // 4)
        buffer.align(8)
        buffer.write_uint32(double_buff.size() // 8)
        byte_buff.seek(0)
        int_buff.seek(0)
        double_buff.seek(0)

        tmp_buff.write(byte_buff.read())
        tmp_buff.align(4)
        tmp_buff.write(int_buff.read())
        tmp_buff.align(8)
        tmp_buff.write(double_buff.read())
        [tmp_buff.write_ascii_string(s, True) for s in strings]
        tmp_buff.write(type_buff.data)

        buffer.write_fmt('I2H', sum(map(len, strings)) + len(strings) + type_buff.size(), object_count, array_count)
        tmp_buff.seek(0)
        if compression_method == KV3CompressionMethod.UNCOMPRESSED:
            buffer.write_fmt('4I', tmp_buff.size(), tmp_buff.size(), 0, 0)
            buffer.write(tmp_buff.data)
        elif compression_method == KV3CompressionMethod.LZ4:
            compressed_data = lz4_compress(tmp_buff.read())
            buffer.write_fmt('4I', tmp_buff.size(), len(compressed_data), 0, 0)
            buffer.write(compressed_data)
        else:
            raise Exception(f'Unknown compression method: {compression_method}')

    def _write_v3(self, buffer: IBuffer, compression_method: KV3CompressionMethod = KV3CompressionMethod.UNCOMPRESSED):

        buffer.write(KV3Signatures.V3.value)
        buffer.write(KV3Formats.KV3_FORMAT_GENERIC.value)

        buffer.write_uint32(compression_method.value)

        if compression_method == KV3CompressionMethod.UNCOMPRESSED:
            buffer.write_uint32(0)
        elif compression_method == KV3CompressionMethod.LZ4:
            buffer.write_fmt('2H', 0, 16384)
        elif compression_method == KV3CompressionMethod.ZSTD:
            buffer.write_uint32(0)
        else:
            raise Exception(f'Unknown compression method: {compression_method}')

        tmp_buff = MemoryBuffer()
        byte_buff = MemoryBuffer()
        int_buff = MemoryBuffer()
        double_buff = MemoryBuffer()
        type_buff = MemoryBuffer()

        strings, object_count, array_count = self._collect_data(self.root)
        int_buff.write_uint32(len(strings))

        bg = BufferGroup(byte_buff, int_buff, double_buff, type_buff, None)
        self._write_value(bg, strings, self.root)

        buffer.write_uint32(byte_buff.size())
        buffer.write_uint32(int_buff.size() // 4)
        buffer.write_uint32(double_buff.size() // 8)

        byte_buff.seek(0)
        int_buff.seek(0)
        double_buff.seek(0)

        tmp_buff.write(byte_buff.read())
        tmp_buff.align(4)
        tmp_buff.write(int_buff.read())
        tmp_buff.align(8)
        tmp_buff.write(double_buff.read())
        [tmp_buff.write_ascii_string(s, True) for s in strings]
        tmp_buff.write(type_buff.data)
        tmp_buff.write_uint32(0xFFEEDD00)

        buffer.write_fmt('I2H', sum(map(len, strings)) + len(strings) + type_buff.size(), object_count, array_count)
        tmp_buff.seek(0)
        if compression_method == KV3CompressionMethod.UNCOMPRESSED:
            buffer.write_fmt('4I', tmp_buff.size(), tmp_buff.size(), 0, 0)
            buffer.write(tmp_buff.data)
        elif compression_method == KV3CompressionMethod.LZ4:
            compressed_data = lz4_compress(tmp_buff.read())
            buffer.write_fmt('4I', tmp_buff.size(), len(compressed_data), 0, 0)
            buffer.write(compressed_data)
        elif compression_method == KV3CompressionMethod.ZSTD:
            compressor = ZstdCompressor()
            compressed_data = compressor.compress(tmp_buff.read())
            buffer.write_fmt('4I', tmp_buff.size(), len(compressed_data), 0, 0)
            buffer.write(compressed_data)
        else:
            raise Exception(f'Unknown compression method: {compression_method}')


def read_keyvalues(buffer: IBuffer) -> BinaryKeyValues:
    return BinaryKeyValues.from_file(buffer)


if __name__ == '__main__':
    data = read_keyvalues(
        FileBuffer(
            Path(r"C:\PYTHON_PROJECTS\SourceIOPlugin\test_data\vkv3\dplus_teardrop_of_winterwood_misc.vmdl_c.kv3"),
            'rb'))
    print(data)
    data = read_keyvalues(
        FileBuffer(Path(r"C:\PYTHON_PROJECTS\SourceIOPlugin\test_data\vkv3\earthshaker_arcana_loadout.vpcf_c.kv3"),
                   'rb'))
    print(data)
    byte_io = MemoryBuffer()
    data.to_file(byte_io, KV3Signatures.V3, )  # compression_method=KV3CompressionMethod.ZSTD)
    byte_io.seek(0)
    data2 = read_keyvalues(byte_io)
    print(data2)
    # with open('./aghsbp_2021_drow_misc.vmdl_c.kv3.w', 'wb') as f:
    #     byte_io.seek(0)
    #     f.write(byte_io.read())
    # for file in Path('./test_data/vkv3').glob('*.kv3'):
    #     print(file)
    #     print((read_keyvalues(FileBuffer(file))).version)
