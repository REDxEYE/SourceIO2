from dataclasses import dataclass
from typing import List

from SourceIO2.source2.data_types.header import ResourceHeader
from SourceIO2.utils import IBuffer


@dataclass
class InfoBlock:
    name: str
    offset: int
    size: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        name = buffer.read_ascii_string(4)
        block_offset = buffer.tell() + buffer.read_uint32()
        block_size = buffer.read_uint32()
        return cls(name, block_offset, block_size)

    def to_file(self, buffer: IBuffer):
        buffer.write_ascii_string(self.name)
        buffer.write_uint32(buffer.tell() - self.offset)
        buffer.write_uint32(self.size)


class GenericCompiledResource:

    def __init__(self, file: IBuffer):
        self._buffer = file
        self._header: ResourceHeader = ResourceHeader(0, 0, 0, 0, 0)

        self._blocks: List[InfoBlock] = []

    @classmethod
    def from_file(cls, buffer: IBuffer):
        self = cls(buffer)
        self._header = ResourceHeader.from_file(buffer)
        buffer.seek(self._header.block_info_offset)
        self._blocks = [InfoBlock.from_file(buffer) for _ in range(self._header.block_count)]
        return self

    def __del__(self):
        self._buffer.close()
