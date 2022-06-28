from dataclasses import dataclass

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class AdditionalRelatedFile(IDependency):
    relative_filename: str
    search_path: str

    @classmethod
    def from_file(cls, buffer: IBuffer):
        rel_name = buffer.read_source2_string()
        search_path = buffer.read_source2_string()
        return cls(rel_name, search_path)


class AdditionalRelatedFiles(IDependencyList[AdditionalRelatedFile]):
    dependency_type = AdditionalRelatedFile
