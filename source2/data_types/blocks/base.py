import abc
from typing import TYPE_CHECKING, Type, TypeVar

from SourceIO2.utils import IBuffer

if TYPE_CHECKING:
    from SourceIO2.source2.resource_types.resource import ICompiledResource


class BaseBlock:
    def __init__(self, buffer: IBuffer, resource: 'ICompiledResource'):
        self._buffer = buffer
        self._resource = resource
        pass

    @classmethod
    @abc.abstractmethod
    def from_file(cls, buffer: IBuffer, resource: 'ICompiledResource') -> 'BaseBlock':
        raise NotImplementedError()
