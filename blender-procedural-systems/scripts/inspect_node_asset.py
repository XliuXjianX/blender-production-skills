#!/usr/bin/env python3
"""Export a readable inventory of node-based Blender assets.

Run with Blender:
    blender.exe asset.blend --background --python inspect_node_asset.py -- output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import bpy


NODE_PROPERTIES = (
    "operation",
    "data_type",
    "domain",
    "mode",
    "input_type",
    "clamp",
    "mapping",
    "transform_space",
    "target_element",
    "axis",
    "pivot_axis",
    "spline_type",
    "fill_type",
    "realize_all",
)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "to_list"):
        return [_json_value(item) for item in value.to_list()]
    if hasattr(value, "__iter__") and not isinstance(value, (bpy.types.ID, bytes)):
        try:
            return [_json_value(item) for item in value]
        except (TypeError, ValueError):
            pass
    if isinstance(value, bpy.types.ID):
        return {"id_type": value.bl_rna.identifier, "name": value.name}
    return str(value)


def _socket(socket: bpy.types.NodeSocket) -> dict[str, Any]:
    payload = {
        "name": socket.name,
        "identifier": getattr(socket, "identifier", ""),
        "type": socket.bl_idname,
        "is_linked": socket.is_linked,
        "enabled": socket.enabled,
        "hide": socket.hide,
    }
    if hasattr(socket, "default_value"):
        try:
            payload["default_value"] = _json_value(socket.default_value)
        except (AttributeError, TypeError, ValueError):
            pass
    return payload


def _node(node: bpy.types.Node) -> dict[str, Any]:
    payload = {
        "name": node.name,
        "label": node.label,
        "type": node.type,
        "bl_idname": node.bl_idname,
        "location": [round(float(node.location.x), 3), round(float(node.location.y), 3)],
        "width": round(float(node.width), 3),
        "hide": node.hide,
        "mute": node.mute,
        "parent": node.parent.name if node.parent else None,
        "inputs": [_socket(socket) for socket in node.inputs],
        "outputs": [_socket(socket) for socket in node.outputs],
    }
    if hasattr(node, "node_tree") and node.node_tree:
        payload["node_tree"] = node.node_tree.name
    properties: dict[str, Any] = {}
    for name in NODE_PROPERTIES:
        if hasattr(node, name):
            try:
                properties[name] = _json_value(getattr(node, name))
            except (AttributeError, TypeError, ValueError):
                pass
    if properties:
        payload["properties"] = properties
    if hasattr(node, "color_ramp"):
        payload["color_ramp"] = {
            "interpolation": node.color_ramp.interpolation,
            "color_mode": node.color_ramp.color_mode,
            "hue_interpolation": node.color_ramp.hue_interpolation,
            "elements": [
                {
                    "position": round(float(element.position), 6),
                    "color": _json_value(element.color),
                }
                for element in node.color_ramp.elements
            ],
        }
    for name in ("blend_type", "noise_dimensions", "normalize", "clamp_factor", "clamp_result"):
        if hasattr(node, name):
            try:
                payload.setdefault("properties", {})[name] = _json_value(getattr(node, name))
            except (AttributeError, TypeError, ValueError):
                pass
    return payload


def _interface(tree: bpy.types.NodeTree) -> list[dict[str, Any]]:
    if not hasattr(tree, "interface"):
        return []
    result = []
    for item in tree.interface.items_tree:
        payload = {
            "name": item.name,
            "item_type": item.item_type,
            "identifier": getattr(item, "identifier", ""),
        }
        for name in ("in_out", "socket_type", "description"):
            if hasattr(item, name):
                payload[name] = _json_value(getattr(item, name))
        if hasattr(item, "default_value"):
            try:
                payload["default_value"] = _json_value(item.default_value)
            except (AttributeError, TypeError, ValueError):
                pass
        result.append(payload)
    return result


def _node_tree(tree: bpy.types.NodeTree) -> dict[str, Any]:
    def socket_index(sockets: Any, target: bpy.types.NodeSocket) -> int:
        for index, socket in enumerate(sockets):
            if socket == target:
                return index
        return -1

    return {
        "name": tree.name,
        "type": tree.bl_idname,
        "users": tree.users,
        "is_modifier": bool(getattr(tree, "is_modifier", False)),
        "interface": _interface(tree),
        "nodes": [_node(node) for node in tree.nodes],
        "links": [
            {
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "from_socket_index": socket_index(link.from_node.outputs, link.from_socket),
                "from_socket_identifier": getattr(link.from_socket, "identifier", ""),
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name,
                "to_socket_index": socket_index(link.to_node.inputs, link.to_socket),
                "to_socket_identifier": getattr(link.to_socket, "identifier", ""),
                "is_muted": link.is_muted,
            }
            for link in tree.links
        ],
    }


def _modifier(modifier: bpy.types.Modifier) -> dict[str, Any]:
    payload = {
        "name": modifier.name,
        "type": modifier.type,
        "show_viewport": modifier.show_viewport,
        "show_render": modifier.show_render,
    }
    if modifier.type == "NODES" and modifier.node_group:
        payload["node_group"] = modifier.node_group.name
        values = {}
        for item in modifier.node_group.interface.items_tree:
            if item.item_type != "SOCKET" or getattr(item, "in_out", "") != "INPUT":
                continue
            identifier = getattr(item, "identifier", "")
            if not identifier:
                continue
            try:
                values[item.name] = _json_value(modifier[identifier])
            except (KeyError, TypeError):
                continue
        payload["input_values"] = values
    return payload


def _object(obj: bpy.types.Object) -> dict[str, Any]:
    return {
        "name": obj.name,
        "type": obj.type,
        "location": _json_value(obj.location),
        "rotation_euler": _json_value(obj.rotation_euler),
        "scale": _json_value(obj.scale),
        "dimensions": _json_value(obj.dimensions),
        "data": obj.data.name if obj.data else None,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers": [_modifier(modifier) for modifier in obj.modifiers],
    }


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Expected output JSON path after --")
    output_path = Path(args[0]).expanduser().resolve()
    payload = {
        "schema_version": "1.0",
        "blender_version": bpy.app.version_string,
        "source_file": bpy.data.filepath,
        "active_scene": bpy.context.scene.name,
        "render_engine": bpy.context.scene.render.engine,
        "objects": [_object(obj) for obj in bpy.data.objects],
        "node_groups": [_node_tree(tree) for tree in bpy.data.node_groups],
        "materials": [
            {
                "name": material.name,
                "use_nodes": material.use_nodes,
                "diffuse_color": _json_value(material.diffuse_color),
                "surface_render_method": getattr(material, "surface_render_method", None),
                "use_backface_culling": getattr(material, "use_backface_culling", None),
                "use_backface_culling_shadow": getattr(
                    material, "use_backface_culling_shadow", None
                ),
                "node_tree": _node_tree(material.node_tree)
                if material.use_nodes and material.node_tree
                else None,
            }
            for material in bpy.data.materials
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(output_path),
                "objects": len(payload["objects"]),
                "node_groups": len(payload["node_groups"]),
                "materials": len(payload["materials"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
