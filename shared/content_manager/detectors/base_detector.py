import abc
from pathlib import Path
from typing import Dict, Tuple, Optional

from SourceIO2.shared.content_manager import IProvider


class IDetector(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def detect(cls, path: Path) -> Tuple[Optional[Path], Dict[str, IProvider]]:
        pass

    @classmethod
    @abc.abstractmethod
    def register_common(cls, root_path: Path, content_providers: Dict[str, IProvider]):
        pass
