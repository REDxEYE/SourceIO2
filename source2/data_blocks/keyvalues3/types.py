from functools import partial
from types import NoneType
from typing import List, TypeVar, Optional, Collection

import numpy as np

from SourceIO2.source2.data_blocks.keyvalues3.enums import KV3TypeFlag, KV3Type


class BaseType:
    def __init_subclass__(cls, **kwargs):
        cls.flag = KV3TypeFlag.NONE


class NullObject(BaseType):
    pass


class String(BaseType, str):
    pass


class _BaseInt(BaseType, int):
    pass


class _BaseFloat(BaseType, float):
    pass


class Bool(_BaseInt):
    pass


class Int32(_BaseInt):
    pass


class UInt32(_BaseInt):
    pass


class Int64(_BaseInt):
    pass


class UInt64(_BaseInt):
    pass


class Double(_BaseFloat):
    pass


class BinaryBlob(BaseType, bytes):
    pass


T = TypeVar('T', BaseType, str)


class Object(BaseType, dict):

    def __setitem__(self, key, value: T):
        if not isinstance(value, (BaseType, str, NoneType, np.ndarray)):
            raise TypeError(f'Only KV3 types are allowed, got {type(value)}')
        if isinstance(value, np.ndarray):
            assert value.dtype in (np.float64, np.uint32, np.int32, np.uint64, np.int64)
        super(Object, self).__setitem__(key, value)


class Array(BaseType, List):
    def __init__(self, initial: Optional[List[T]] = None):
        super(Array, self).__init__(initial)

    def append(self, value: T):
        assert isinstance(value, BaseType)
        super(Array, self).append(value)

    def extend(self, values: Collection[T]):
        assert all(map(partial(isinstance, __class_or_tuple=BaseType), values))
        super(Array, self).extend(values)


class TypedArray(BaseType, List):
    def __init__(self, data_type: KV3Type, data_flag: KV3TypeFlag, initial: Optional[List[T]] = None):
        super(TypedArray, self).__init__(initial)
        self.data_type = data_type
        self.data_flag = data_flag

    def append(self, value: T):
        assert isinstance(value, BaseType)
        super(TypedArray, self).append(value)

    def extend(self, values: Collection[T]):
        assert all(map(partial(isinstance, __class_or_tuple=BaseType), values))
        super(TypedArray, self).extend(values)


__all__ = ['BaseType', 'Object', 'NullObject', 'String', 'Bool',
           'Int64', 'UInt32', 'UInt64', 'Int32', 'Double',
           'BinaryBlob', 'Array', 'TypedArray']
