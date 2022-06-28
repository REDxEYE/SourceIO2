import logging
from pathlib import Path
from typing import Iterator, List

from SourceIO2.shared.content_manager import IProvider
from SourceIO2.shared.content_manager.providers.vpk_provider import VPKProvider
from SourceIO2.utils import IBuffer, FileBuffer

logger = logging.getLogger('FileSystemProvider')


class FileSystemProvider(IProvider):

    def __init__(self, root_path: Path):
        self.root = root_path
        self.sub_providers: List[IProvider] = []
        for vpk in self.root.glob('*_dir.vpk'):
            logger.info(f'Found VPK in {root_path.stem!r} mod: {vpk}')
            self.sub_providers.append(VPKProvider(vpk))

    def find_file(self, file_name: Path) -> Path:
        logger.debug(f'Looking for {file_name.as_posix()!r} in {self.root.as_posix()!r}')
        if (self.root / file_name).exists():
            return self.root / file_name
        for sub in self.sub_providers:
            if file := sub.find_file(file_name):
                return file

    def get_file(self, file_name: Path) -> IBuffer:
        logger.debug(f'Looking for {file_name.as_posix()!r} in {self.root.as_posix()!r}')
        if (self.root / file_name).exists():
            return FileBuffer(self.root / file_name)
        for sub in self.sub_providers:
            if file := sub.get_file(file_name):
                return file

    def grep(self, fname) -> Iterator[Path]:
        for item in self.root.rglob(fname):
            yield item, FileBuffer(item)
        for sub in self.sub_providers:
            yield from sub.grep(fname)
