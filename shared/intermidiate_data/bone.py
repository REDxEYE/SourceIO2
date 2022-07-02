from dataclasses import dataclass
from typing import Optional

from .common import Vector3, Quaternion


@dataclass
class Bone:
    name: str
    parent: Optional[str]

    pos: Vector3
    rot: Quaternion
