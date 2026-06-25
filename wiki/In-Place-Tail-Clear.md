# In-Place Tail Clear

## Problem

Replacing file bytes in place without truncating leaves **ghost tail data** — bytes beyond the new envelope that still exist on disk. Readers that use `st_size` are safe; sloppy mmap reads or forensic recovery are not.

## World Redata rule

After writing the WRDT1 envelope at offset 0:

```c
ftruncate(fd, envelope_len);
fsync(fd);
```

The cleared region is **within the same inode** only. No other path is modified.

## Tiny-file overlap worry

If the envelope were larger than the original file, expanding in place could theoretically consume spare allocation — but we **refuse** that case:

```
pack only when envelope_len < original_st_size
```

For already-compressed or very small inputs, use sidecar output (web download / `restore -o`).

## Destructive?

Yes — to **stale tail bytes** only. Lossless bytes live in the envelope and must verify via SHA-256 on restore.