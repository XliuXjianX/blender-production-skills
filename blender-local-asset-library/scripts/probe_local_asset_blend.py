#!/usr/bin/env python3
"""Probe data blocks from an already-open asset blend without saving it.

Run this script only through Blender in background mode.  It creates temporary data in the
currently loaded file, forces dependency-graph evaluation, writes a JSON report, and exits
without saving.  A passing probe proves that the data block can be instantiated by the current
Blender runtime; it does not claim that its artistic result is suitable for every task.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

import bpy


TEMP_PREFIX = "__codex_asset_probe__"


def _arguments() -> Path:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- <output-json-path>")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if not values:
        raise SystemExit("Expected output JSON path")
    return Path(values[0]).expanduser().resolve()


def _socket_type(socket: Any) -> str:
    return str(getattr(socket, "type", "") or getattr(socket, "bl_socket_idname", ""))


def _interface_sockets(group: Any, direction: str) -> list[Any]:
    sockets: list[Any] = []
    for item in getattr(getattr(group, "interface", None), "items_tree", []):
        if getattr(item, "item_type", None) == "SOCKET" and str(getattr(item, "in_out", "")) == direction:
            sockets.append(item)
    return sockets


def _temporary_mesh_object(name: str) -> Any:
    mesh = bpy.data.meshes.new(f"{TEMP_PREFIX}{name}_mesh")
    mesh.from_pydata(
        [
            (-0.5, -0.5, -0.5),
            (0.5, -0.5, -0.5),
            (0.5, 0.5, -0.5),
            (-0.5, 0.5, -0.5),
            (-0.5, -0.5, 0.5),
            (0.5, -0.5, 0.5),
            (0.5, 0.5, 0.5),
            (-0.5, 0.5, 0.5),
        ],
        [],
        [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (4, 0, 3, 7),
        ],
    )
    mesh.update()
    obj = bpy.data.objects.new(f"{TEMP_PREFIX}{name}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _remove_temporary_object(obj: Any) -> None:
    mesh = getattr(obj, "data", None)
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh is not None and getattr(mesh, "users", 0) == 0:
        bpy.data.meshes.remove(mesh)


def _mesh_evidence(obj: Any) -> dict[str, Any]:
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = None
    try:
        mesh = evaluated.to_mesh()
        return {
            "vertex_count": len(mesh.vertices),
            "edge_count": len(mesh.edges),
            "polygon_count": len(mesh.polygons),
        }
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()


def _geometry_probe(group: Any) -> dict[str, Any]:
    outputs = _interface_sockets(group, "OUTPUT")
    first_output_is_geometry = bool(outputs) and str(getattr(outputs[0], "socket_type", "")) == "NodeSocketGeometry"
    if not first_output_is_geometry:
        host = bpy.data.node_groups.new(f"{TEMP_PREFIX}{group.name}", "GeometryNodeTree")
        try:
            node = host.nodes.new("GeometryNodeGroup")
            node.node_tree = group
            host.update_tag()
            return {
                "kind": "geometry_node_group",
                "status": "passed",
                "integration_mode": "nested_group",
                "modifier_eligible": False,
                "public_input_count": len(_interface_sockets(group, "INPUT")),
                "public_output_count": len(outputs),
                "note": "This is a field or helper group. It is valid inside a Geometry Nodes graph but is not a standalone modifier output.",
            }
        finally:
            bpy.data.node_groups.remove(host)

    obj = _temporary_mesh_object(str(group.name))
    try:
        modifier = obj.modifiers.new(f"{TEMP_PREFIX}nodes", "NODES")
        modifier.node_group = group
        bpy.context.view_layer.update()
        evidence = _mesh_evidence(obj)
        error = str(getattr(modifier, "error", "") or "")
        return {
            "kind": "geometry_node_group",
            "status": "passed" if not error else "warning",
            "integration_mode": "modifier",
            "modifier_eligible": True,
            "modifier_name": str(modifier.name),
            "modifier_error": error or None,
            "evaluated_mesh": evidence,
            "public_input_count": len(_interface_sockets(group, "INPUT")),
            "public_output_count": len(_interface_sockets(group, "OUTPUT")),
        }
    finally:
        _remove_temporary_object(obj)


def _first_output_socket(node: Any, socket_type: str) -> Any | None:
    for socket in node.outputs:
        if _socket_type(socket) == socket_type:
            return socket
    return None


def _shader_probe(group: Any) -> dict[str, Any]:
    material = bpy.data.materials.new(f"{TEMP_PREFIX}{group.name}")
    try:
        material.use_nodes = True
        tree = material.node_tree
        assert tree is not None
        group_node = tree.nodes.new("ShaderNodeGroup")
        group_node.node_tree = group
        output = tree.nodes.get("Material Output") or tree.nodes.new("ShaderNodeOutputMaterial")
        shader_output = _first_output_socket(group_node, "SHADER")
        color_output = _first_output_socket(group_node, "RGBA")
        link_mode = "unlinked"
        if shader_output is not None:
            tree.links.new(shader_output, output.inputs["Surface"])
            link_mode = "shader_to_surface"
        elif color_output is not None:
            principled = tree.nodes.get("Principled BSDF") or tree.nodes.new("ShaderNodeBsdfPrincipled")
            tree.links.new(color_output, principled.inputs["Base Color"])
            tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
            link_mode = "color_to_principled"
        tree.update_tag()
        bpy.context.view_layer.update()
        return {
            "kind": "shader_node_group",
            "status": "passed",
            "link_mode": link_mode,
            "public_input_count": len(_interface_sockets(group, "INPUT")),
            "public_output_count": len(_interface_sockets(group, "OUTPUT")),
        }
    finally:
        bpy.data.materials.remove(material)


def _compositor_probe(group: Any) -> dict[str, Any]:
    scene = bpy.data.scenes.new(f"{TEMP_PREFIX}{group.name}")
    try:
        tree = bpy.data.node_groups.new(f"{TEMP_PREFIX}{group.name}", "CompositorNodeTree")
        scene.compositing_node_group = tree
        group_node = tree.nodes.new("CompositorNodeGroup")
        group_node.node_tree = group
        image_output = _first_output_socket(group_node, "RGBA")
        tree.update_tag()
        return {
            "kind": "compositor_node_group",
            "status": "passed",
            "integration_mode": "scene_compositing_group",
            "has_image_output": image_output is not None,
            "public_input_count": len(_interface_sockets(group, "INPUT")),
            "public_output_count": len(_interface_sockets(group, "OUTPUT")),
            "note": "Blender 5.2 compositor output nodes are managed by the scene pipeline; this confirms group instantiation and interface availability.",
        }
    finally:
        tree = getattr(scene, "compositing_node_group", None)
        bpy.data.scenes.remove(scene)
        if tree is not None and getattr(tree, "users", 0) == 0:
            bpy.data.node_groups.remove(tree)


def _generic_group_probe(group: Any) -> dict[str, Any]:
    return {
        "kind": str(getattr(group, "bl_idname", "node_group")),
        "status": "passed",
        "public_input_count": len(_interface_sockets(group, "INPUT")),
        "public_output_count": len(_interface_sockets(group, "OUTPUT")),
        "note": "Interface was read; this node-tree class has no isolated runtime evaluator in this probe.",
    }


def _node_group_probe(group: Any) -> dict[str, Any]:
    tree_type = str(getattr(group, "bl_idname", ""))
    if tree_type == "GeometryNodeTree":
        return _geometry_probe(group)
    if tree_type == "ShaderNodeTree":
        return _shader_probe(group)
    if tree_type == "CompositorNodeTree":
        return _compositor_probe(group)
    return _generic_group_probe(group)


def _object_probe(obj: Any) -> dict[str, Any]:
    bpy.context.view_layer.update()
    result = {
        "kind": "object",
        "status": "passed",
        "object_type": str(obj.type),
        "modifier_count": len(obj.modifiers),
        "material_slot_count": len(obj.material_slots),
    }
    if obj.type == "MESH":
        result["evaluated_mesh"] = _mesh_evidence(obj)
    return result


def _material_probe(material: Any) -> dict[str, Any]:
    obj = _temporary_mesh_object(str(material.name))
    try:
        obj.data.materials.append(material)
        bpy.context.view_layer.update()
        return {
            "kind": "material",
            "status": "passed",
            "node_count": len(material.node_tree.nodes) if material.node_tree else 0,
            "attached_to_temporary_mesh": True,
        }
    finally:
        _remove_temporary_object(obj)


def _collection_probe(collection: Any) -> dict[str, Any]:
    evaluated_objects = 0
    mesh_evaluations = 0
    for obj in collection.all_objects:
        evaluated_objects += 1
        if obj.type == "MESH":
            _mesh_evidence(obj)
            mesh_evaluations += 1
    return {
        "kind": "collection",
        "status": "passed",
        "object_count": evaluated_objects,
        "mesh_evaluations": mesh_evaluations,
    }


def _probe(label: str, callback: Any) -> dict[str, Any]:
    try:
        return callback()
    except Exception as exc:  # Keep testing the remaining assets in this source file.
        return {
            "kind": label,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback_tail": traceback.format_exc(limit=4)[-2000:],
        }


def main() -> int:
    output = _arguments()
    groups = sorted(bpy.data.node_groups, key=lambda item: (item.bl_idname, item.name.lower()))
    objects = sorted(bpy.data.objects, key=lambda item: item.name.lower())
    materials = sorted(bpy.data.materials, key=lambda item: item.name.lower())
    collections = sorted(bpy.data.collections, key=lambda item: item.name.lower())
    payload = {
        "schema_version": "1.0",
        "read_only": True,
        "source_blend": str(bpy.data.filepath),
        "blender_version": bpy.app.version_string,
        "node_groups": [
            {"name": str(group.name), "tree_type": str(group.bl_idname), "probe": _probe("node_group", lambda group=group: _node_group_probe(group))}
            for group in groups
        ],
        "objects": [
            {"name": str(obj.name), "object_type": str(obj.type), "probe": _probe("object", lambda obj=obj: _object_probe(obj))}
            for obj in objects
        ],
        "materials": [
            {"name": str(material.name), "probe": _probe("material", lambda material=material: _material_probe(material))}
            for material in materials
        ],
        "collections": [
            {"name": str(collection.name), "probe": _probe("collection", lambda collection=collection: _collection_probe(collection))}
            for collection in collections
        ],
        "limitations": [
            "Passing means the current Blender runtime attached or evaluated the data block without a Python exception.",
            "This probe does not certify artistic intent, all optional input combinations, external media availability, or task-scene compatibility.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    summary = {
        "status": "ok",
        "node_groups": len(groups),
        "objects": len(objects),
        "materials": len(materials),
        "collections": len(collections),
        "output": str(output),
    }
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
