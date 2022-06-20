from dataclasses import dataclass

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass
class ArgumentDependency(IDependency):
    name: str
    type: str
    fingerprint: int
    fingerprint_default: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        rel_name = buffer.read_source2_string()
        search_path = buffer.read_source2_string()
        return cls(rel_name, search_path, *buffer.read_fmt('2I'))


class ArgumentDependencies(IDependencyList[ArgumentDependency]):
    dependency_type = ArgumentDependency
