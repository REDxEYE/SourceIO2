from typing import Type

from SourceIO2.utils import IBuffer
from SourceIO2.source2.data_types.info_block import InfoBlock
from SourceIO2.source2.data_types.blocks import BaseBlock, ResourceEditInfo, KV3Block, ResourceExternalReferenceList
from SourceIO2.source2.data_types.header import ResourceHeader
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.source2.data_types.blocks.dummy import DummyBlock
from SourceIO2.source2.data_types.blocks.vertex_index_buffer import VertexIndexBuffer


class GenericCompiledResource(ICompiledResource):

    @classmethod
    def from_file(cls, buffer: IBuffer):
        self = cls(buffer)
        self._header = ResourceHeader.from_file(buffer)
        buffer.seek(self._header.block_info_offset)
        self._info_blocks = [InfoBlock.from_file(buffer) for _ in range(self._header.block_count)]
        return self

    def _get_block_class(self, name) -> Type[BaseBlock]:
        if name == "NTRO":
            return ResourceIntrospectionManifest
        elif name == "REDI":
            return ResourceEditInfo
        elif name == "RED2":
            return ResourceEditInfo2
        elif name == "RERL":
            return ResourceExternalReferenceList
        elif name == 'ASEQ':
            return KV3Block
        elif name == 'MDAT':
            return KV3Block
        elif name == 'PHYS':
            return KV3Block
        elif name == 'AGRP':
            return KV3Block
        elif name == 'DATA':
            return KV3Block
        elif name == 'CTRL':
            return KV3Block
        elif name == 'MRPH':
            return KV3Block
        elif name == 'MBUF':
            return VertexIndexBuffer
        else:
            return DummyBlock
