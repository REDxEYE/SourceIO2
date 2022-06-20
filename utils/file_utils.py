import abc
import binascii
import contextlib
import io
import os
from struct import unpack, calcsize, pack
from typing import overload, TypeVar


class IBuffer(abc.ABC, io.RawIOBase):
    @contextlib.contextmanager
    def save_current_pos(self):
        entry = self.tell()
        yield
        self.seek(entry)

    @contextlib.contextmanager
    def read_from_offset(self, offset: int):
        entry = self.tell()
        self.seek(offset)
        yield
        self.seek(entry)

    @property
    @abc.abstractmethod
    def data(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def size(self):
        raise NotImplementedError()

    @property
    def preview(self):
        with self.save_current_pos():
            return binascii.hexlify(self.read(64), sep=' ', bytes_per_sep=4).decode('ascii').upper()

    def align(self, align_to):
        value = self.tell()
        padding = (align_to - value % align_to) % align_to
        self.seek(padding, io.SEEK_CUR)

    def read_fmt(self, fmt):
        return unpack(fmt, self.read(calcsize(fmt)))

    def _read(self, fmt):
        return unpack(fmt, self.read(calcsize(fmt)))[0]

    def read_uint64(self):
        return self._read('Q')

    def read_int64(self):
        return self._read('q')

    def read_uint32(self):
        return self._read('I')

    def read_int32(self):
        return self._read('i')

    def read_uint16(self):
        return self._read('H')

    def read_int16(self):
        return self._read('h')

    def read_uint8(self):
        return self._read('B')

    def read_int8(self):
        return self._read('b')

    def read_float(self):
        return self._read('f')

    def read_double(self):
        return self._read('d')

    def read_ascii_string(self, length=None):
        if length is not None:
            buffer = self.read(length).strip(b'\x00').rstrip(b'\x00')
            return buffer.decode('latin', errors='replace')

        buffer = bytearray()

        while True:
            chunk = self.read(32)
            if chunk:
                chunk_end = chunk.find(b'\x00')
            else:
                chunk_end = 0
            if chunk_end >= 0:
                buffer += chunk[:chunk_end]
            else:
                buffer += chunk
            if chunk_end >= 0:
                self.seek(-(len(chunk) - chunk_end - 1), io.SEEK_CUR)
                return buffer.decode('latin', errors='replace')

    def read_fourcc(self):
        return self.read_ascii_string(4)

    def read_source1_string(self, entry):
        offset = self.read_int32()
        if offset:
            with self.save_current_pos():
                self.seek(entry + offset)
                return self.read_ascii_string()
        else:
            return ""

    def read_source2_string(self):
        offset = self.tell() + self.read_int32()
        with self.save_current_pos():
            self.seek(offset)
            return self.read_ascii_string()

    def write_fmt(self, fmt: str, *values):
        self.write(pack(fmt, *values))

    def write_uint64(self, value):
        self.write_fmt('Q', value)

    def write_int64(self, value):
        self.write_fmt('q', value)

    def write_uint32(self, value):
        self.write_fmt('I', value)

    def write_int32(self, value):
        self.write_fmt('i', value)

    def write_uint16(self, value):
        self.write_fmt('H', value)

    def write_int16(self, value):
        self.write_fmt('h', value)

    def write_uint8(self, value):
        self.write_fmt('B', value)

    def write_int8(self, value):
        self.write_fmt('b', value)

    def write_float(self, value):
        self.write_fmt('f', value)

    def write_double(self, value):
        self.write_fmt('d', value)

    def write_ascii_string(self, string, zero_terminated=False, length=-1):
        pos = self.tell()
        for c in string:
            self.write(c.encode('ascii'))
        if zero_terminated:
            self.write(b'\x00')
        elif length != -1:
            to_fill = length - (self.tell() - pos)
            if to_fill > 0:
                for _ in range(to_fill):
                    self.write_uint8(0)

    def write_fourcc(self, fourcc):
        self.write_ascii_string(fourcc)


class MemoryBuffer(io.BytesIO, IBuffer):

    def size(self):
        return len(self.getbuffer())

    @property
    def data(self):
        return self.getbuffer()


class FileBuffer(io.FileIO, IBuffer):

    def size(self):
        return os.fstat(self.fileno()).st_size

    @property
    def data(self):
        offset = self.tell()
        self.seek(0)
        _data = self.read()
        self.seek(offset)
        return _data


T = TypeVar('T', bound='IFromFile')


class IFromFile(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_file(cls: T, buffer: IBuffer) -> T:
        ...


__all__ = ['IBuffer', 'MemoryBuffer', 'FileBuffer', 'IFromFile']
