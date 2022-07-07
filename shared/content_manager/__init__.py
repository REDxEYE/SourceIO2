import logging
from pathlib import Path
from typing import Dict, Iterator, Tuple, Type

from SourceIO2.shared.content_manager.providers.base_provider import IProvider
from SourceIO2.utils import IBuffer
from .detectors import hla, test_data
from .providers.fs_provider import FileSystemProvider
from .providers.vpk_provider import VPKProvider
from ...utils.singleton import Singleton

logger = logging.getLogger('ContentManager')
detectors = [hla.HLADetector, test_data.TestDataDetector]


class ContentManager(IProvider):

    def __init__(self):
        self.game_root = Path()
        self.providers: Dict[str, IProvider] = {}

    @classmethod
    def from_game_asset(cls: Type['ContentManager'], asset_path: Path):
        for detector in detectors:
            root, providers = detector.detect(asset_path)
            if root:
                self = cls()
                self.game_root = root
                [self.add_provider(name, provider) for name, provider in providers.items()]
                return self

    def mount(self, path: Path):
        if path.is_file() and path.suffix == '.vpk':
            self.add_provider(path.stem, VPKProvider(path))
        elif path.is_dir() and path.exists():
            self.add_provider(path.stem, FileSystemProvider(path))

    def add_provider(self, name: str, provider: IProvider):
        logger.info(f'Added provider: {provider.__class__.__name__}({name!r})')
        self.providers[name] = provider

    def get_provider_for(self, mod_name):
        """Returns either provider for asked mod or itself as fallback"""
        return self.providers.get(mod_name, self)

    def find_file(self, file_name: Path) -> Path:
        for name, provider in self.providers.items():
            if file := provider.find_file(file_name):
                logger.debug(f'Found {file_name.as_posix()!r} in {name!r}')
                return file

    def get_file(self, file_name: Path) -> IBuffer:
        for name, provider in self.providers.items():
            if file := provider.get_file(file_name):
                logger.debug(f'Found {file_name.as_posix()!r} in {name!r}')
                return file

    def grep(self, fname: str) -> Iterator[Tuple[Path, IBuffer]]:
        for name, provider in self.providers.items():
            yield from provider.grep(fname)


class GlobalContentManager(ContentManager, metaclass=Singleton):

    def from_content_manager(self, cm: ContentManager):
        self.providers = cm.providers
        self.game_root = cm.game_root
        return self
