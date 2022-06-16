from pathlib import Path

from SourceIO2.utils.file_utils import FileBuffer
from SourceIO2.source2.resource_types.generic import GenericCompiledResource


def load_compiled_resouce(path: Path):
    return GenericCompiledResource.from_file(FileBuffer(path))
