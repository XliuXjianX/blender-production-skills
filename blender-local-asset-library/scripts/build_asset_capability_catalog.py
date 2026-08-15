#!/usr/bin/env python3
"""Build a read-only, inspected capability catalog for a local Blender asset library."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from search_local_asset_library import (
    DEFAULT_LIBRARY_ROOT,
    load_index,
    owner_for_catalog,
    resolve_library_root,
    source_file_status,
)


SCRIPT_DIR = Path(__file__).resolve().parent
INSPECTOR = SCRIPT_DIR / "inspect_local_asset_blend.py"


def _compact_group(group: dict[str, Any]) -> dict[str, Any]:
    interface = group.get("public_interface", [])
    return {
        "name": group.get("name"),
        "tree_type": group.get("tree_type"),
        "is_modifier": bool(group.get("is_modifier")),
        "is_asset": bool(group.get("is_asset")),
        "asset_metadata": group.get("asset_metadata"),
        "public_inputs": [item for item in interface if item.get("in_out") == "INPUT"],
        "public_outputs": [item for item in interface if item.get("in_out") == "OUTPUT"],
        "node_count": group.get("node_count"),
        "link_count": group.get("link_count"),
        "frame_count": group.get("frame_count"),
        "node_types": group.get("node_types", {}),
        "nested_node_groups": group.get("nested_node_groups", []),
        "uses_instances": bool(group.get("uses_instances")),
        "realize_instances_count": group.get("realize_instances_count", 0),
        "uses_simulation_zone": bool(group.get("uses_simulation_zone")),
        "uses_repeat_zone": bool(group.get("uses_repeat_zone")),
    }


def _compact_data_block(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": block.get("name"),
        "type": block.get("type"),
        "is_asset": block.get("is_asset"),
        "asset_metadata": block.get("asset_metadata"),
        "data_name": block.get("data_name"),
        "modifiers": block.get("modifiers", []),
        "material_slots": block.get("material_slots", []),
        "node_tree_type": block.get("node_tree_type"),
        "node_count": block.get("node_count"),
        "node_types": block.get("node_types", {}),
        "object_names": block.get("object_names", []),
    }


def _run_inspection(
    blender: Path,
    root: Path,
    source_rel: str,
    work_dir: Path,
) -> dict[str, Any]:
    source = root / source_rel
    report = work_dir / (source_rel.replace("/", "__").replace("\\", "__") + ".json")
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        str(source),
        "--python",
        str(INSPECTOR),
        "--",
        str(report),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    record: dict[str, Any] = {
        "source_blend": source_rel,
        "status": "inspected" if completed.returncode == 0 and report.is_file() else "inspection_failed",
        "returncode": completed.returncode,
        "report_path": str(report),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }
    if record["status"] == "inspected":
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
            record.update(
                {
                    "blender_version": payload.get("blender_version"),
                    "group_count": payload.get("matched_group_count", 0),
                    "node_groups": payload.get("node_groups", []),
                    "objects": payload.get("objects", []),
                    "materials": payload.get("materials", []),
                    "collections": payload.get("collections", []),
                }
            )
        except (OSError, json.JSONDecodeError) as exc:
            record["status"] = "inspection_report_invalid"
            record["error"] = str(exc)
    return record


def build_catalog(root: Path, blender: Path, work_dir: Path) -> dict[str, Any]:
    index, assets, catalog_by_id = load_index(root)
    source_paths = sorted(
        {
            str(path)
            for asset in assets
            for path in asset.get("files", [])
        }
    )
    source_statuses = {
        source: source_file_status(root, source) for source in source_paths
    }
    work_dir.mkdir(parents=True, exist_ok=True)
    inspections: dict[str, dict[str, Any]] = {}
    for source in source_paths:
        status = source_statuses[source]
        if not status["usable_source"]:
            inspections[source] = {
                "source_blend": source,
                "status": "source_unavailable",
                "source_status": status,
                "node_groups": [],
            }
            continue
        inspected = _run_inspection(blender, root, source, work_dir)
        inspected["source_status"] = status
        inspections[source] = inspected

    by_source_and_name: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_source_and_object_name: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_source_and_material_name: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_source_and_collection_name: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for source, inspection in inspections.items():
        for group in inspection.get("node_groups", []):
            by_source_and_name.setdefault((source, str(group.get("name", ""))), []).append(group)
        for obj in inspection.get("objects", []):
            by_source_and_object_name.setdefault((source, str(obj.get("name", ""))), []).append(obj)
        for material in inspection.get("materials", []):
            by_source_and_material_name.setdefault((source, str(material.get("name", ""))), []).append(material)
        for collection in inspection.get("collections", []):
            by_source_and_collection_name.setdefault((source, str(collection.get("name", ""))), []).append(collection)

    catalog_assets: list[dict[str, Any]] = []
    inspected_count = 0
    unavailable_count = 0
    unmatched_count = 0
    for asset in assets:
        meta = asset.get("meta", {})
        source_blends = [str(value) for value in asset.get("files", [])]
        catalog = catalog_by_id.get(str(meta.get("catalog_id", "")), "Uncategorized")
        groups = [
            _compact_group(group)
            for source in source_blends
            for group in by_source_and_name.get((source, str(asset.get("name", ""))), [])
        ]
        data_blocks = [
            _compact_data_block(block)
            for source in source_blends
            for block in (
                by_source_and_object_name.get((source, str(asset.get("name", ""))), [])
                + by_source_and_material_name.get((source, str(asset.get("name", ""))), [])
                + by_source_and_collection_name.get((source, str(asset.get("name", ""))), [])
            )
        ]
        usable_sources = [
            source
            for source in source_blends
            if source_statuses.get(source, {}).get("usable_source")
        ]
        failed_sources = [
            source
            for source in source_blends
            if inspections.get(source, {}).get("status") not in {"inspected", "source_unavailable"}
        ]
        if groups or data_blocks:
            status = "inspected"
            inspected_count += 1
        elif not usable_sources:
            status = "source_unavailable"
            unavailable_count += 1
        elif failed_sources:
            status = "inspection_failed"
            unmatched_count += 1
        else:
            status = "asset_group_not_matched"
            unmatched_count += 1
        catalog_assets.append(
            {
                "name": str(asset.get("name", "")),
                "id_type": str(asset.get("id_type", "")),
                "catalog": catalog,
                "description": str(meta.get("description", "")),
                "source_blends": source_blends,
                "source_statuses": [source_statuses[source] for source in source_blends],
                "minimum_blender_version": asset.get("bl_versions", {}).get("min"),
                "recommended_owner_skill": owner_for_catalog(catalog),
                "inspection_status": status,
                "node_groups": groups,
                "data_blocks": data_blocks,
            }
        )
    catalog_assets.sort(key=lambda item: (item["catalog"], item["name"].lower()))
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "library_root": str(root),
        "blender_executable": str(blender),
        "asset_count": int(index.get("asset_count", len(assets))),
        "source_count": len(source_paths),
        "source_inspections": [inspections[source] for source in source_paths],
        "inspected_asset_count": inspected_count,
        "source_unavailable_asset_count": unavailable_count,
        "unmatched_or_failed_asset_count": unmatched_count,
        "assets": catalog_assets,
        "limitations": [
            "An inspected interface and graph topology are evidence for retrieval, not proof of aesthetic suitability.",
            "Assets whose source files are unavailable remain unavailable and must not be selected for production.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Asset root or parent directory")
    parser.add_argument("--blender", required=True, help="Absolute Blender executable path")
    parser.add_argument("--output", required=True, help="Capability catalog JSON output path")
    parser.add_argument("--work-dir", help="Directory for per-source inspection reports")
    args = parser.parse_args()

    root = resolve_library_root(args.root)
    if root is None:
        raise SystemExit(f"Asset library not found; checked default {DEFAULT_LIBRARY_ROOT}")
    blender = Path(args.blender).expanduser().resolve()
    if not blender.is_file():
        raise SystemExit(f"Blender executable not found: {blender}")
    output = Path(args.output).expanduser().resolve()
    work_dir = (
        Path(args.work_dir).expanduser().resolve()
        if args.work_dir
        else output.parent / "source-inspections"
    )
    payload = build_catalog(root, blender, work_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(output),
                "asset_count": payload["asset_count"],
                "inspected_asset_count": payload["inspected_asset_count"],
                "source_unavailable_asset_count": payload["source_unavailable_asset_count"],
                "unmatched_or_failed_asset_count": payload["unmatched_or_failed_asset_count"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
