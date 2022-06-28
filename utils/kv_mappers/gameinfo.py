import logging
from pathlib import Path
from typing import Union, IO, List, Mapping, Dict, Tuple
from io import TextIOBase, BufferedIOBase, BytesIO, StringIO


class GameInfoMapper:
    class HiddenMaps:
        def __init__(self, raw_data):
            self._raw_data = raw_data

        @property
        def test_speakers(self):
            return bool(int(self._raw_data.get('test_speakers', '0')))

        @property
        def test_hardware(self):
            return bool(int(self._raw_data.get('test_hardware', '0')))

    class FileSystem:
        class SearchPaths:
            def __init__(self, raw_data):
                self._raw_data = raw_data

            @property
            def game(self):
                value = self._raw_data.get('game', [])
                if isinstance(value, str):
                    return [value]
                return value

            @property
            def all_paths(self) -> List[Tuple[str, str]]:
                paths = []
                for name, value in self._raw_data.items():
                    if isinstance(value, str):
                        value = [value]
                    for path in value:
                        if '|all_source_engine_paths|' in path:
                            path = path.replace('|all_source_engine_paths|', "")
                        paths.append((name, path))
                return list(set(paths))

        def __init__(self, raw_data):
            self._raw_data = raw_data

        @property
        def steam_app_id(self):
            return int(self._raw_data.get('steamappid', '0'))

        @property
        def tools_app_id(self):
            return int(self._raw_data.get('toolsappid', '0'))

        @property
        def search_paths(self):
            return self.SearchPaths(self._raw_data.get('searchpaths', {}))

    def __init__(self, data: Dict, root: Path):
        self.root = root
        self.header, self._raw_data = data.popitem()

    @property
    def all_paths(self) -> List[Tuple[str, Path]]:
        paths = []
        for path_type, path in self.file_system.search_paths.all_paths:
            try:
                if '|gameinfo_path|' in path:
                    path = f"{self.root.as_posix()}/{path.replace('|gameinfo_path|', '')}"
                    if path.endswith('*'):
                        path = path[:-1]
                        for sub_path in (self.root / path).iterdir():
                            paths.append(sub_path)
                    else:
                        paths.append((path_type, Path(path)))
                elif path.endswith('*'):
                    path = path[:-1]
                    if (self.root.parent / path).exists():
                        for sub_path in (self.root.parent / path).iterdir():
                            paths.append((path_type, sub_path))
                else:
                    paths.append((path_type, Path(path)))
            except Exception as e:
                logging.exception(f'Failed to get paths from gameinfo({self.root})')
        return paths

    @property
    def game(self):
        return self._raw_data.get('game')

    @property
    def title(self):
        return self._raw_data.get('title')

    @property
    def title2(self):
        return self._raw_data.get('title2')

    @property
    def type(self):
        return self._raw_data.get('type')

    @property
    def nomodels(self):
        return bool(int(self._raw_data.get('nomodels')))

    @property
    def nohimodel(self):
        return bool(int(self._raw_data.get('nohimodel')))

    @property
    def nocrosshair(self):
        return bool(int(self._raw_data.get('nocrosshair')))

    @property
    def hidden_maps(self):
        return self.HiddenMaps(self._raw_data.get('hidden_maps', {}))

    @property
    def nodegraph(self):
        return bool(int(self._raw_data.get('nodegraph')))

    @property
    def file_system(self):
        return self.FileSystem(self._raw_data.get('filesystem', {}))
