from functools import cache
from typing import List, Dict

from SourceIO2.source2 import CompiledGenericResource


class CompiledMaterialResource(CompiledGenericResource):
    def get_used_textures(self):
        data_block, = self.get_data_block(block_name='DATA')
        used_textures = {}
        for texture in data_block['m_textureParams']:
            used_textures[texture['m_name']] = texture['m_pValue']
        return used_textures

    @cache
    def get_int_property(self, prop_name):
        data, = self.get_data_block(block_name='DATA')
        return self._get_prop(prop_name, data['m_intParams'], 'm_nValue')

    @cache
    def get_float_property(self, prop_name):
        data, = self.get_data_block(block_name='DATA')
        return self._get_prop(prop_name, data['m_intParams'], 'm_flValue')

    @cache
    def get_vector_property(self, prop_name):
        data, = self.get_data_block(block_name='DATA')
        return self._get_prop(prop_name, data['m_vectorParams'], 'm_value')

    @cache
    def get_texture_property(self, prop_name):
        data, = self.get_data_block(block_name='DATA')
        return self._get_prop(prop_name, data['m_textureParams'], 'm_pValue')

    @staticmethod
    def _get_prop(prop_name: str, prop_array: List[Dict], prop_value_name):
        for prop in prop_array:
            if prop['m_name'] == prop_name:
                return prop[prop_value_name]
