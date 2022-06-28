import abc
from pathlib import Path
from typing import Dict, List, Type, Optional, Union

from SourceIO2.utils import IBuffer, MemoryBuffer
from SourceIO2.source2.data_types.abstract_block import IBlock
from SourceIO2.source2.data_types.header import ResourceHeader
from SourceIO2.source2.resource_types.compiled_generic_resource import InfoBlock


class ICompiledResource:
    def __init__(self, file: IBuffer, filename: Path):
        self._buffer = file
        self._header: ResourceHeader = ResourceHeader(0, 0, 0, 0, 0)
        self._filename = filename

        self._info_blocks: List[InfoBlock] = []
        self._blocks: Dict[int, IBlock] = {}

    @classmethod
    @abc.abstractmethod
    def from_file(cls, buffer: IBuffer, filename: Path):
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_block_class(self, name) -> Type[IBlock]:
        raise NotImplementedError()

    def get_data_block(self, *,
                       block_id: Optional[int] = None,
                       block_name: Optional[str] = None) -> Optional[Union[IBlock, List[IBlock]]]:
        if block_id is not None:
            if block_id == -1:
                return None
            data_block = self._blocks.get(block_id, None)
            if data_block is None:
                info_block = self._info_blocks[block_id]
                data_block_class = self._get_block_class(info_block.name)
                if data_block_class is None:
                    return None
                self._buffer.seek(info_block.offset)
                data_block = data_block_class.from_file(MemoryBuffer(self._buffer.read(info_block.size)), self)
                data_block.custom_name = info_block.name
            self._blocks[block_id] = data_block
            return data_block
        elif block_name is not None:
            blocks = []
            for i, block in enumerate(self._info_blocks):
                if block.name == block_name:
                    data_block = self.get_data_block(block_id=i)
                    if data_block is not None:
                        blocks.append(data_block)
            return blocks

    def __del__(self):
        self._buffer.close()
