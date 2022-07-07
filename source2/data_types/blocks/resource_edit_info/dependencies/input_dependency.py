from dataclasses import dataclass

from SourceIO2.source2.data_types.keyvalues3.types import Object
from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class InputDependency(IDependency):
    relative_name: str
    search_path: str
    file_crc: int
    flags: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        rel_name = buffer.read_source2_string()
        search_path = buffer.read_source2_string()
        return cls(rel_name, search_path, *buffer.read_fmt('2I'))

    @classmethod
    def from_vkv3(cls, vkv: Object) -> 'IDependency':
        return cls(vkv['m_RelativeFilename'], vkv['m_SearchPath'], vkv['m_nFileCRC'], 0)


class InputDependencies(IDependencyList[InputDependency]):
    dependency_type = InputDependency


class AdditionalInputDependencies(IDependencyList[InputDependency]):
    dependency_type = InputDependency
