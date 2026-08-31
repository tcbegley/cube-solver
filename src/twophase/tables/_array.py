from __future__ import annotations

import array
from enum import StrEnum
from typing import Iterator


class dtypes(StrEnum):
    """
    Map system dependent array types to more understandable types.
    """

    u8 = "B"
    u16 = "H"
    u32 = "I" if array.array("I").itemsize >= 4 else "L"


class BitpackedArray:
    """
    A lightweight wrapper around a 32-bit array that can be used to store 16 two bit
    values in each 32-bit entry of the underlying array.
    """

    def __init__(self, dim: int) -> None:
        self._array = array.array(dtypes.u32, [0xFFFF_FFFF] * ((dim - 1) // 16 + 1))

    @classmethod
    def frombytes(cls, data: bytes) -> BitpackedArray:
        bitpacked_array = cls(0)
        bitpacked_array._array.frombytes(data)
        return bitpacked_array

    def tobytes(self) -> bytes:
        return self._array.tobytes()

    def __getitem__(self, index: int) -> int:
        """
        Helper function for retrieving values from an array where each entry is 32-bit
        unsigned integer that represents 16 2-bit integers.
        """
        # Each entry is a block of 16 two-bit values. Bit operations avoid creating
        # the tuple returned by divmod in this search-critical lookup.
        block = self._array[index >> 4]
        bit_shift = (index & 0b1111) << 1
        return (block >> bit_shift) & 0b11

    def __setitem__(self, index: int, value: int) -> None:
        """
        Helper function for setting values in an array where each entry is a 32-bit
        unsigned integer that represents 16 2-bit integers
        """
        # see get_index for explanation
        block_index, bitpair_offset = divmod(index, 16)
        bit_shift = bitpair_offset * 2
        # we first zero the bits we are writing
        self._array[block_index] &= ~(0b11 << bit_shift) & 0xFFFF_FFFF
        # then we shift the supplied value and set it in the relevant block
        self._array[block_index] |= value << bit_shift

    def __len__(self) -> int:
        return len(self._array) * 16

    def __iter__(self) -> Iterator[int]:
        return iter(self[i] for i in range(len(self)))


def max_val_to_dtype(max_val: int) -> dtypes:
    # we check against max val -1 so that we can reserve the largest value as an
    # "invalid" marker
    if max_val < 2**8 - 1:
        return dtypes.u8
    elif max_val < 2**16 - 1:
        return dtypes.u16
    return dtypes.u32


def dtype_to_max_val(dtype: dtypes) -> int:
    match dtype:
        case dtypes.u8:
            return 2**8 - 1
        case dtypes.u16:
            return 2**16 - 1
        case dtypes.u32:
            return 2**32 - 1
