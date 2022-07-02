from typing import List

from SourceIO2.source2.data_types.blocks import DataBlock, ResourceIntrospectionManifest
from SourceIO2.source2.data_types.keyvalues3.binary_keyvalues import BinaryKeyValues
from SourceIO2.source2.data_types.keyvalues3.enums import KV3Signatures
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer


class MorphBlock(DataBlock):

    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        super().__init__(buffer, resource)

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource) -> 'MorphBlock':
        self: 'MorphBlock' = cls(buffer, resource)
        magic = buffer.read(4)
        buffer.seek(-4, 1)
        if KV3Signatures.is_valid(magic):
            kv3 = BinaryKeyValues.from_file(buffer)
            self.update(kv3.root)
        elif self.has_ntro:
            ntro: ResourceIntrospectionManifest
            ntro, = resource.get_data_block(block_name='NTRO')
            top_struct = ntro.struct_by_name('MorphSetData_t')
            self.update(ntro.read_struct(buffer, top_struct))
        else:
            raise NotImplementedError('Unknown data block format')
        return self

    @property
    def lookup_type(self):
        return self['m_nLookupType']

    @property
    def encoding_type(self):
        return self['m_nEncodingType']

    @property
    def bundles(self) -> List[str]:
        return self['m_bundleTypes']

    def get_bundle_id(self, bundle_name):
        if bundle_name in self.bundles:
            return self.bundles.index(bundle_name)