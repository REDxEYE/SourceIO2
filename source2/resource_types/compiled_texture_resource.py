import io
import logging
from typing import Type, Optional

import numpy as np

from SourceIO2.source2 import CompiledGenericResource
from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.data_types.blocks.texture_data import TextureData, VTexExtraData, CompressedMip, VTexFormat
from SourceIO2.utils.pylib_loader import pylib

lz4_decompress = pylib.lz4.decompress
lz4_compress = pylib.lz4.compress
tdc = pylib.texture

logger = logging.getLogger('CompiledTextureResource')


class CompiledTextureResource(CompiledGenericResource):
    def _get_block_class(self, name) -> Type[BaseBlock]:
        if name == 'DATA':
            return TextureData
        return super()._get_block_class(name)

    @staticmethod
    def _calculate_buffer_size_for_mip(data_block: TextureData, mip_level):
        texture_info = data_block.texture_info
        bytes_per_pixel = VTexFormat.block_size(texture_info.pixel_format)
        width = texture_info.width >> mip_level
        height = texture_info.height >> mip_level
        depth = texture_info.depth >> mip_level
        if depth < 1:
            depth = 1
        if texture_info.pixel_format in [
            VTexFormat.DXT1,
            VTexFormat.DXT5,
            VTexFormat.BC6H,
            VTexFormat.BC7,
            VTexFormat.ETC2,
            VTexFormat.ETC2_EAC,
            VTexFormat.ATI1N,
            VTexFormat.ATI2N,
        ]:

            misalign = width % 4

            if misalign > 0:
                width += 4 - misalign

            misalign = height % 4

            if misalign > 0:
                height += 4 - misalign

            if 4 > width > 0:
                width = 4

            if 4 > height > 0:
                height = 4

            if 4 > depth > 1:
                depth = 4

            num_blocks = (width * height) >> 4
            num_blocks *= depth

            return num_blocks * bytes_per_pixel

        return width * height * depth * bytes_per_pixel

    def get_texture_data(self, mip_level=0, flip=True):
        logger.info(f'Loading texture {self._filename.as_posix()!r}')
        info_block = None
        for block in self._info_blocks:
            if block.name == 'DATA':
                info_block = block
                break
        data_block: TextureData
        data_block, = self.get_data_block(block_name='DATA')
        buffer = self._buffer
        buffer.seek(info_block.offset + info_block.size)
        compression_info: Optional[CompressedMip] = data_block.extra_data.get(VTexExtraData.COMPRESSED_MIP_SIZE, None)

        uncompressed_size = self._calculate_buffer_size_for_mip(data_block, mip_level)
        if compression_info and compression_info.compressed:
            compressed_size = compression_info.mip_sizes[mip_level]
            for size in reversed(compression_info.mip_sizes[mip_level + 1:]):
                buffer.seek(size, io.SEEK_CUR)
        else:
            compressed_size = self._calculate_buffer_size_for_mip(data_block, mip_level)
            for i in range(data_block.texture_info.mip_count - 1, mip_level, -1):
                buffer.seek(self._calculate_buffer_size_for_mip(data_block, i), io.SEEK_CUR)

        if compressed_size >= uncompressed_size:
            data = buffer.read(uncompressed_size)
        else:
            data = lz4_decompress(buffer.read(compressed_size), compressed_size, uncompressed_size)
            assert len(data) == uncompressed_size, "Uncompressed data size != expected uncompressed size"
        pixel_format = data_block.texture_info.pixel_format
        width = data_block.texture_info.width
        height = data_block.texture_info.height
        if pixel_format == VTexFormat.RGBA8888:
            data = np.frombuffer(data, np.uint8).reshape((width, height, 4))
            if flip:
                data = np.flipud(data)
        elif pixel_format == VTexFormat.BC7:
            data = tdc.bc7_decompress(data, width, height, flip)
        elif pixel_format == VTexFormat.ATI1N:
            data = tdc.ati1_decompress(data, width, height, flip)
        elif pixel_format == VTexFormat.ATI2N:
            data = tdc.ati2_decompress(data, width, height, flip)
        elif pixel_format == VTexFormat.DXT1:
            data = tdc.dxt1_decompress(data, width, height, flip)
        elif pixel_format == VTexFormat.DXT5:
            data = tdc.dxt5_decompress(data, width, height, flip)
        elif pixel_format == VTexFormat.RGBA16161616F:
            data = np.frombuffer(data, np.float16, width * height * 4)
        return data, (width, height)
