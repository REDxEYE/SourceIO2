import abc
import typing
from SourceIO2.utils import IBuffer

if typing.TYPE_CHECKING:
    from SourceIO2.source2.resource_types.resource import ICompiledResource


class IBlock:
    buffer: IBuffer
    resource: 'ICompiledResource'

    @classmethod
    @abc.abstractmethod
    def from_file(cls, buffer: IBuffer, resource):
        raise NotImplementedError()
