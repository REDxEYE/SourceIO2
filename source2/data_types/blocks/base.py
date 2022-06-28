import abc
from typing import Optional

from SourceIO2.source2.data_types.abstract_block import IBlock
from SourceIO2.utils import IBuffer

from SourceIO2.source2.resource_types.resource import ICompiledResource


class BaseBlock(IBlock):
    custom_name: Optional[str] = None

    def __init__(self, buffer: IBuffer, resource: 'ICompiledResource'):
        self._buffer = buffer
        self._resource = resource
        pass

    @classmethod
    @abc.abstractmethod
    def from_file(cls, buffer: IBuffer, resource: 'ICompiledResource') -> 'BaseBlock':
        raise NotImplementedError()
