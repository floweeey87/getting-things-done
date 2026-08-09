#!/usr/bin/env python3
"""Build content-sync/manifest.json and ready.json for kurssturzkompass.de.

Reads all part-*.html files (sorted) from articles/<source-dir>/, joins them,
base64-encodes the result and stamps a sha256 over exactly the bytes that were
encoded, so the consuming bridge can verify integrity. Bumps the manifest
version by one on every invocation.

Usage:
  python3 kurssturzkompass/scripts/build_manifest.py \
      --source-dir article-001 \
      --slug beispiel-ag-aktie \
      --title "Beispiel AG-Aktie nach Q2-Zahlen 2026: ..." \
      --excerpt "..."
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARTICLES = BASE / "articles"
SYNC = BASE / "content-sync"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-dir", required=True, help="directory under articles/, e.g. article-001")
    ap.add_argument("--slug", required=True, help="exact WordPress slug of the article")
    ap.add_argument("--title", required=True)
    ap.add_argument("--excerpt", required=True)
    args = ap.parse_args()

    src = ARTICLES / args.source_dir
    parts = sorted(src.glob("part-*.html"))
    if not parts:
        print(f"error: no part-*.html files in {src}", file=sys.stderr)
        return 1

    content = "\n".join(p.read_text(encoding="utf-8").rstrip("\n") for p in parts)
    raw = content.encode("utf-8")
    b64 = base64.b64encode(raw).decode("ascii")
    sha = hashlib.sha256(raw).hexdigest()

    manifest_path = SYNC / "manifest.json"
    ready_path = SYNC / "ready.json"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": 0}
    version = int(old.get("version", 0)) + 1

    manifest = {
        "version": version,
        "updates": [
            {
                "slug": args.slug,
                "title": args.title,
                "excerpt": args.excerpt,
                "content_base64": b64,
                "content_sha256": sha,
            }
        ],
    }
    ready = {
        "version": version,
        "slug": args.slug,
        "title": args.title,
        "excerpt": args.excerpt,
        "source_dir": args.source_dir,
    }

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    ready_path.write_text(json.dumps(ready, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    # self-check: decode what we wrote and compare hashes
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    check = hashlib.sha256(base64.b64decode(written["updates"][0]["content_base64"])).hexdigest()
    if check != written["updates"][0]["content_sha256"]:
        print("error: sha256 self-check failed", file=sys.stderr)
        return 1

    print(f"manifest version {version}: slug={args.slug} parts={len(parts)} bytes={len(raw)} sha256={sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
