"""WRDT1 — World Redata lossless in-place format.

Not compression-as-storage: canonical bytes live in the envelope with SHA-256 proof.
In-place pack writes header+payload at offset 0 and ftruncates the file tail so stale
bytes never bleed into adjacent inode space or confuse readers.

Copyright (c) Zachary Geurts. All rights reserved. See LICENSE.
"""
from __future__ import annotations

import hashlib
import mmap
import os
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"WRDT"
VERSION = 1
HEADER_SIZE = 52  # 4 magic + 16 fixed fields + 32 sha256
PAYLOAD_OFFSET = 52

METHOD_STORE = 0
METHOD_ZLIB1 = 1

FLAG_INPLACE = 1 << 0


@dataclass(frozen=True)
class RedataEnvelope:
    method: int
    original_size: int
    payload: bytes
    digest: bytes

    @property
    def packed_size(self) -> int:
        return HEADER_SIZE + len(self.payload)


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def is_redata(data: bytes) -> bool:
    return len(data) >= HEADER_SIZE and data[:4] == MAGIC


def _parse_header(blob: bytes) -> RedataEnvelope:
    if not is_redata(blob):
        raise ValueError("not WRDT1")
    ver, method, flags, orig, pay_len = struct.unpack_from("<BBHQI", blob, 4)
    if ver != VERSION:
        raise ValueError(f"unsupported WRDT version {ver}")
    digest = blob[20:PAYLOAD_OFFSET]
    payload = blob[PAYLOAD_OFFSET : PAYLOAD_OFFSET + pay_len]
    if len(payload) != pay_len:
        raise ValueError("truncated WRDT payload")
    return RedataEnvelope(method=method, original_size=orig, payload=payload, digest=digest)


def _wrap(method: int, raw: bytes, payload: bytes) -> bytes:
    return (
        MAGIC
        + struct.pack("<BBHQI", VERSION, method, 0, len(raw), len(payload))
        + sha256(raw)
        + payload
    )


def redata_pack(raw: bytes, *, min_gain: float = 1.0) -> bytes | None:
    """Build WRDT1 blob. Returns None if envelope would not shrink raw."""
    if is_redata(raw):
        return raw
    if not raw:
        return None

    candidates: list[tuple[int, bytes]] = [(METHOD_STORE, raw)]
    if len(raw) >= 16:
        z = zlib.compress(raw, level=1)
        if len(z) < len(raw):
            candidates.append((METHOD_ZLIB1, z))

    method, payload = min(candidates, key=lambda x: len(x[1]))
    wrapped = _wrap(method, raw, payload)
    if len(wrapped) >= len(raw) * min_gain:
        return None
    return wrapped


def redata_unpack(blob: bytes) -> bytes:
    if not is_redata(blob):
        return blob
    env = _parse_header(blob)
    if env.method == METHOD_STORE:
        body = env.payload
    elif env.method == METHOD_ZLIB1:
        body = zlib.decompress(env.payload)
    else:
        raise ValueError(f"unknown WRDT method {env.method}")
    if len(body) != env.original_size:
        raise ValueError("WRDT size mismatch")
    if sha256(body) != env.digest:
        raise ValueError("WRDT sha256 mismatch — data not lossless")
    return body


def can_inplace(path: Path, packed_len: int) -> tuple[bool, str]:
    try:
        orig = path.stat().st_size
    except OSError as exc:
        return False, str(exc)
    if packed_len >= orig:
        return False, f"packed {packed_len} B >= original {orig} B — tail clear unsafe"
    return True, "ok"


def redata_inplace(path: Path, *, min_gain: float = 1.0, dry_run: bool = False) -> dict:
    """mmap pack + single write + ftruncate tail. Destructive to stale tail only."""
    path = path.resolve()
    t0 = time.perf_counter()

    with path.open("r+b") as fh:
        fd = fh.fileno()
        orig_size = os.fstat(fd).st_size
        if orig_size == 0:
            return {"ok": False, "path": str(path), "reason": "empty file"}

        with mmap.mmap(fd, 0, access=mmap.ACCESS_READ) as mm:
            raw = bytes(mm)

        if is_redata(raw):
            return {
                "ok": True,
                "path": str(path),
                "skipped": True,
                "reason": "already WRDT1",
                "stored_bytes": orig_size,
            }

        packed = redata_pack(raw, min_gain=min_gain)
        if packed is None:
            return {
                "ok": True,
                "path": str(path),
                "skipped": True,
                "reason": "no shrink — envelope larger than file",
                "raw_bytes": orig_size,
            }

        ok, why = can_inplace(path, len(packed))
        if not ok:
            return {"ok": False, "path": str(path), "reason": why}

        if dry_run:
            return {
                "ok": True,
                "path": str(path),
                "dry_run": True,
                "raw_bytes": orig_size,
                "stored_bytes": len(packed),
                "tail_cleared_bytes": orig_size - len(packed),
                "ratio": round(orig_size / len(packed), 3),
            }

        with mmap.mmap(fd, max(len(packed), orig_size), access=mmap.ACCESS_WRITE) as mm:
            mm[: len(packed)] = packed
            mm.flush()
        os.ftruncate(fd, len(packed))
        os.fsync(fd)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    restored = redata_unpack(packed)
    return {
        "ok": True,
        "path": str(path),
        "lossless": restored == raw,
        "raw_bytes": orig_size,
        "stored_bytes": len(packed),
        "tail_cleared_bytes": orig_size - len(packed),
        "ratio": round(orig_size / len(packed), 3),
        "elapsed_ms": elapsed_ms,
    }


def redata_restore_inplace(path: Path, *, dry_run: bool = False) -> dict:
    """Expand WRDT1 file back to original bytes in-place (requires spare inode size)."""
    path = path.resolve()
    with path.open("r+b") as fh:
        fd = fh.fileno()
        stored = os.fstat(fd).st_size
        raw_blob = fh.read()
        if not is_redata(raw_blob):
            return {"ok": False, "path": str(path), "reason": "not WRDT1"}
        env = _parse_header(raw_blob)
        if env.original_size <= stored and not dry_run:
            return {
                "ok": False,
                "path": str(path),
                "reason": "inode has no spare bytes — restore to sibling path instead",
            }
        body = redata_unpack(raw_blob)
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "path": str(path),
                "stored_bytes": stored,
                "restored_bytes": len(body),
            }
        fh.seek(0)
        fh.write(body)
        fh.truncate(len(body))
        os.fsync(fd)
    return {
        "ok": True,
        "path": str(path),
        "stored_bytes": stored,
        "restored_bytes": len(body),
        "lossless": True,
    }


def redata_restore_to(src: Path, dest: Path) -> dict:
    raw = redata_unpack(src.read_bytes())
    dest.write_bytes(raw)
    return {
        "ok": True,
        "src": str(src),
        "dest": str(dest),
        "bytes": len(raw),
        "sha256": sha256(raw).hex(),
    }


def bench(raw: bytes) -> dict:
    t0 = time.perf_counter()
    packed = redata_pack(raw)
    pack_ms = int((time.perf_counter() - t0) * 1000)
    if packed is None:
        return {"raw_bytes": len(raw), "skipped": True, "reason": "no shrink"}
    t1 = time.perf_counter()
    restored = redata_unpack(packed)
    unpack_ms = int((time.perf_counter() - t1) * 1000)
    return {
        "raw_bytes": len(raw),
        "stored_bytes": len(packed),
        "lossless": restored == raw,
        "pack_ms": pack_ms,
        "unpack_ms": unpack_ms,
        "ratio": round(len(raw) / len(packed), 3),
    }