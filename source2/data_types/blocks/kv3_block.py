from typing import Type, MutableMapping, Dict

from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.data_types.keyvalues3.types import BaseType
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer
from SourceIO2.source2.data_types.keyvalues3.enums import KV3Signatures
from SourceIO2.source2.data_types.keyvalues3.binary_keyvalues import BinaryKeyValues


class KV3Block(Dict[str, BaseType], BaseBlock):
    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        BaseBlock.__init__(self, buffer, resource)
        dict.__init__(self)

    @property
    def has_ntro(self):
        return self._resource.get_data_block(block_name="NTRO") or False

    def __str__(self) -> str:
        str_data = dict.__str__(self)
        return f"<DATA  \"{str_data if len(str_data) < 50 else str_data[:50] + '...'}\">"

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource) -> 'KV3Block':
        self = cls(buffer, resource)
        magic = buffer.read(4)
        buffer.seek(-4, 1)
        if KV3Signatures.is_valid(magic):
            kv3 = BinaryKeyValues.from_file(buffer)
            self.update(kv3.root)
        elif self.has_ntro:
            raise NotImplementedError('NTRO based data blocks are not supported')
        else:
            raise NotImplementedError('Unknown data block format')
        return self
