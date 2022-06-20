from dataclasses import dataclass

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass
class ExtraData(IDependency):
    name: str


@dataclass
class ExtraIntData(ExtraData):
    value: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_source2_string(), buffer.read_uint32())


@dataclass
class ExtraFloatData(ExtraData):
    value: float

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_source2_string(), buffer.read_float())


@dataclass
class ExtraStringData(ExtraData):
    value: str

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_source2_string(), buffer.read_source2_string())


class ExtraInts(IDependencyList[ExtraIntData]):
    dependency_type = ExtraIntData


class ExtraFloats(IDependencyList[ExtraFloatData]):
    dependency_type = ExtraFloatData


class ExtraStrings(IDependencyList[ExtraStringData]):
    dependency_type = ExtraStringData
