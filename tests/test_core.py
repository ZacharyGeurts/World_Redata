#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from redata.core import HEADER_SIZE, is_redata, redata_inplace, redata_pack, redata_restore_to, redata_unpack


def test_roundtrip_zlib():
    raw = b"Field Technology " * 500 + b"operator grep dispatch\n"
    packed = redata_pack(raw)
    assert packed is not None
    assert is_redata(packed)
    assert len(packed) < len(raw)
    assert redata_unpack(packed) == raw


def test_skip_tiny_no_gain():
    raw = b"x" * 40
    assert redata_pack(raw) is None


def test_inplace_tail_clear():
    raw = ("Redata lossless segment " * 200).encode()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "sample.txt"
        path.write_bytes(raw)
        rep = redata_inplace(path)
        assert rep["ok"]
        assert rep["lossless"]
        assert path.stat().st_size < len(raw)
        assert path.stat().st_size == rep["stored_bytes"]
        assert redata_unpack(path.read_bytes()) == raw


def test_restore_sidecar():
    raw = b"{" + b'"body": "chapter text",\n' * 100 + b"}"
    packed = redata_pack(raw)
    assert packed
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "a.wrdt"
        dest = Path(td) / "a.json"
        src.write_bytes(packed)
        redata_restore_to(src, dest)
        assert dest.read_bytes() == raw


if __name__ == "__main__":
    test_roundtrip_zlib()
    test_skip_tiny_no_gain()
    test_inplace_tail_clear()
    test_restore_sidecar()
    print("ok")