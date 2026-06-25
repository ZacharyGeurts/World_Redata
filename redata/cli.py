#!/usr/bin/env python3
"""World Redata CLI — in-place lossless tail-clear conversion."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from redata.core import bench, is_redata, redata_inplace, redata_restore_to, redata_unpack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="world-redata",
        description="WRDT1 lossless in-place conversion with tail clear",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    pack = sub.add_parser("pack", help="Pack file in-place (truncate tail)")
    pack.add_argument("path", type=Path)
    pack.add_argument("--dry-run", action="store_true")
    pack.add_argument("--min-gain", type=float, default=1.0)

    restore = sub.add_parser("restore", help="Restore WRDT1 to output path")
    restore.add_argument("path", type=Path)
    restore.add_argument("-o", "--output", type=Path, required=True)

    verify = sub.add_parser("verify", help="Verify WRDT1 envelope")
    verify.add_argument("path", type=Path)

    bench_p = sub.add_parser("bench", help="Benchmark pack/unpack in memory")
    bench_p.add_argument("path", type=Path)

    cat = sub.add_parser("cat", help="Stdout restored bytes")
    cat.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "pack":
            rep = redata_inplace(args.path, min_gain=args.min_gain, dry_run=args.dry_run)
        elif args.cmd == "restore":
            rep = redata_restore_to(args.path, args.output)
        elif args.cmd == "verify":
            blob = args.path.read_bytes()
            if not is_redata(blob):
                rep = {"ok": False, "reason": "not WRDT1"}
            else:
                body = redata_unpack(blob)
                rep = {"ok": True, "restored_bytes": len(body)}
        elif args.cmd == "bench":
            raw = args.path.read_bytes()
            if is_redata(raw):
                raw = redata_unpack(raw)
            rep = bench(raw)
        elif args.cmd == "cat":
            sys.stdout.buffer.write(redata_unpack(args.path.read_bytes()))
            return 0
        else:
            return 2
        print(json.dumps(rep, indent=2))
        return 0 if rep.get("ok", True) else 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())