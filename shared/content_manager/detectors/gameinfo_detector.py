import abc
from pathlib import Path
from typing import Tuple, List

from SourceIO2.utils import FileBuffer
from SourceIO2.utils.kv_parser import parse_kv
from SourceIO2.utils.kv_mappers.gameinfo import GameInfoMapper


class GameInfoDetector:
    @classmethod
    def scan_gameinfo(cls, gameinfo_path: Path, game_root: Path) -> List[Tuple[str, Path]]:
        if not gameinfo_path.exists():
            return []
        data = parse_kv(FileBuffer(gameinfo_path), str(gameinfo_path))
        mapper = GameInfoMapper(data.to_dict(), gameinfo_path.parent)
        paths = []
        for path_type, path in mapper.all_paths:
            if (game_root / path).exists():
                paths.append((path_type, game_root / path))
        return paths
