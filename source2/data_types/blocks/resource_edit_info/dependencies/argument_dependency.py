import struct
from dataclasses import dataclass
from typing import Any, Union

from SourceIO2.source2.data_types.keyvalues3.types import Object
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

    @classmethod
    def from_vkv3(cls, vkv: Object) -> 'IDependency':
        return cls(vkv['m_ParameterName'], vkv['m_ParameterType'], vkv['m_nFingerprint'], vkv['m_nFingerprintDefault'])


class ArgumentDependencies(IDependencyList[ArgumentDependency]):
    dependency_type = ArgumentDependency
