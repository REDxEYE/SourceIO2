from dataclasses import dataclass

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


class ChildResources(IDependencyList[ChildResource]):
    dependency_type = ChildResource
