from typing import Type

from SourceIO2.source2 import CompiledGenericResource
from SourceIO2.source2.data_types.blocks import BaseBlock, MorphBlock


class CompiledMorphResource(CompiledGenericResource):

    def _get_block_class(self, name) -> Type[BaseBlock]:
        if name == 'DATA':
            return MorphBlock
        return super()._get_block_class(name)
