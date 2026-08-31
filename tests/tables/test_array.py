import pytest

from twophase.tables._array import (
    BitpackedArray,
    dtype_to_max_val,
    dtypes,
    max_val_to_dtype,
)

DTYPE_MAX_VAL_PAIRS = [
    (dtypes.u8, 255),
    (dtypes.u16, 65_535),
    (dtypes.u32, 4_294_967_295),
]

MAX_VAL_DTYPE_TEST_CASES = [
    (0, dtypes.u8),
    (254, dtypes.u8),
    (255, dtypes.u16),
    (1_000, dtypes.u16),
    (65_534, dtypes.u16),
    (65_535, dtypes.u32),
    (1_000_000, dtypes.u32),
]


@pytest.mark.parametrize(["dtype", "max_val"], DTYPE_MAX_VAL_PAIRS)
def test_dtype_to_max_val(dtype, max_val):
    assert dtype_to_max_val(dtype) == max_val


@pytest.mark.parametrize(["max_val", "dtype"], MAX_VAL_DTYPE_TEST_CASES)
def test_max_val_to_dtype(max_val, dtype):
    assert max_val_to_dtype(max_val) == dtype


def test_bitpacked_array():
    array = BitpackedArray(16)

    # array has required length
    assert len(array) == 16
    # underlying array is minimum length required to hold the requested number of
    # entries
    assert len(array._array) == 1

    # all bits are initially 1
    assert list(array) == [0b11] * 16

    # zero all entries but the first
    for i in range(1, 16):
        array[i] = 0b00

    assert list(array) == [0b11] + [0b00] * 15
    assert array[0] == 0b11
    assert all(array[i] == 0b00 for i in range(1, 16))
