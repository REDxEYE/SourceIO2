import abc
from abc import ABC
from typing import TypeVar, List

from SourceIO2.source2.data_types.keyvalues3.types import Object, TypedArray
from SourceIO2.utils import IBuffer, IFromFile


class IDependency(IFromFile, ABC):
    @classmethod
    @abc.abstractmethod
    def from_file(cls, buffer: IBuffer) -> 'IDependency':
        pass

    @classmethod
    @abc.abstractmethod
    def from_vkv3(cls, vkv: Object) -> 'IDependency':
        pass


T = TypeVar('T', bound=IDependency)


class IDependencyList(List[T], IFromFile):
    dependency_type: T = IDependency
    _vkv_key = 'FILL ME'

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'IDependencyList':
        self = cls()
        offset = buffer.read_relative_offset32()
        size = buffer.read_uint32()
        with buffer.read_from_offset(offset):
            for _ in range(size):
                self.append(cls.dependency_type.from_file(buffer))

        return self

    @classmethod
    def from_vkv3(cls, vkv: TypedArray[Object]):
        self = cls()
        for dependency in vkv:
            self.append(cls.dependency_type.from_vkv3(dependency))
        return self