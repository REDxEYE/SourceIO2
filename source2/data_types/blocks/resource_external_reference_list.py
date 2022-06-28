from dataclasses import dataclass
from typing import List, Type, Dict

from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IFromFile, IBuffer


@dataclass(slots=True)
class ResourceExternalReference(IFromFile):
    hash: int
    r_id: int
    name: str
    unk: int

    def __repr__(self):
        return '<External resource "{}">'.format(self.name)

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_uint32(), buffer.read_uint32(), buffer.read_source2_string(), buffer.read_uint32())


class ResourceExternalReferenceList(List[ResourceExternalReference], BaseBlock):

    def __init__(self, buffer: IBuffer, resource: 'ICompiledResource'):
        list.__init__(self)
        BaseBlock.__init__(self, buffer, resource)
        self._mapping: Dict[int, ResourceExternalReference] = {}

    def __str__(self) -> str:
        str_data = list.__str__(self)
        return f"<ResourceExternalReferenceList  \"{str_data if len(str_data) < 50 else str_data[:50] + '...'}\">"

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource) -> 'ResourceExternalReferenceList':
        offset = buffer.read_relative_offset32()
        count = buffer.read_uint32()
        self = cls(buffer, resource)
        with buffer.read_from_offset(offset):
            for _ in range(count):
                ref = ResourceExternalReference.from_file(buffer)
                self._mapping[ref.hash] = ref
                self.append(ref)

        return self

    def find_resource(self, resource_id: int):
        if res := self._mapping.get(resource_id & 0xFFFF_FFFF, None):
            return res.name
