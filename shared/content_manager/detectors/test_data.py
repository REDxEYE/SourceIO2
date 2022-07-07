from pathlib import Path
from typing import Dict, Type

from SourceIO2.shared.content_manager.providers.base_provider import IProvider
from SourceIO2.shared.content_manager.detectors.s2_detector import Source2Detector
from SourceIO2.shared.content_manager.providers.fs_provider import FileSystemProvider
from SourceIO2.utils.path_utils import backwalk_resolve


class TestDataDetector(Source2Detector):
    @classmethod
    def register_common(cls, root_path: Path, content_providers: Dict[str, IProvider]):
        pass

    @classmethod
    def detect(cls: Type['TestDataDetector'], path: Path):
        root = None
        test_marker = backwalk_resolve(path, Path('TEST.TEST'))
        if test_marker is not None:
            root = test_marker.parent
        if root is None:
            return Path(), {}
        content_providers = {}
        gameinfo = backwalk_resolve(path, Path('gameinfo.gi'))
        for path_type, path in cls.scan_gameinfo(gameinfo, root):
            if path_type in ('game', 'mod', 'write'):
                if path.stem in content_providers:
                    continue
                content_providers[path.stem] = FileSystemProvider(path)
            elif path_type == 'addonroot':
                for addon in path.iterdir():
                    if addon.stem.startswith('.') or f'addon_{addon.stem}' in content_providers:
                        continue
                    content_providers[f'addon_{addon.stem}'] = FileSystemProvider(addon)

        return root, content_providers
