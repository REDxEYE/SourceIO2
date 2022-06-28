import abc
from pathlib import Path
from typing import Iterator, Tuple

from SourceIO2.utils import IBuffer


class IProvider:

    @abc.abstractmethod
    def find_file(self, file_name: Path) -> Path:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_file(self, file_name: Path) -> IBuffer:
        raise NotImplementedError()

    @abc.abstractmethod
    def grep(self, fname) -> Iterator[Tuple[Path, IBuffer]]:
        raise NotImplementedError()
