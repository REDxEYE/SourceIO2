import platform
from pathlib import Path
from typing import Optional


def pop_path_back(path: Path):
    if len(path.parts) > 1:
        return Path().joinpath(*path.parts[1:])
    else:
        return path


def pop_path_front(path: Path):
    if len(path.parts) > 1:
        return Path().joinpath(*path.parts[:-1])
    else:
        return path


def backwalk_resolve(current_path: Path, target_path: Path) -> Optional[Path]:
    current_path = current_path.absolute()
    for _ in range(len(current_path.parts) - 1):
        second_part = target_path
        for _ in range(len(target_path.parts)):
            new_path = case_sensetive_fs_fix(current_path / second_part)
            if new_path.exists():
                return new_path

            second_part = pop_path_back(second_part)
        current_path = pop_path_front(current_path)


def case_sensetive_fs_fix(path: Path):
    if platform.system() == "Windows" or path.exists():  # Shortcut for windows
        return path

    root, *parts, fname = path.parts

    new_path = Path(root)
    for part in parts:
        for dir_name in new_path.iterdir():
            if dir_name.is_file():
                continue
            if dir_name.name.lower() == part.lower():
                new_path = dir_name
                break
    for file_name in new_path.iterdir():
        if file_name.is_file() and file_name.name.lower() == fname.lower():
            return file_name
    return path
