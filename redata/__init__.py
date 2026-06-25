"""World Redata — lossless in-place data envelopes."""
from redata.core import (
    HEADER_SIZE,
    MAGIC,
    bench,
    can_inplace,
    is_redata,
    redata_inplace,
    redata_pack,
    redata_restore_inplace,
    redata_restore_to,
    redata_unpack,
)

__all__ = [
    "MAGIC",
    "HEADER_SIZE",
    "is_redata",
    "redata_pack",
    "redata_unpack",
    "redata_inplace",
    "redata_restore_inplace",
    "redata_restore_to",
    "can_inplace",
    "bench",
]