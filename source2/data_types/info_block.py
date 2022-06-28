from dataclasses import dataclass

from SourceIO2.utils import IBuffer, IFromFile


@dataclass(slots=True)
class InfoBlock(IFromFile):
    name: str
    offset: int
    size: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        name = buffer.read_ascii_string(4)
        block_offset = buffer.read_relative_offset32()
        block_size = buffer.read_uint32()
        return cls(name, block_offset, block_size)

    def to_file(self, buffer: IBuffer):
        buffer.write_ascii_string(self.name)
        buffer.write_uint32(buffer.tell() - self.offset)
        buffer.write_uint32(self.size)
