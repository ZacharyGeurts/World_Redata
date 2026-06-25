# WRDT1 Format Specification

Version 1 · Zachary Geurts · Proprietary

## Header (52 bytes, little-endian)

```
WRDT                    # 4  magic
u8  version = 1
u8  method              # 0=store 1=zlib-1
u16 flags               # reserved
u64 original_size
u32 payload_length
byte[32] sha256(original)
```

## Payload

| Method | Payload |
|--------|---------|
| 0 STORE | Raw bytes (rare — only when already smaller than zlib+header) |
| 1 ZLIB1 | `zlib.compress(data, level=1)` |

## Verification

On unpack:

1. Decompress payload per method
2. `len(body) == original_size`
3. `sha256(body) == header digest`

Failure at any step = **not lossless** — abort.

## In-place semantics

Pack algorithm:

1. mmap read original
2. Build envelope in memory
3. If `len(envelope) >= st_size`: **skip**
4. Write envelope at offset 0
5. `ftruncate(fd, len(envelope))` — **tail clear**

Restore in-place requires `original_size <= st_size` before expand; otherwise restore to a new path.