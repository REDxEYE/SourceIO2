import fnmatch
import logging
from pathlib import Path
from typing import Iterator, Tuple

from SourceIO2.shared.content_manager import IProvider
from SourceIO2.shared.vpk import load_vpk
from SourceIO2.utils import IBuffer

logger = logging.getLogger('VPKProvider')


class VPKProvider(IProvider):

    def __init__(self, file_path: Path) -> None:
        self.path = file_path
        self._vpk = load_vpk(self.path)

    def find_file(self, file_name: Path) -> Path:
        logger.debug(f'Looking for {file_name.as_posix()!r} in {self.path.as_posix()!r}')
        if file_name in self._vpk:
            return Path(f'<VPK:{self.path.stem}>') / file_name

    def get_file(self, file_name: Path) -> IBuffer:
        logger.debug(f'Looking for {file_name.as_posix()!r} in {self.path.as_posix()!r}')
        if file_name in self._vpk:
            return self._vpk.get_file(file_name)

    def grep(self, fname) -> Iterator[Tuple[Path, IBuffer]]:
        for file_name, entry in self._vpk.entries.items():
            if fnmatch.fnmatch(file_name, fname):
                yield Path(file_name), self._vpk.get_file(Path(file_name))
