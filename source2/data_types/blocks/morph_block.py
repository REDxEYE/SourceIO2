import logging
from collections import defaultdict
from typing import List, Dict

import numpy as np
import numpy.typing as npt

from SourceIO2.shared.content_manager import ContentManager
from SourceIO2.source2.data_types.blocks import DataBlock, ResourceIntrospectionManifest
from SourceIO2.source2.data_types.keyvalues3.binary_keyvalues import BinaryKeyValues
from SourceIO2.source2.data_types.keyvalues3.enums import KV3Signatures
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer


class MorphBlock(DataBlock):

    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        super().__init__(buffer, resource)
        self._morph_datas: Dict[int, Dict[str, npt.NDArray[np.float32]]] = defaultdict(dict)
        self._vmorf_texture = None

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

    def get_morph_data(self, cm: ContentManager, flex_name, bundle_id):
        bundle_data = self._morph_datas[bundle_id]
        if flex_name in bundle_data:
            return bundle_data[flex_name]
        assert self.lookup_type == 'LOOKUP_TYPE_VERTEX_ID'
        assert self.encoding_type == 'ENCODING_TYPE_OBJECT_SPACE'
        if not self._vmorf_texture:
            vmorf = self._resource.get_child_resource(self['m_pTextureAtlas'], cm)
            if not vmorf:
                logging.error(f'Failed to find {self["m_pTextureAtlas"]!r} morf texture')
                return None
            self._vmorf_texture = texture, (t_width, t_height) = vmorf.get_texture_data(0, False)
        else:
            texture, (t_width, t_height) = self._vmorf_texture

        width = self['m_nWidth']
        height = self['m_nHeight']

        for morph_data_ in self['m_morphDatas']:
            if morph_data_['m_name'] == flex_name:
                morph_data = morph_data_
                break
        else:
            logging.error(f'Failed to find morph data for {flex_name!r} flex')
            return None
        rect_flex_data = bundle_data[morph_data['m_name']] = np.zeros((height, width, 4), dtype=np.float32)

        for n, rect in enumerate(morph_data['m_morphRectDatas']):
            bundle = rect['m_bundleDatas'][bundle_id]

            rect_width = round(rect['m_flUWidthSrc'] * t_width)
            rect_height = round(rect['m_flVHeightSrc'] * t_height)
            dst_x = rect['m_nXLeftDst']
            dst_y = rect['m_nYTopDst']
            y_slice = slice(dst_y, dst_y + rect_height)
            x_slice = slice(dst_x, dst_x + rect_width)
            rect_u = round(bundle['m_flULeftSrc'] * t_width)
            rect_v = round(bundle['m_flVTopSrc'] * t_height)
            morph_data_rect = texture[rect_v:rect_v + rect_height, rect_u:rect_u + rect_width, :]

            transformed_data = np.divide(morph_data_rect, 255)
            transformed_data = np.multiply(transformed_data, bundle['m_ranges'])
            transformed_data = np.add(transformed_data, bundle['m_offsets'])
            rect_flex_data[y_slice, x_slice, :] = transformed_data

        return rect_flex_data
