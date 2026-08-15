#!/usr/bin/env python3
"""Deterministic tests for official-document indexing and public artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Previously built official docs index")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    docs = _load_module(script_dir / "search_official_blender_docs.py", "official_docs")
    index_path = Path(args.index).expanduser().resolve()
    existing = json.loads(index_path.read_text(encoding="utf-8"))
    tests: list[dict[str, Any]] = []

    allowed = [
        "https://docs.blender.org/manual/en/5.2/modeling/index.html",
        "https://extensions.blender.org/add-ons/",
    ]
    blocked = [
        "http://docs.blender.org/manual/en/5.2/",
        "https://example.com/blender",
        "file:///C:/temp/index.html",
    ]
    allowlist_ok = all(docs._allow_url(url) for url in allowed) and not any(
        docs._allow_url(url) for url in blocked
    )
    tests.append(_result("official_domain_allowlist", allowlist_ok, "Only official HTTPS hosts are accepted."))

    original_download = docs._download

    def unavailable(_url: str) -> bytes:
        raise OSError("offline test")

    docs._download = unavailable
    try:
        cached = docs.build_index(str(existing.get("blender_manual_version", "5.2")), existing)
    finally:
        docs._download = original_download
    cached_ok = (
        len(cached.get("entries", [])) == len(existing.get("entries", []))
        and bool(cached.get("entries"))
        and set(cached.get("source_status", {}).values()) == {"cached"}
        and all(docs._allow_url(entry["url"]) for entry in cached.get("entries", []))
    )
    tests.append(_result("offline_cached_fallback", cached_ok, "Network failure reuses the verified cached index."))

    search_results = docs.search(existing, "布料碰撞 self collision", 8)
    search_ok = bool(search_results) and all(
        docs._allow_url(item["url"]) for item in search_results
    )
    tests.append(_result("official_search_results", search_ok, f"Found {len(search_results)} official results."))

    raycast_results = docs.search(existing, "Shader Raycast only local", 10)
    raycast_ok = bool(raycast_results) and any(
        "ShaderNodeRaycast" in item["url"] or "/raycast.html" in item["url"]
        for item in raycast_results
    ) and all(docs._allow_url(item["url"]) for item in raycast_results)
    tests.append(
        _result(
            "cycles_shader_raycast_docs",
            raycast_ok,
            f"Found {len(raycast_results)} official Shader Raycast results.",
        )
    )

    with tempfile.TemporaryDirectory(prefix="official_docs_resolve_") as temp:
        cache_root = Path(temp)
        cache_path = cache_root / "5.2" / "official_blender_docs_index.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(index_path, cache_path)
        resolved = docs.resolve_official_sources(
            "5.2",
            "Array modifier stairs constant offset",
            cache_root=cache_root,
            offline=True,
        )
        resolve_ok = (
            resolved.get("status") == "cached"
            and bool(resolved.get("results"))
            and all(docs._allow_url(item["url"]) for item in resolved["results"])
        )
        tests.append(
            _result(
                "versioned_official_source_resolution",
                resolve_ok,
                f"Resolved {len(resolved.get('results', []))} cached official pages.",
            )
        )

    output = {
        "schema_version": "1.0",
        "passed": all(test["passed"] for test in tests),
        "test_count": len(tests),
        "tests": tests,
    }
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
