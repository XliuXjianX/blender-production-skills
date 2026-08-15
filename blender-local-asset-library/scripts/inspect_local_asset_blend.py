#!/usr/bin/env python3
"""Inspect a local Blender asset source in background Blender without saving it."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import bpy


def _asset_metadata(data_block: Any) -> dict[str, Any] | None:
    asset = getattr(data_block, "asset_data", None)
    if asset is None:
        return None
    tags = []
    try:
        tags = [str(tag.name) for tag in asset.tags]
    except Exception:
        pass
    return {
        "catalog_id": str(getattr(asset, "catalog_id", "")),
        "description": str(getattr(asset, "description", "")),
        "author": str(getattr(asset, "author", "")),
        "tags": tags,
    }


def _interface(group: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in getattr(getattr(group, "interface", None), "items_tree", []):
        if getattr(item, "item_type", None) != "SOCKET":
            continue
        result.append(
            {
                "name": str(getattr(item, "name", "")),
                "identifier": str(getattr(item, "identifier", "")),
                "in_out": str(getattr(item, "in_out", "")),
                "socket_type": str(getattr(item, "socket_type", "")),
            }
        )
    return result


def _group_summary(group: Any) -> dict[str, Any]:
    node_types: dict[str, int] = {}
    nested_groups: list[str] = []
    frames = 0
    for node in group.nodes:
        node_types[node.bl_idname] = node_types.get(node.bl_idname, 0) + 1
        if node.bl_idname == "NodeFrame":
            frames += 1
        nested = getattr(node, "node_tree", None)
        if nested is not None:
            nested_groups.append(str(nested.name))
    return {
        "name": str(group.name),
        "tree_type": str(group.bl_idname),
        "is_modifier": bool(getattr(group, "is_modifier", False)),
        "is_asset": getattr(group, "asset_data", None) is not None,
        "asset_metadata": _asset_metadata(group),
        "public_interface": _interface(group),
        "node_count": len(group.nodes),
        "link_count": len(group.links),
        "frame_count": frames,
        "node_types": dict(sorted(node_types.items())),
        "nested_node_groups": sorted(set(nested_groups)),
        "uses_instances": any("Instance" in node_type for node_type in node_types),
        "realize_instances_count": node_types.get("GeometryNodeRealizeInstances", 0),
        "uses_simulation_zone": any("Simulation" in node_type for node_type in node_types),
        "uses_repeat_zone": any("Repeat" in node_type for node_type in node_types),
    }


def _object_summary(obj: Any) -> dict[str, Any]:
    modifiers = []
    for modifier in obj.modifiers:
        modifiers.append(
            {
                "name": str(modifier.name),
                "type": str(modifier.type),
                "node_group": str(getattr(getattr(modifier, "node_group", None), "name", "")),
            }
        )
    return {
        "name": str(obj.name),
        "type": str(obj.type),
        "is_asset": getattr(obj, "asset_data", None) is not None,
        "asset_metadata": _asset_metadata(obj),
        "data_name": str(getattr(getattr(obj, "data", None), "name", "")),
        "modifiers": modifiers,
        "material_slots": [
            str(getattr(getattr(slot, "material", None), "name", ""))
            for slot in obj.material_slots
        ],
        "dimensions": [round(float(value), 6) for value in obj.dimensions],
    }


def _material_summary(material: Any) -> dict[str, Any]:
    tree = getattr(material, "node_tree", None)
    return {
        "name": str(material.name),
        "is_asset": getattr(material, "asset_data", None) is not None,
        "asset_metadata": _asset_metadata(material),
        "node_tree_type": str(getattr(tree, "bl_idname", "")),
        "node_count": len(tree.nodes) if tree else 0,
        "node_types": (
            {
                node_type: sum(1 for node in tree.nodes if node.bl_idname == node_type)
                for node_type in sorted({node.bl_idname for node in tree.nodes})
            }
            if tree
            else {}
        ),
    }


def _arguments() -> tuple[Path, str | None]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- <output-json-path> [--asset-name <name>]")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if not values:
        raise SystemExit("Expected output JSON path")
    output = Path(values[0]).expanduser().resolve()
    asset_name = None
    if "--asset-name" in values:
        index = values.index("--asset-name")
        if index + 1 >= len(values):
            raise SystemExit("--asset-name requires a value")
        asset_name = values[index + 1]
    return output, asset_name


def main() -> int:
    output, asset_name = _arguments()
    groups = list(bpy.data.node_groups)
    if asset_name:
        groups = [group for group in groups if group.name == asset_name]
    groups.sort(key=lambda group: (group.bl_idname, group.name.lower()))
    payload = {
        "schema_version": "1.0",
        "read_only": True,
        "source_blend": str(bpy.data.filepath),
        "blender_version": bpy.app.version_string,
        "asset_name_filter": asset_name,
        "matched_group_count": len(groups),
        "node_groups": [_group_summary(group) for group in groups],
        "objects": [_object_summary(obj) for obj in sorted(bpy.data.objects, key=lambda item: item.name.lower())],
        "materials": [_material_summary(material) for material in sorted(bpy.data.materials, key=lambda item: item.name.lower())],
        "collections": [
            {
                "name": str(collection.name),
                "is_asset": getattr(collection, "asset_data", None) is not None,
                "asset_metadata": _asset_metadata(collection),
                "object_names": sorted(str(obj.name) for obj in collection.objects),
            }
            for collection in sorted(bpy.data.collections, key=lambda item: item.name.lower())
        ],
        "warning": (
            "This report describes source data only. The owning specialist must still choose, "
            "integrate, and validate a candidate in the task scene."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Some source groups contain legacy or malformed display text. ASCII escapes keep the
    # inspection artifact valid without changing the source .blend.
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "groups": len(groups), "output": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
