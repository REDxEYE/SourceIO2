import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

from SourceIO2.utils import IFromFile, IBuffer
from SourceIO2.utils.file_utils import FileBuffer, MemoryBuffer

VPK_MAGIC = 0x55AA1234


class InvalidMagic(Exception):
    pass


@dataclass(slots=True)
class LazyVPKFileEntry:
    name: str
    offset: int


@dataclass(slots=True)
class VPKFileEntry(IFromFile):
    crc32: int
    preload: bytearray
    archive_id: int
    offset: int
    size: int

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'VPKFileEntry':
        (crc32, preload_data_size, archive_id, offset, size) = buffer.read_fmt('I2H2I')

        if buffer.read_uint16() != 0xFFFF:
            raise NotImplementedError('Invalid terminator')
        if preload_data_size > 0:
            preload_data = bytearray(buffer.read(preload_data_size))
        else:
            preload_data = bytearray()
        return cls(crc32, preload_data, archive_id, offset, size)


@dataclass(slots=True)
class VPKHeader(IFromFile):
    version: Tuple[int, int]
    tree_size: int
    file_data_section_size: int
    archive_md5_section_size: int
    other_md5_section_size: int
    signature_section_size: int

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'VPKHeader':
        magic = buffer.read_uint32()
        assert magic == VPK_MAGIC
        version_mj, version_mn = buffer.read_fmt('2H')
        tree_size = buffer.read_uint32()
        if version_mj == 1:
            return cls((version_mj, version_mj), tree_size, 0, 0, 0, 0)
        elif version_mj == 2 and version_mn == 0:
            return cls((version_mj, version_mj), tree_size, *buffer.read_fmt('4I'))
        elif version_mj == 2 and version_mn == 3:
            return cls((version_mj, version_mj), tree_size, buffer.read_uint32(), 0, 0, 0)
        else:
            raise NotImplementedError(f"Bad VPK version ({version_mj}.{version_mn})")


class VPKFile:
    def __init__(self, buffer: IBuffer, filepath: Path):
        self._path = filepath
        self._buffer = buffer
        self.entries: Dict[str, LazyVPKFileEntry] = {}
        self._entry_cache: Dict[str, VPKFileEntry] = {}
        self.header = VPKHeader((0, 0), 0, 0, 0, 0, 0)
        self.data_start = 0

    @classmethod
    def from_file(cls, buffer: IBuffer, filepath: Path) -> 'VPKFile':
        self = cls(buffer, filepath)
        self.header = VPKHeader.from_file(buffer)

        while type_name := buffer.read_ascii_string():
            while directory_name := buffer.read_ascii_string():
                while file_name := buffer.read_ascii_string():
                    full_path = f'{directory_name}/{file_name}.{type_name}'.lower()
                    self.entries[full_path] = LazyVPKFileEntry(full_path, buffer.tell())
                    _, preload_size = buffer.read_fmt('IH')
                    buffer.seek(preload_size + 12, io.SEEK_CUR)
        self.data_start = buffer.tell()
        return self

    def __contains__(self, item: Path):
        return item.as_posix() in self.entries

    def _get_entry_data(self, entry: VPKFileEntry):
        if entry.archive_id == 0x7FFF:
            data = entry.preload
            with self._buffer.read_from_offset(entry.offset + self.data_start):
                data.extend(self._buffer.read(entry.size))
            reader = MemoryBuffer(entry.preload + data)
            return reader
        else:
            target_archive_path = self._path.parent / f'{self._path.stem[:-3]}{entry.archive_id:03d}.vpk'
            with open(target_archive_path, 'rb') as target_archive:
                target_archive.seek(entry.offset)
                reader = MemoryBuffer(entry.preload + target_archive.read(entry.size))
                return reader

    def get_file(self, path: Path):
        path = path.as_posix()

        if entry := self._entry_cache.get(path, None):
            return self._get_entry_data(entry)

        if lazy_entry := self.entries.get(path, None):
            self._buffer.seek(lazy_entry.offset)
            entry = VPKFileEntry.from_file(self._buffer)
            self._entry_cache[path] = entry
            return self._get_entry_data(entry)


def load_vpk(file_path: Path) -> VPKFile:
    from struct import unpack
    with open(file_path, 'rb') as f:
        magic, version_mj, version_mn = unpack('IHH', f.read(8))
    if magic != VPK_MAGIC:
        raise InvalidMagic(f'Not a VPK file, expected magic: {VPK_MAGIC}, got {magic}')
    if version_mj in [1, 2] and version_mn == 0:
        return VPKFile.from_file(FileBuffer(file_path), file_path)
    else:
        raise NotImplementedError(f"Failed to find VPK handler for VPK:{version_mj}.{version_mn}.")
