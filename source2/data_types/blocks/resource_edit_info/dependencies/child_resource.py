from dataclasses import dataclass

from SourceIO2.source2.data_types.keyvalues3.types import Object, String
from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class ChildResource(IDependency):
    id: int
    name: str
    unk: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_uint64(), buffer.read_source2_string(), buffer.read_uint32())

    @classmethod
    def from_vkv3(cls, vkv: String) -> 'IDependency':
        return cls(-1, vkv, -1)


class ChildResources(IDependencyList[ChildResource]):
    dependency_type = ChildResource
