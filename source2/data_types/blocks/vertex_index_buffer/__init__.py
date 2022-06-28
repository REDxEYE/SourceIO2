from typing import List

from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.data_types.blocks.vertex_index_buffer.index_buffer import IndexBuffer
from SourceIO2.source2.data_types.blocks.vertex_index_buffer.vertex_buffer import VertexBuffer
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer


class VertexIndexBuffer(BaseBlock):
    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        super().__init__(buffer, resource)
        self.vertex_buffers: List[VertexBuffer] = []
        self.index_buffers: List[IndexBuffer] = []

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource):
        vertex_buffers_offset = buffer.read_relative_offset32()
        vertex_buffers_count = buffer.read_uint32()
        index_buffers_offset = buffer.read_relative_offset32()
        index_buffers_count = buffer.read_uint32()
        self = cls(buffer, resource)
        with buffer.read_from_offset(vertex_buffers_offset):
            for _ in range(vertex_buffers_count):
                self.vertex_buffers.append(VertexBuffer.from_file(buffer))
        with buffer.read_from_offset(index_buffers_offset):
            for _ in range(index_buffers_count):
                self.index_buffers.append(IndexBuffer.from_file(buffer))
        return self

