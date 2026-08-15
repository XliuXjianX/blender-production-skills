#!/usr/bin/env python3
"""Report complete, missing, or Git LFS pointer source files in a local asset library."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from search_local_asset_library import DEFAULT_LIBRARY_ROOT, resolve_library_root, source_file_status, load_index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = resolve_library_root(args.root)
    if root is None:
        payload = {
            "schema_version": "1.0",
            "status": "library_not_found",
            "default_root": str(DEFAULT_LIBRARY_ROOT),
            "sources": [],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 2

    index, assets, _ = load_index(root)
    relative_paths = sorted(
        {
            str(relative)
            for asset in assets
            for relative in asset.get("files", [])
        }
    )
    sources = [source_file_status(root, relative) for relative in relative_paths]
    complete = sum(bool(item["usable_source"]) for item in sources)
    pointers = sum(bool(item["git_lfs_pointer"]) for item in sources)
    payload = {
        "schema_version": "1.0",
        "status": "ok",
        "library_root": str(root),
        "asset_count": int(index.get("asset_count", len(assets))),
        "source_count": len(sources),
        "complete_source_count": complete,
        "git_lfs_pointer_count": pointers,
        "sources": sources,
        "read_only": True,
    }
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
