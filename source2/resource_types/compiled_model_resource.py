from typing import Collection, List

from SourceIO2.shared.intermidiate_data.bone import Bone
from SourceIO2.source2.exceptions import MissingBlock
from SourceIO2.source2.resource_types import CompiledGenericResource


class CompiledModelResource(CompiledGenericResource):

    def get_bones(self) -> Collection[Bone]:
        data, = self.get_data_block(block_name='DATA')
        if data is None:
            raise MissingBlock('Required block "DATA" is missing')
        bones: List[Bone] = []

        model_skeleton = data['m_modelSkeleton']
        names = model_skeleton['m_boneName']
        parents = model_skeleton['m_nParent']
        positions = model_skeleton['m_bonePosParent']
        rotations = model_skeleton['m_boneRotParent']

        for bone_id, name in enumerate(names):
            parent_id = parents[bone_id]
            if parent_id >= 0:
                parent_name = names[parent_id]
            else:
                parent_name = None
            bones.append(Bone(name, parent_name, positions[bone_id], rotations[bone_id]))

        return bones
