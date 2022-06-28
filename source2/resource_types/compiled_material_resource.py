from SourceIO2.source2 import CompiledGenericResource


class CompiledMaterialResource(CompiledGenericResource):
    def get_used_textures(self):
        data_block, = self.get_data_block(block_name='DATA')
        used_textures = {}
        for texture in data_block['m_textureParams']:
            used_textures[texture['m_name']] = texture['m_pValue']

        return used_textures
