import numpy as np

from SourceIO2.utils import IFromFile, IBuffer
from SourceIO2.utils.file_utils import T, MemoryBuffer
from SourceIO2.utils.pylib_loader import pylib


class IndexBuffer(IFromFile):

    @staticmethod
    def decode_index_buffer(data, size, count):
        return pylib.decode_index_buffer(data, len(data), size, count)

    def __init__(self) -> None:
        self._index_buffer = MemoryBuffer()
        self.index_count = 0
        self.index_size = 0

    @classmethod
    def from_file(cls, buffer: IBuffer) -> 'IndexBuffer':
        self = cls()
        self.index_count, self.index_size = buffer.read_fmt('2I')
        unk1, unk2 = buffer.read_fmt('2I')
        data_offset = buffer.tell() + buffer.read_uint32()
        data_size = buffer.read_uint32()

        with buffer.read_from_offset(data_offset):
            data = buffer.read(data_size)
            if data_size == self.index_size * self.index_count:
                self._index_buffer = MemoryBuffer(data)
            else:
                self._index_buffer = MemoryBuffer(self.decode_index_buffer(data, self.index_size, self.index_count))
        return self

    def get_indices(self):
        index_dtype = np.uint32 if self.index_size == 4 else np.uint16
        indices = np.frombuffer(self._index_buffer.data, index_dtype)
        return indices.reshape((-1, 3))
