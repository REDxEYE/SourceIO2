from pathlib import Path
from typing import Type, Union

from SourceIO2.shared.content_manager import ContentManager
from SourceIO2.source2 import load_compiled_resource
from SourceIO2.utils import IBuffer
from SourceIO2.source2.data_types.info_block import InfoBlock
from SourceIO2.source2.data_types.blocks import BaseBlock, ResourceEditInfo, DataBlock, ResourceExternalReferenceList, \
    ResourceIntrospectionManifest, VertexIndexBuffer, DummyBlock, PhysBlock, AseqBlock, AgrpBlock, MorphBlock
from SourceIO2.source2.data_types.header import ResourceHeader
from SourceIO2.source2.resource_types.resource import ICompiledResource


class CompiledGenericResource(ICompiledResource):

    @classmethod
    def from_file(cls, buffer: IBuffer, filename: Path):
        self: 'CompiledGenericResource' = cls(buffer, filename)
        self._header = ResourceHeader.from_file(buffer)
        buffer.seek(self._header.block_info_offset)
        self._info_blocks = [InfoBlock.from_file(buffer) for _ in range(self._header.block_count)]
        self._blocks = [None] * self._header.block_count
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
            return AseqBlock
        elif name == 'MDAT':
            return DataBlock
        elif name == 'PHYS':
            return PhysBlock
        elif name == 'AGRP':
            return AgrpBlock
        elif name == 'DATA':
            return DataBlock
        elif name == 'CTRL':
            return DataBlock
        elif name == 'MRPH':
            return MorphBlock
        elif name == 'MBUF':
            return VertexIndexBuffer
        elif name == 'VBIB':
            return VertexIndexBuffer
        else:
            return DummyBlock

    def get_child_resource_path(self, name_or_id: Union[str, int]):
        external_resource_list: ResourceExternalReferenceList
        external_resource_list, = self.get_data_block(block_name='RERL')
        for child_resource in external_resource_list:
            if child_resource.hash == name_or_id or child_resource.name == name_or_id:
                return Path(child_resource.name + '_c')

    def get_child_resource(self, name_or_id: Union[str, int], cm: ContentManager):
        if resource_path := self.get_child_resource_path(name_or_id):
            return load_compiled_resource(cm.get_file(resource_path), resource_path)
