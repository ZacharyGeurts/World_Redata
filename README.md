# THIS IS OLD AND INFO ONLY. NO FIELD NEXT TO FIELD. ALWAYS FIELD 1 and per device kinda thing. USB might be okay if you instantiate first to the storage.
# FIX THOSE ISSUES AND BE SAFE.

# World_Redata

**Lossless in-place data envelopes — not a compression codec.**

World Redata (`WRDT1`) stores canonical bytes with SHA-256 proof. Conversion is mmap-fast: write the envelope at offset 0, then **truncate the file tail** so stale data never survives inside the inode. Other files on disk are never touched.

Copyright (c) 2026 **Zachary Geurts**. All rights reserved. See [LICENSE](LICENSE).

---

## Doctrine

| Principle | Meaning |
|-----------|---------|
| **Lossless always** | Restored bytes must match SHA-256 in the header |
| **Data, not codec** | WRDT1 is sovereign storage — not “smaller is truth” |
| **Tail clear** | `ftruncate` after pack — never leave ghost bytes |
| **Skip when unsafe** | If envelope ≥ file size, refuse in-place (tiny-file rule) |

---

## Quick start

```bash
cd World_Redata
pip install -r requirements.txt
python3 -m pytest tests/ -q

# In-place pack (destructive to stale tail only)
PYTHONPATH=. python3 -m redata.cli pack ./myfile.json

# Restore to sibling path (safe)
PYTHONPATH=. python3 -m redata.cli restore ./myfile.wrdt -o ./myfile.json

# Bench memory speed
PYTHONPATH=. python3 -m redata.cli bench ./myfile.json
```

### Web UI (drag and drop)

```bash
PYTHONPATH=. python3 web/app.py
# open http://127.0.0.1:9478/
```

---

## WRDT1 layout (52-byte header)

| Offset | Field |
|--------|-------|
| 0 | Magic `WRDT` |
| 4 | Version, method, flags |
| 8 | Original size (u64) |
| 16 | Payload length (u32) |
| 20 | SHA-256 of original |
| 52 | Payload (store or zlib-1) |

---

## Tiny-file safety

Header is 52 bytes. In-place pack runs only when:

```
len(WRDT1 envelope) < original file size
```

Otherwise the tool skips — no risk of overlapping inode capacity with a larger envelope.

---

## Wiki

- [Home](wiki/Home.md)
- [Format spec](wiki/Format-Spec.md)
- [In-place tail clear](wiki/In-Place-Tail-Clear.md)
- [Hostess7 / Field Technology bridge](wiki/Hostess7-Bridge.md)

---

## Related office work

Field Technology redata pipeline (segments, ZAC7, SDF plates) lives under `SG/Hostess7` and `SG/Field_Primer`. World_Redata is the **portable in-place tool** layer — same lossless discipline, different job than brain imaging.

---

## License

Proprietary. No redistribution without written permission from Zachary Geurts.
