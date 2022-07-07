from dataclasses import dataclass

from SourceIO2.source2.data_types.keyvalues3.types import Object
from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class SpecialDependency(IDependency):
    string: str
    compiler_id: str
    fingerprint: int
    user_data: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        rel_name = buffer.read_source2_string()
        search_path = buffer.read_source2_string()
        return cls(rel_name, search_path, *buffer.read_fmt('2I'))

    @classmethod
    def from_vkv3(cls, vkv: Object) -> 'IDependency':
        return cls(vkv['m_String'], vkv['m_CompilerIdentifier'], vkv['m_nFingerprint'], vkv['m_nUserData'])


class SpecialDependencies(IDependencyList[SpecialDependency]):
    dependency_type = SpecialDependency
