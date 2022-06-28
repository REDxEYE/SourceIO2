from SourceIO2.source2.data_types.blocks import DataBlock, ResourceIntrospectionManifest
from SourceIO2.source2.data_types.keyvalues3.binary_keyvalues import BinaryKeyValues
from SourceIO2.source2.data_types.keyvalues3.enums import KV3Signatures
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer


class AgrpBlock(DataBlock):
    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource) -> 'DataBlock':
        self: 'DataBlock' = cls(buffer, resource)
        magic = buffer.read(4)
        buffer.seek(-4, 1)
        if KV3Signatures.is_valid(magic):
            kv3 = BinaryKeyValues.from_file(buffer)
            self.update(kv3.root)
        elif self.has_ntro:
            ntro: ResourceIntrospectionManifest
            ntro, = resource.get_data_block(block_name='NTRO')
            top_struct = ntro.struct_by_name('AnimationGroupResourceData_t')
            self.update(ntro.read_struct(buffer, top_struct))
        else:
            raise NotImplementedError('Unknown data block format')
        return self