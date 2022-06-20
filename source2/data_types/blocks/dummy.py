from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer


class DummyBlock(BaseBlock):
    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        super().__init__(buffer, resource)

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource):
        return cls(buffer, resource)
