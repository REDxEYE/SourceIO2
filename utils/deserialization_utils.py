import abc
import struct
from dataclasses import dataclass
from typing import Generic, get_args, TypeVar, get_origin

from SourceIO2.utils import IBuffer, MemoryBuffer


class IFromFile(abc.ABC):
    @classmethod
    def from_file(cls, buffer: IBuffer):
        def _read_value(buffer, value_type):
            if get_origin(value_type) == StaticArray:
                array_type, array_size = get_args(value_type)
                return tuple([_read_value(buffer, array_type) for _ in range(array_size)])
            elif get_origin(value_type) == _string:
                _, array_size = get_args(value_type)
                return buffer.read_ascii_string(array_size)
            elif issubclass(value_type, IFromFile):
                field_value = value_type.from_file(buffer)
            elif issubclass(value_type, int16):
                field_value = buffer.read_int16()
            elif issubclass(value_type, uint16):
                field_value = buffer.read_uint16()
            elif issubclass(value_type, int32):
                field_value = buffer.read_int32()
            elif issubclass(value_type, uint32):
                field_value = buffer.read_uint32()
            else:
                raise Exception(f'Unsupported type: {field_type} for member {field_name!r} in {cls.__name__!r} class')
            return field_value

        init_args = {}
        for field_name, field_type in cls.__annotations__.items():
            field_value = _read_value(buffer, field_type)

            init_args[field_name] = field_value
        return cls(**init_args)


T = TypeVar('T')
V = TypeVar('V', bound=int)


class DeserializationBase:
    pass


class StaticArray(Generic[T, V], tuple[T, ...], DeserializationBase):
    pass


class CanBeStaticArray(Generic[T], DeserializationBase):
    def __class_getitem__(cls, value):
        return StaticArray[cls, value]


class int16(int, CanBeStaticArray, DeserializationBase):
    pass


class uint16(int, CanBeStaticArray, DeserializationBase):
    pass


class int32(int, CanBeStaticArray, DeserializationBase):
    pass


class uint32(int, CanBeStaticArray, DeserializationBase):
    pass


class _string(str, DeserializationBase, Generic[T, V]):
    pass


class string(str, DeserializationBase):
    def __class_getitem__(cls, value):
        return _string[cls, value]


class int8(int, CanBeStaticArray, DeserializationBase):
    pass


class uint8(int, CanBeStaticArray, DeserializationBase):
    pass


if __name__ == '__main__':
    @dataclass
    class Test(IFromFile):
        a: int16
        b: uint16
        c: int32
        d: uint32
        e: uint32[8]
        string: string[8]


    test = Test.from_file(
        MemoryBuffer(struct.pack('hHiI8I8s', -45, 45, -554, 554, 1, 2, 3, 4, 5, 6, 7, 8, b'testing1')))
    print(test)
