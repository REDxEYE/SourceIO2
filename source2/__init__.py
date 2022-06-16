from pathlib import Path

from SourceIO2.utils.file_utils import FileBuffer
from SourceIO2.source2.resource_types.generic import GenericCompiledFile


def load_compiled_file(path: Path):
    return GenericCompiledFile(FileBuffer(path))
