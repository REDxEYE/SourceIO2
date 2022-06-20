from dataclasses import dataclass

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass
class CustomDependency(IDependency):
    @classmethod
    def from_file(cls, buffer: IBuffer):
        raise NotImplementedError('Unsupported, if found please report to ValveResourceFormat repo and to SourceIO2')


class CustomDependencies(IDependencyList[CustomDependency]):
    dependency_type = CustomDependency
