from pathlib import Path

from SourceIO2.utils.file_utils import FileBuffer, IBuffer
from SourceIO2.source2.resource_types.compiled_generic_resource import CompiledGenericResource
from SourceIO2.source2.resource_types.compiled_material_resource import CompiledMaterialResource
from SourceIO2.source2.resource_types.compiled_texture_resource import CompiledTextureResource


def load_compiled_resource_from_path(path: Path):
    return load_compiled_resource(FileBuffer(path), path)


def load_compiled_resource(buffer: IBuffer, path: Path):
    if not buffer:
        return None
    file_type = path.suffix
    if file_type == '.vtex_c':
        return CompiledTextureResource.from_file(buffer, path)
    if file_type == '.vmat_c':
        return CompiledMaterialResource.from_file(buffer, path)
    return CompiledGenericResource.from_file(buffer, path)
