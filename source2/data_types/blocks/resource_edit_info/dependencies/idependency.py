from abc import ABC
from typing import TypeVar, List

from SourceIO2.utils import IBuffer, IFromFile


class IDependency(IFromFile, ABC):
    ...


T = TypeVar('T', bound=IDependency)


class IDependencyList(List[T], IFromFile):
    dependency_type: T = IDependency

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'IDependencyList':
        self = cls()
        offset = buffer.read_relative_offset32()
        size = buffer.read_uint32()
        with buffer.read_from_offset(offset):
            for _ in range(size):
                self.append(cls.dependency_type.from_file(buffer))

        return self
