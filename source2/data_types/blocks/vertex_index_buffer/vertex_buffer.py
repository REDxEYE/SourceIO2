from dataclasses import dataclass
from typing import List

import numpy as np

from SourceIO2.source2.data_types.blocks.vertex_index_buffer.enums import DxgiFormat, SlotType
from SourceIO2.utils import IFromFile, IBuffer
from SourceIO2.utils.file_utils import MemoryBuffer
from SourceIO2.utils.pylib_loader import pylib


class VertexBuffer(IFromFile):
    @staticmethod
    def decode_vertex_buffer(data, size, count):
        return pylib.decode_vertex_buffer(data, len(data), size, count)

    def __init__(self) -> None:
        self._vertex_buffer = MemoryBuffer()
        self.vertex_count = 0
        self.vertex_size = 0
        self.attributes: List[VertexAttribute] = []

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'VertexBuffer':
        self = cls()
        self.vertex_count, self.vertex_size = buffer.read_fmt('2I')
        attr_offset = buffer.read_relative_offset32()
        attr_count = buffer.read_uint32()

        data_offset = buffer.read_relative_offset32()
        data_size = buffer.read_uint32()

        with buffer.read_from_offset(attr_offset):
            for _ in range(attr_count):
                self.attributes.append(VertexAttribute.from_file(buffer))

        with buffer.read_from_offset(data_offset):
            data = buffer.read(data_size)
            if data_size == self.vertex_size * self.vertex_count:
                self._vertex_buffer = MemoryBuffer(data)
            else:
                self._vertex_buffer = MemoryBuffer(self.decode_vertex_buffer(data, self.vertex_size, self.vertex_count))
        return self

    def generate_numpy_dtype(self):
        struct = []
        for attr in self.attributes:
            struct.append((attr.name, *attr.get_numpy_type()))
        return np.dtype(struct)

    def get_vertices(self):
        np_dtype = self.generate_numpy_dtype()
        return np.frombuffer(self._vertex_buffer.data, np_dtype, self.vertex_count)

    def __str__(self) -> str:
        return f'<VertexBuffer ' \
               f'vertices:{self.vertex_count} ' \
               f'attributes:{len(self.attributes)} ' \
               f'vertex size:{self.vertex_size}>'


@dataclass(slots=True)
class VertexAttribute(IFromFile):
    _name: str
    index: int
    format: DxgiFormat
    offset: int
    slot: int
    slot_type: SlotType
    instance_step_rate: int

    @property
    def name(self):
        return self._name
        # if self.index == 0:
        #     return self.name
        # else:
        #     return f'{self._name}_{self.index}'

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'VertexAttribute':
        name = buffer.read_ascii_string(32)
        index, fmt, offset, slot, slot_type, instance_step_rate = buffer.read_fmt('6I')
        return cls(name, index, DxgiFormat(fmt),
                   offset, slot, SlotType(slot_type), instance_step_rate)

    def get_numpy_type(self):
        if self.format == DxgiFormat.R32G32B32_FLOAT:
            return np.float32, (3,)
        elif self.format == DxgiFormat.R32G32_FLOAT:
            return np.float32, (2,)
        elif self.format == DxgiFormat.R32_FLOAT:
            return np.float32, (1,)
        elif self.format == DxgiFormat.R32G32B32_UINT:
            return np.uint32, (3,)
        elif self.format == DxgiFormat.R32G32B32_SINT:
            return np.int32, (3,)
        elif self.format == DxgiFormat.R32G32B32A32_FLOAT:
            return np.float32, (4,)
        elif self.format == DxgiFormat.R32G32B32A32_UINT:
            return np.uint32, (4,)
        elif self.format == DxgiFormat.R32G32B32A32_SINT:
            return np.int32, (3,)
        elif self.format == DxgiFormat.R16G16_FLOAT:
            return np.float16, (2,)
        elif self.format == DxgiFormat.R16G16_SINT:
            return np.int16, (2,)
        elif self.format == DxgiFormat.R16G16_UINT:
            return np.uint16, (2,)
        elif self.format == DxgiFormat.R16G16B16A16_SINT:
            return np.int16, (4,)
        elif self.format == DxgiFormat.R8G8B8A8_SNORM:
            return np.int8, (4,)
        elif self.format == DxgiFormat.R8G8B8A8_UNORM:
            return np.uint8, (4,)
        elif self.format == DxgiFormat.R8G8B8A8_UINT:
            return np.uint8, (4,)
        elif self.format == DxgiFormat.R16G16_UNORM:
            return np.uint16, (2,)
        else:
            raise NotImplementedError(f"Unsupported DXGI format {self.format.name}")
