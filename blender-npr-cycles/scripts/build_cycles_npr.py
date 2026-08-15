#!/usr/bin/env python3
"""Build a Blender 5.2 Cycles four-direction Shader Raycast outline.

The script only targets selected mesh objects. It never resets the scene,
World, camera, collections, or unrelated data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import bpy


OWNER = "blender-npr-cycles"
SCHEMA_VERSION = "1.0"
OWNER_PROP = "bps_owner"
ROLE_PROP = "bps_role"

SAMPLE_GROUP_NAME = "BPS_NPR_CYCLES_RAYCAST_SAMPLE"
LOOK_GROUP_NAME = "BPS_NPR_CYCLES_RAYCAST_LOOK"
MATERIAL_NAME = "BPS_NPR_CYCLES_MATERIAL"


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _require_runtime() -> None:
    if bpy.app.version < (5, 2, 0):
        raise RuntimeError(
            f"Shader Raycast outline requires Blender 5.2+, found {bpy.app.version_string}"
        )
    if not hasattr(bpy.types, "ShaderNodeRaycast"):
        raise RuntimeError("ShaderNodeRaycast is unavailable in this Blender runtime")


def _claim_material(preferred_name: str, role: str) -> bpy.types.Material:
    for material in bpy.data.materials:
        if material.get(OWNER_PROP) == OWNER and material.get(ROLE_PROP) == role:
            return material
    material = bpy.data.materials.get(preferred_name)
    if material is not None and material.get(OWNER_PROP) != OWNER:
        material = bpy.data.materials.new(f"{preferred_name}__BPS")
    elif material is None:
        material = bpy.data.materials.new(preferred_name)
    material[OWNER_PROP] = OWNER
    material[ROLE_PROP] = role
    material["bps_schema_version"] = SCHEMA_VERSION
    return material


def _claim_shader_group(preferred_name: str, role: str) -> bpy.types.NodeTree:
    for group in bpy.data.node_groups:
        if (
            group.bl_idname == "ShaderNodeTree"
            and group.get(OWNER_PROP) == OWNER
            and group.get(ROLE_PROP) == role
        ):
            return group
    group = bpy.data.node_groups.get(preferred_name)
    if group is not None and (
        group.bl_idname != "ShaderNodeTree" or group.get(OWNER_PROP) != OWNER
    ):
        group = bpy.data.node_groups.new(f"{preferred_name}__BPS", "ShaderNodeTree")
    elif group is None:
        group = bpy.data.node_groups.new(preferred_name, "ShaderNodeTree")
    group[OWNER_PROP] = OWNER
    group[ROLE_PROP] = role
    group["bps_schema_version"] = SCHEMA_VERSION
    return group


def _clear_interface(node_tree: bpy.types.NodeTree) -> None:
    for item in list(node_tree.interface.items_tree):
        node_tree.interface.remove(item)


def _new_socket(
    node_tree: bpy.types.NodeTree,
    name: str,
    in_out: str,
    socket_type: str,
    *,
    default: Any | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> Any:
    socket = node_tree.interface.new_socket(
        name=name,
        in_out=in_out,
        socket_type=socket_type,
    )
    if default is not None and hasattr(socket, "default_value"):
        socket.default_value = default
    if minimum is not None and hasattr(socket, "min_value"):
        socket.min_value = minimum
    if maximum is not None and hasattr(socket, "max_value"):
        socket.max_value = maximum
    return socket


def _locate(node: bpy.types.Node, x: float, y: float) -> bpy.types.Node:
    node.location = (x, y)
    return node


def build_raycast_sample_group(
    *,
    width: float = 0.02,
    ray_length: float = 100.0,
    only_local: bool = True,
) -> bpy.types.NodeTree:
    """Build one camera-plane-offset Cycles ray sample."""

    _require_runtime()
    group = _claim_shader_group(SAMPLE_GROUP_NAME, "raycast_sample")
    group.nodes.clear()
    _clear_interface(group)

    _new_socket(
        group,
        "Offset",
        "INPUT",
        "NodeSocketVector",
        default=(1.0, 0.0, 0.0),
    )
    _new_socket(
        group,
        "Width",
        "INPUT",
        "NodeSocketFloat",
        default=width,
        minimum=0.0,
        maximum=max(width * 20.0, 1.0),
    )
    _new_socket(
        group,
        "Ray Length",
        "INPUT",
        "NodeSocketFloat",
        default=ray_length,
        minimum=0.001,
        maximum=max(ray_length * 100.0, 1000.0),
    )
    _new_socket(group, "Is Hit", "OUTPUT", "NodeSocketFloat")

    nodes = group.nodes
    links = group.links
    group_input = _locate(nodes.new("NodeGroupInput"), -920, 80)
    group_output = _locate(nodes.new("NodeGroupOutput"), 620, 80)

    geometry = _locate(nodes.new("ShaderNodeNewGeometry"), -920, -170)
    geometry.name = "BPS Surface Position And Incoming"

    camera_to_world = _locate(nodes.new("ShaderNodeVectorTransform"), -650, 170)
    camera_to_world.name = "BPS Camera Offset To World"
    camera_to_world.vector_type = "VECTOR"
    camera_to_world.convert_from = "CAMERA"
    camera_to_world.convert_to = "WORLD"

    offset_scale = _locate(nodes.new("ShaderNodeVectorMath"), -410, 170)
    offset_scale.name = "BPS Scale Outline Offset"
    offset_scale.operation = "SCALE"

    shifted_origin = _locate(nodes.new("ShaderNodeVectorMath"), -150, 130)
    shifted_origin.name = "BPS Shift Ray Origin"
    shifted_origin.operation = "ADD"

    reverse_incoming = _locate(nodes.new("ShaderNodeVectorMath"), -410, -150)
    reverse_incoming.name = "BPS Reverse Incoming Toward Camera"
    reverse_incoming.operation = "SCALE"
    reverse_incoming.inputs["Scale"].default_value = -1.0

    raycast = _locate(nodes.new("ShaderNodeRaycast"), 120, 80)
    raycast.name = "BPS Cycles Silhouette Raycast"
    raycast.only_local = bool(only_local)

    links.new(group_input.outputs["Offset"], camera_to_world.inputs["Vector"])
    links.new(camera_to_world.outputs["Vector"], offset_scale.inputs["Vector"])
    links.new(group_input.outputs["Width"], offset_scale.inputs["Scale"])
    links.new(geometry.outputs["Position"], shifted_origin.inputs[0])
    links.new(offset_scale.outputs["Vector"], shifted_origin.inputs[1])
    links.new(geometry.outputs["Incoming"], reverse_incoming.inputs["Vector"])
    links.new(shifted_origin.outputs["Vector"], raycast.inputs["Position"])
    links.new(reverse_incoming.outputs["Vector"], raycast.inputs["Direction"])
    links.new(group_input.outputs["Ray Length"], raycast.inputs["Length"])
    links.new(raycast.outputs["Is Hit"], group_output.inputs["Is Hit"])

    group["only_local"] = bool(only_local)
    group["ray_count_per_instance"] = 1
    return group


def build_look_group(
    sample_group: bpy.types.NodeTree,
    *,
    base_color: Sequence[float] = (0.42, 0.62, 0.82, 1.0),
    outline_color: Sequence[float] = (0.004, 0.006, 0.01, 1.0),
    width: float = 0.02,
    ray_length: float = 100.0,
    toon_size: float = 0.52,
    toon_smooth: float = 0.03,
) -> bpy.types.NodeTree:
    """Build the four-direction mask and Cycles-compatible toon look."""

    group = _claim_shader_group(LOOK_GROUP_NAME, "raycast_look")
    group.nodes.clear()
    _clear_interface(group)

    _new_socket(group, "Base Color", "INPUT", "NodeSocketColor", default=tuple(base_color))
    _new_socket(
        group,
        "Outline Color",
        "INPUT",
        "NodeSocketColor",
        default=tuple(outline_color),
    )
    _new_socket(
        group,
        "Width",
        "INPUT",
        "NodeSocketFloat",
        default=width,
        minimum=0.0,
        maximum=max(width * 20.0, 1.0),
    )
    _new_socket(
        group,
        "Ray Length",
        "INPUT",
        "NodeSocketFloat",
        default=ray_length,
        minimum=0.001,
        maximum=max(ray_length * 100.0, 1000.0),
    )
    _new_socket(
        group,
        "Toon Size",
        "INPUT",
        "NodeSocketFloat",
        default=toon_size,
        minimum=0.0,
        maximum=1.0,
    )
    _new_socket(
        group,
        "Toon Smooth",
        "INPUT",
        "NodeSocketFloat",
        default=toon_smooth,
        minimum=0.0,
        maximum=1.0,
    )
    _new_socket(group, "Shader", "OUTPUT", "NodeSocketShader")
    _new_socket(group, "Outline Mask", "OUTPUT", "NodeSocketFloat")

    nodes = group.nodes
    links = group.links
    group_input = _locate(nodes.new("NodeGroupInput"), -1000, 40)
    group_output = _locate(nodes.new("NodeGroupOutput"), 780, 40)

    offsets = [
        ("BPS Ray +X", (1.0, 0.0, 0.0), -700, 310),
        ("BPS Ray -X", (-1.0, 0.0, 0.0), -700, 120),
        ("BPS Ray +Y", (0.0, 1.0, 0.0), -700, -70),
        ("BPS Ray -Y", (0.0, -1.0, 0.0), -700, -260),
    ]
    samples: list[bpy.types.Node] = []
    for name, offset, x, y in offsets:
        sample = _locate(nodes.new("ShaderNodeGroup"), x, y)
        sample.name = name
        sample.node_tree = sample_group
        sample.inputs["Offset"].default_value = offset
        links.new(group_input.outputs["Width"], sample.inputs["Width"])
        links.new(group_input.outputs["Ray Length"], sample.inputs["Ray Length"])
        samples.append(sample)

    multiply_x = _locate(nodes.new("ShaderNodeMath"), -400, 240)
    multiply_x.name = "BPS Multiply X Hits"
    multiply_x.operation = "MULTIPLY"
    multiply_y = _locate(nodes.new("ShaderNodeMath"), -400, -150)
    multiply_y.name = "BPS Multiply Y Hits"
    multiply_y.operation = "MULTIPLY"
    multiply_all = _locate(nodes.new("ShaderNodeMath"), -120, 40)
    multiply_all.name = "BPS Interior Hit Mask"
    multiply_all.operation = "MULTIPLY"
    multiply_all.use_clamp = True

    links.new(samples[0].outputs["Is Hit"], multiply_x.inputs[0])
    links.new(samples[1].outputs["Is Hit"], multiply_x.inputs[1])
    links.new(samples[2].outputs["Is Hit"], multiply_y.inputs[0])
    links.new(samples[3].outputs["Is Hit"], multiply_y.inputs[1])
    links.new(multiply_x.outputs[0], multiply_all.inputs[0])
    links.new(multiply_y.outputs[0], multiply_all.inputs[1])

    outline = _locate(nodes.new("ShaderNodeEmission"), 90, 230)
    outline.name = "BPS Unlit Outline"
    outline.inputs["Strength"].default_value = 1.0
    links.new(group_input.outputs["Outline Color"], outline.inputs["Color"])

    toon = _locate(nodes.new("ShaderNodeBsdfToon"), 80, -150)
    toon.name = "BPS Cycles Toon Fill"
    toon.component = "DIFFUSE"
    links.new(group_input.outputs["Base Color"], toon.inputs["Color"])
    links.new(group_input.outputs["Toon Size"], toon.inputs["Size"])
    links.new(group_input.outputs["Toon Smooth"], toon.inputs["Smooth"])

    mix_shader = _locate(nodes.new("ShaderNodeMixShader"), 420, 40)
    mix_shader.name = "BPS Outline Or Toon"
    links.new(multiply_all.outputs[0], mix_shader.inputs[0])
    links.new(outline.outputs["Emission"], mix_shader.inputs[1])
    links.new(toon.outputs["BSDF"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], group_output.inputs["Shader"])
    links.new(multiply_all.outputs[0], group_output.inputs["Outline Mask"])

    group["sample_count"] = 4
    group["ray_count_per_shading_point"] = 4
    return group


def build_material(
    look_group: bpy.types.NodeTree,
) -> bpy.types.Material:
    material = _claim_material(MATERIAL_NAME, "raycast_material")
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = _locate(tree.nodes.new("ShaderNodeOutputMaterial"), 260, 0)
    look = _locate(tree.nodes.new("ShaderNodeGroup"), 0, 0)
    look.name = "BPS Cycles Raycast Look"
    look.node_tree = look_group
    tree.links.new(look.outputs["Shader"], output.inputs["Surface"])
    return material


def _assign_material(
    obj: bpy.types.Object,
    material: bpy.types.Material,
    *,
    replace_material: bool,
) -> str:
    if replace_material:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
        return "replaced_by_explicit_request"
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
        return "assigned_to_empty_slots"
    if material in obj.data.materials.values():
        return "already_present"
    return "preserved_existing_materials"


def selected_mesh_objects() -> list[bpy.types.Object]:
    return [
        obj
        for obj in bpy.context.selected_objects
        if obj.type == "MESH" and not obj.hide_get()
    ]


def apply_to_objects(
    objects: Iterable[bpy.types.Object],
    *,
    width: float = 0.02,
    ray_length: float = 100.0,
    only_local: bool = True,
    base_color: Sequence[float] = (0.42, 0.62, 0.82, 1.0),
    outline_color: Sequence[float] = (0.004, 0.006, 0.01, 1.0),
    toon_size: float = 0.52,
    toon_smooth: float = 0.03,
    replace_material: bool = False,
) -> dict[str, Any]:
    """Apply the Cycles raycast material to explicit mesh objects."""

    _require_runtime()
    mesh_objects = [obj for obj in objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("No mesh objects were provided")

    try:
        bpy.context.scene.render.engine = "CYCLES"
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Cycles is unavailable in this Blender runtime") from exc
    sample_group = build_raycast_sample_group(
        width=width,
        ray_length=ray_length,
        only_local=only_local,
    )
    look_group = build_look_group(
        sample_group,
        base_color=base_color,
        outline_color=outline_color,
        width=width,
        ray_length=ray_length,
        toon_size=toon_size,
        toon_smooth=toon_smooth,
    )
    material = build_material(look_group)

    results = []
    for obj in mesh_objects:
        action = _assign_material(
            obj,
            material,
            replace_material=replace_material,
        )
        results.append({"object": obj.name, "material_action": action})

    return {
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "blender_version": bpy.app.version_string,
        "render_engine": bpy.context.scene.render.engine,
        "objects": results,
        "sample_group": sample_group.name,
        "look_group": look_group.name,
        "material": material.name,
        "ray_samples": 4,
        "offsets": [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]],
        "width": width,
        "ray_length": ray_length,
        "only_local": only_local,
        "replace_material": replace_material,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=float, default=0.02)
    parser.add_argument("--ray-length", type=float, default=100.0)
    parser.add_argument("--scene-aware", action="store_true")
    parser.add_argument("--base-color", type=float, nargs=3, default=(0.42, 0.62, 0.82))
    parser.add_argument("--outline-color", type=float, nargs=3, default=(0.004, 0.006, 0.01))
    parser.add_argument("--toon-size", type=float, default=0.52)
    parser.add_argument("--toon-smooth", type=float, default=0.03)
    parser.add_argument("--replace-material", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args(_script_args())

    objects = selected_mesh_objects()
    if not objects:
        raise RuntimeError("Select at least one visible mesh object before running this script")
    report = apply_to_objects(
        objects,
        width=args.width,
        ray_length=args.ray_length,
        only_local=not args.scene_aware,
        base_color=(*args.base_color, 1.0),
        outline_color=(*args.outline_color, 1.0),
        toon_size=args.toon_size,
        toon_smooth=args.toon_smooth,
        replace_material=args.replace_material,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        output = Path(args.report).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print("BPS_CYCLES_NPR " + json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
