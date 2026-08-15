#!/usr/bin/env python3
"""Search a Blueish Blender Asset Library metadata index without changing it."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY_ROOT = Path(
    r"C:\Users\Administrator\Downloads\Assets-main\Assets-main\blender\assets"
)
DEFAULT_CAPABILITY_CATALOG = Path(
    r"C:\Users\Administrator\.codex\cache\blender-production-suite\5.2\blueish_asset_capabilities.json"
)


def _version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    parts = re.findall(r"\d+", str(value))
    if not parts:
        return None
    return tuple(int(part) for part in parts[:3])


def _at_most(required: str | None, runtime: str | None) -> bool | None:
    required_version = _version_tuple(required)
    runtime_version = _version_tuple(runtime)
    if required_version is None or runtime_version is None:
        return None
    length = max(len(required_version), len(runtime_version))
    return required_version + (0,) * (length - len(required_version)) <= runtime_version + (0,) * (length - len(runtime_version))


def resolve_library_root(value: str | None) -> Path | None:
    candidates: list[Path] = []
    for raw in (value, os.environ.get("BLENDER_LOCAL_ASSET_LIBRARY_ROOT")):
        if raw:
            candidates.append(Path(raw).expanduser())
    candidates.append(DEFAULT_LIBRARY_ROOT)
    for candidate in candidates:
        expanded = candidate.resolve()
        for root in (expanded, expanded / "blender" / "assets", expanded / "assets"):
            if (root / "_asset-library-meta.json").is_file() and (root / "_v1" / "asset-index.json").is_file():
                return root
    return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_index(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    index = _read_json(root / "_v1" / "asset-index.json")
    catalog_by_id: dict[str, str] = {}
    for catalog in index.get("catalogs", []):
        for identifier in catalog.get("uuids", []):
            catalog_by_id[str(identifier)] = str(catalog.get("path", "Uncategorized"))
    assets: list[dict[str, Any]] = []
    for page in index.get("pages", []):
        page_path = root / str(page.get("url", ""))
        if page_path.is_file():
            assets.extend(_read_json(page_path).get("assets", []))
    return index, assets, catalog_by_id


def owner_for_catalog(catalog: str) -> str:
    lowered = catalog.lower()
    if "geometry node" in lowered:
        return "blender-geometry-nodes-studio"
    if "material" in lowered or "mfs" in lowered or "shader" in lowered:
        return "blender-material-surfacing"
    if "particle" in lowered or "vfx" in lowered:
        return "blender-simulation-effects"
    if "rigging" in lowered:
        return "blender-deformation-rigging"
    if "stylized" in lowered:
        return "blender-production-router (then Blender NPR skill chosen by render engine)"
    if "compositor" in lowered:
        return "blender-production-router (then compositor or NPR owner)"
    return "blender-production-router"


def _terms(value: str) -> list[str]:
    return [term for term in re.split(r"\s+", value.strip().lower()) if term]


def source_file_status(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        return {
            "path": relative_path,
            "exists": False,
            "git_lfs_pointer": False,
            "usable_source": False,
            "size_bytes": None,
        }
    try:
        with path.open("rb") as handle:
            head = handle.read(96)
        is_pointer = head.startswith(b"version https://git-lfs.github.com/spec/v1")
        size = path.stat().st_size
    except OSError:
        return {
            "path": relative_path,
            "exists": True,
            "git_lfs_pointer": False,
            "usable_source": False,
            "size_bytes": None,
        }
    return {
        "path": relative_path,
        "exists": True,
        "git_lfs_pointer": is_pointer,
        "usable_source": not is_pointer,
        "size_bytes": size,
    }


def resolve_capability_catalog(value: str | None) -> Path | None:
    candidates: list[Path] = []
    for raw in (value, os.environ.get("BLENDER_LOCAL_ASSET_CAPABILITY_CATALOG")):
        if raw:
            candidates.append(Path(raw).expanduser())
    candidates.append(DEFAULT_CAPABILITY_CATALOG)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def load_capability_lookup(path: Path | None) -> dict[tuple[str, str], list[dict[str, Any]]]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    lookup: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for asset in payload.get("assets", []):
        key = (str(asset.get("catalog", "")), str(asset.get("name", "")))
        lookup.setdefault(key, []).append(asset)
    return lookup


def _capability_summary(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    groups = [group for record in records for group in record.get("node_groups", [])]
    data_blocks = [block for record in records for block in record.get("data_blocks", [])]
    node_types: dict[str, int] = {}
    for group in groups:
        for node_type, count in group.get("node_types", {}).items():
            node_types[node_type] = node_types.get(node_type, 0) + int(count)
    return {
        "inspection_status": records[0].get("inspection_status"),
        "runtime_probe_statuses": sorted(
            {
                str(record.get("runtime_probe", {}).get("status"))
                for record in records
                if record.get("runtime_probe")
            }
        ),
        "runtime_callable": all(
            bool(record.get("runtime_probe", {}).get("runtime_callable"))
            for record in records
            if record.get("runtime_probe")
        ) if any(record.get("runtime_probe") for record in records) else None,
        "runtime_integration_modes": sorted(
            {
                str(mode)
                for record in records
                for mode in record.get("runtime_probe", {}).get("integration_modes", [])
            }
        ),
        "source_blends": records[0].get("source_blends", []),
        "tree_types": sorted({str(group.get("tree_type")) for group in groups}),
        "public_inputs": [
            socket
            for group in groups
            for socket in group.get("public_inputs", [])
        ],
        "public_outputs": [
            socket
            for group in groups
            for socket in group.get("public_outputs", [])
        ],
        "node_types": dict(sorted(node_types.items())),
        "nested_node_groups": sorted(
            {
                str(name)
                for group in groups
                for name in group.get("nested_node_groups", [])
            }
        ),
        "uses_instances": any(bool(group.get("uses_instances")) for group in groups),
        "uses_simulation_zone": any(bool(group.get("uses_simulation_zone")) for group in groups),
        "uses_repeat_zone": any(bool(group.get("uses_repeat_zone")) for group in groups),
        "data_blocks": data_blocks,
        "runtime_probe": [
            record.get("runtime_probe")
            for record in records
            if record.get("runtime_probe")
        ],
    }


def search(
    root: Path,
    assets: list[dict[str, Any]],
    catalog_by_id: dict[str, str],
    query: str,
    catalog_filter: str | None,
    type_filter: str | None,
    blender_version: str | None,
    capability_lookup: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    query_terms = _terms(query)
    matches: list[tuple[int, dict[str, Any]]] = []
    for asset in assets:
        meta = asset.get("meta", {})
        catalog = catalog_by_id.get(str(meta.get("catalog_id", "")), "Uncategorized")
        asset_type = str(asset.get("id_type", ""))
        description = str(meta.get("description", ""))
        name = str(asset.get("name", ""))
        haystack = " ".join((name, catalog, description, asset_type)).lower()
        if query_terms and not all(term in haystack for term in query_terms):
            continue
        if catalog_filter and catalog_filter.lower() not in catalog.lower():
            continue
        if type_filter and type_filter.upper() != asset_type.upper():
            continue
        minimum_version = str(asset.get("bl_versions", {}).get("min", "")) or None
        compatible = _at_most(minimum_version, blender_version)
        if compatible is False:
            continue
        source_files = [
            source_file_status(root, str(value))
            for value in asset.get("files", [])
        ]
        score = sum(4 for term in query_terms if term in name.lower())
        score += sum(2 for term in query_terms if term in catalog.lower())
        score += sum(1 for term in query_terms if term in description.lower())
        matches.append(
            (
                score,
                {
                    "name": name,
                    "id_type": asset_type,
                    "catalog": catalog,
                    "description": description,
                    "source_blends": [str(value) for value in asset.get("files", [])],
                    "source_files": source_files,
                    "usable_source_available": any(
                        bool(item.get("usable_source")) for item in source_files
                    ),
                    "minimum_blender_version": minimum_version,
                    "compatible_with_runtime": compatible,
                    "recommended_owner_skill": owner_for_catalog(catalog),
                    "thumbnail": asset.get("thumbnail", {}).get("url"),
                    "inspected_capabilities": _capability_summary(
                        (capability_lookup or {}).get((catalog, name), [])
                    ),
                },
            )
        )
    matches.sort(key=lambda item: (-item[0], item[1]["catalog"], item[1]["name"].lower()))
    return [item[1] for item in matches]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Asset root or parent directory")
    parser.add_argument("--query", default="", help="Terms that must match candidate metadata")
    parser.add_argument("--catalog", help="Case-insensitive catalog path fragment")
    parser.add_argument("--type", dest="type_filter", help="Blender ID type, such as NODETREE")
    parser.add_argument("--blender-version", help="Runtime version used to exclude incompatible assets")
    parser.add_argument(
        "--capability-catalog",
        help="Optional inspected capability catalog JSON; defaults to the versioned local cache when present",
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", help="Optional report path; stdout remains compact JSON")
    args = parser.parse_args()

    root = resolve_library_root(args.root)
    if root is None:
        payload = {
            "schema_version": "1.0",
            "status": "library_not_found",
            "searched_roots": [str(DEFAULT_LIBRARY_ROOT)],
            "candidates": [],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 2

    index, assets, catalog_by_id = load_index(root)
    capability_path = resolve_capability_catalog(args.capability_catalog)
    capability_lookup = load_capability_lookup(capability_path)
    candidates = search(
        root,
        assets,
        catalog_by_id,
        args.query,
        args.catalog,
        args.type_filter,
        args.blender_version,
        capability_lookup,
    )[: max(args.limit, 0)]
    payload = {
        "schema_version": "1.0",
        "status": "ok",
        "library_name": _read_json(root / "_asset-library-meta.json").get("name", "Local Blender Asset Library"),
        "library_root": str(root),
        "asset_count": int(index.get("asset_count", len(assets))),
        "runtime_blender_version": args.blender_version,
        "query": args.query,
        "catalog_filter": args.catalog,
        "type_filter": args.type_filter,
        "capability_catalog": str(capability_path) if capability_path else None,
        "candidate_count": len(candidates),
        "candidates": candidates,
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
