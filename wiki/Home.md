# World Redata Wiki

**Owner:** Zachary Geurts · **Format:** WRDT1 · **License:** Proprietary

## What it is

World Redata converts files into lossless `WRDT1` envelopes. It is **data stewardship**, not a compression product:

- Canonical bytes are recoverable with SHA-256 verification
- In-place mode clears the **file tail** via `ftruncate`
- Neighboring files are never overwritten

## When to use

| Use case | Tool |
|----------|------|
| Shrink JSON/text/jsonl in place | `world-redata pack` |
| Batch download via browser | Web UI `/api/pack` |
| Restore sovereign bytes | `world-redata restore -o out` |
| Brain segments + ZAC | Hostess7 pipeline (see bridge doc) |

## Commands

```bash
PYTHONPATH=. python3 -m redata.cli pack file.json
PYTHONPATH=. python3 -m redata.cli restore file.wrdt -o file.json
```

## IP notice

This wiki, the WRDT1 specification, and all reference code are copyrighted. Do not republish without permission.