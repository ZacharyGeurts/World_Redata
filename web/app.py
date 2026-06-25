#!/usr/bin/env python3
"""World Redata drag-and-drop web surface."""
from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file

from redata.core import bench, is_redata, redata_pack, redata_unpack, sha256

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, static_folder=".", static_url_path="")


@app.get("/")
def index() -> object:
    return app.send_static_file("index.html")


@app.post("/api/pack")
def api_pack() -> object:
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "no file"}), 400
    f = request.files["file"]
    raw = f.read()
    name = f.filename or "upload.bin"
    packed = redata_pack(raw)
    if packed is None:
        return jsonify({
            "ok": True,
            "skipped": True,
            "reason": "envelope not smaller — in-place tail clear skipped",
            "raw_bytes": len(raw),
        })
    return send_file(
        io.BytesIO(packed),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=f"{Path(name).stem}.wrdt",
    )


@app.post("/api/restore")
def api_restore() -> object:
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "no file"}), 400
    f = request.files["file"]
    blob = f.read()
    if not is_redata(blob):
        return jsonify({"ok": False, "error": "not WRDT1"}), 400
    body = redata_unpack(blob)
    orig_name = (f.filename or "restored.bin").replace(".wrdt", "")
    return send_file(
        io.BytesIO(body),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=orig_name,
    )


@app.post("/api/bench")
def api_bench() -> object:
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "no file"}), 400
    raw = request.files["file"].read()
    if is_redata(raw):
        raw = redata_unpack(raw)
    return jsonify({"ok": True, **bench(raw)})


@app.post("/api/batch")
def api_batch() -> object:
    files = request.files.getlist("files")
    if not files:
        return jsonify({"ok": False, "error": "no files"}), 400
    buf = io.BytesIO()
    rows = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            raw = f.read()
            packed = redata_pack(raw)
            entry = f.filename or "file.bin"
            if packed is None:
                rows.append({"file": entry, "skipped": True})
                zf.writestr(entry, raw)
            else:
                rows.append({
                    "file": entry,
                    "raw_bytes": len(raw),
                    "stored_bytes": len(packed),
                    "lossless": redata_unpack(packed) == raw,
                })
                zf.writestr(f"{Path(entry).stem}.wrdt", packed)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name="world-redata-batch.zip")


def main() -> None:
    app.run(host="127.0.0.1", port=9478, debug=False)


if __name__ == "__main__":
    main()