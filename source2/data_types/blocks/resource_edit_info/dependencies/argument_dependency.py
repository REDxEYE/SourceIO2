import struct
from dataclasses import dataclass
from typing import Any, Union

from SourceIO2.utils import IBuffer
from .idependency import IDependency, IDependencyList


@dataclass(slots=True)
class ArgumentDependency(IDependency):
    name: str
    type: str
    fingerprint: Union[int, float]
    fingerprint_default: Union[int, float]

    @classmethod
    def from_file(cls, buffer: IBuffer):
        name = buffer.read_source2_string()
        data_type = buffer.read_source2_string()
        if data_type == 'FloatArg':
            data = buffer.read_fmt('2f')
        else:
            data = buffer.read_fmt('2I')
        return cls(name, data_type, *data)


class ArgumentDependencies(IDependencyList[ArgumentDependency]):
    dependency_type = ArgumentDependency
