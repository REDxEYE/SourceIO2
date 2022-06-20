from dataclasses import dataclass
from typing import List, Type

from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IFromFile, IBuffer
from SourceIO2.utils.file_utils import T


@dataclass
class ResourceExternalReference(IFromFile):
    resource_hash: int
    r_id: int
    resource_name: str
    unk: int

    def __repr__(self):
        return '<External resource "{}">'.format(self.resource_name)

    @classmethod
    def from_file(cls: T, buffer: IBuffer) -> T:
        return cls(buffer.read_uint32(), buffer.read_uint32(), buffer.read_source2_string(), buffer.read_uint32())


class ResourceExternalReferenceList(List[ResourceExternalReference], BaseBlock):

    def __init__(self, buffer: IBuffer, resource: 'ICompiledResource'):
        list.__init__(self)
        BaseBlock.__init__(self, buffer, resource)

    def __str__(self) -> str:
        str_data = list.__str__(self)
        return f"<ResourceExternalReferenceList  \"{str_data if len(str_data) < 50 else str_data[:50] + '...'}\">"

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource) -> 'ResourceExternalReferenceList':
        offset = buffer.tell() + buffer.read_uint32()
        count = buffer.read_uint32()
        self = cls(buffer, resource)
        with buffer.read_from_offset(offset):
            for _ in range(count):
                self.append(ResourceExternalReference.from_file(buffer))

        return self
