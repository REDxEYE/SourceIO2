import abc
from abc import ABC

from SourceIO2.shared.content_manager.detectors.base_detector import IDetector
from SourceIO2.shared.content_manager.detectors.gameinfo_detector import GameInfoDetector


class Source2Detector(IDetector, GameInfoDetector, ABC):
    pass
