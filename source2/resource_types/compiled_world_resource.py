from SourceIO2.shared.content_manager import ContentManager
from SourceIO2.source2.resource_types.compiled_generic_resource import CompiledGenericResource
from SourceIO2.source2 import load_compiled_resource


class CompiledWorldResource(CompiledGenericResource):
    def get_worldnodes(self, cm: ContentManager):
        data, = self.get_data_block(block_name='DATA')
        for world_node_group in data['m_worldNodes']:
            node_group_prefix = world_node_group['m_worldNodePrefix']
            for path, buffer in cm.grep(node_group_prefix + '*.vmdl_c'):
                yield load_compiled_resource(buffer, path)
