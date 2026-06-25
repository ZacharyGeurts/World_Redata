# Hostess7 / Field Technology Bridge

World_Redata (`WRDT1`) complements the office redata pipeline — it does not replace it.

| Layer | Job |
|-------|-----|
| **Hostess7** | Mayer segments → `seg-*.json` + truth filter + SDF plates |
| **ZAC7** | Sovereign field transport tar + manifest |
| **FLD1** | Brain JSON fly codec inside ZAC |
| **WRDT1** | Portable in-place file envelopes + web drag-drop |

## Shared doctrine

> Imaging is not the codec. Lossless bytes are provable. Tail clear is inode-local.

## Integration path

1. Pack chapter JSON with `world-redata pack` before ZAC staging
2. Verify with `world-redata verify`
3. Existing `build-field-technology-zac.py` can ingest restored bytes from WRDT1 exports

Queen / Hostess7 commands unchanged — World_Redata is a sibling tool repo.