from pathlib import Path
from typing import Dict, Type

from SourceIO2.shared.content_manager.providers.provider_base import IProvider
from SourceIO2.shared.content_manager.detectors.s2_detector import Source2Detector
from SourceIO2.shared.content_manager.providers.fs_provider import FileSystemProvider
from SourceIO2.utils.path_utils import backwalk_resolve


class HLADetector(Source2Detector):
    @classmethod
    def register_common(cls, root_path: Path, content_providers: Dict[str, IProvider]):
        pass

    @classmethod
    def detect(cls: Type['HLADetector'], path: Path):
        hla_root = None
        hlvr_folder = backwalk_resolve(path, Path('hlvr'))
        if hlvr_folder is not None:
            hla_root = hlvr_folder.parent
        if hla_root is None:
            return Path(), {}
        if not (hla_root / 'hlvr_addons').exists():
            return Path(), {}
        content_providers = {}
        gameinfo = hlvr_folder / 'gameinfo.gi'
        for path_type, path in cls.scan_gameinfo(gameinfo, hla_root):
            if path_type in ('game', 'mod', 'write'):
                if path.stem in content_providers:
                    continue
                content_providers[path.stem] = FileSystemProvider(path)
            elif path_type == 'addonroot':
                for addon in path.iterdir():
                    if addon.stem.startswith('.') or f'addon_{addon.stem}' in content_providers:
                        continue
                    content_providers[f'addon_{addon.stem}'] = FileSystemProvider(addon)

        return hla_root, content_providers
