from dataclasses import dataclass

from SourceIO2.utils import IBuffer, IFromFile


@dataclass
class ResourceHeader(IFromFile):
    file_size: int
    header_version: int
    resource_version: int
    block_info_offset: int
    block_count: int

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'ResourceHeader':
        self = ResourceHeader(*buffer.read_fmt('I2H'), buffer.tell() + buffer.read_uint32(), buffer.read_uint32())
        assert self.header_version == 12
        return self
