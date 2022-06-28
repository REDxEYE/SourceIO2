from dataclasses import dataclass

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class ExtraData(IDependency):
    name: str


@dataclass(slots=True)
class ExtraIntData(ExtraData):
    value: int

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_source2_string(), buffer.read_int32())


@dataclass(slots=True)
class ExtraFloatData(ExtraData):
    value: float

    @classmethod
    def from_file(cls, buffer: IBuffer):
        return cls(buffer.read_source2_string(), buffer.read_float())


@dataclass(slots=True)
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
