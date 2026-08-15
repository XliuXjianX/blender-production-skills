#!/usr/bin/env python3
"""Build an idempotent Eevee toon material and inverted-hull outline.

Run through Blender's Python environment. The script only targets selected mesh
objects and never resets the scene, World, camera, or unrelated data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import bpy


OWNER = "blender-npr-eevee"
SCHEMA_VERSION = "1.0"
OWNER_PROP = "bps_owner"
ROLE_PROP = "bps_role"

TOON_MATERIAL_NAME = "BPS_NPR_EEVEE_TOON"
OUTLINE_MATERIAL_NAME = "BPS_NPR_EEVEE_OUTLINE"
OUTLINE_GROUP_NAME = "BPS_NPR_EEVEE_INVERTED_HULL"
OUTLINE_MODIFIER_NAME = "BPS_NPR_EEVEE_OUTLINE"


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


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


def _claim_node_group(preferred_name: str, role: str) -> bpy.types.NodeTree:
    for group in bpy.data.node_groups:
        if (
            group.bl_idname == "GeometryNodeTree"
            and group.get(OWNER_PROP) == OWNER
            and group.get(ROLE_PROP) == role
        ):
            return group
    group = bpy.data.node_groups.get(preferred_name)
    if group is not None and (
        group.bl_idname != "GeometryNodeTree" or group.get(OWNER_PROP) != OWNER
    ):
        group = bpy.data.node_groups.new(f"{preferred_name}__BPS", "GeometryNodeTree")
    elif group is None:
        group = bpy.data.node_groups.new(preferred_name, "GeometryNodeTree")
    group[OWNER_PROP] = OWNER
    group[ROLE_PROP] = role
    group["bps_schema_version"] = SCHEMA_VERSION
    return group


def _clear_interface(node_tree: bpy.types.NodeTree) -> None:
    for item in list(node_tree.interface.items_tree):
        node_tree.interface.remove(item)


def _clear_nodes(node_tree: bpy.types.NodeTree) -> None:
    node_tree.nodes.clear()


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


def _shade(color: Sequence[float], factor: float) -> tuple[float, float, float, float]:
    values = list(color[:3])
    return (
        min(max(values[0] * factor, 0.0), 1.0),
        min(max(values[1] * factor, 0.0), 1.0),
        min(max(values[2] * factor, 0.0), 1.0),
        1.0,
    )


def _set_node_location(node: bpy.types.Node, x: float, y: float) -> bpy.types.Node:
    node.location = (x, y)
    return node


def build_toon_material(
    base_color: Sequence[float] = (0.48, 0.07, 0.12, 1.0),
) -> bpy.types.Material:
    """Create or rebuild the owned Eevee toon material."""

    material = _claim_material(TOON_MATERIAL_NAME, "toon_fill")
    material.use_nodes = True
    material.diffuse_color = tuple(base_color)
    tree = material.node_tree
    _clear_nodes(tree)

    output = _set_node_location(tree.nodes.new("ShaderNodeOutputMaterial"), 860, 40)
    output.name = "BPS Material Output"

    emission = _set_node_location(tree.nodes.new("ShaderNodeEmission"), 620, 40)
    emission.name = "BPS Unlit Toon Output"
    emission.inputs["Strength"].default_value = 1.0

    multiply = _set_node_location(tree.nodes.new("ShaderNodeMixRGB"), 380, 40)
    multiply.name = "BPS Palette x Material Variation"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs["Factor"].default_value = 1.0

    palette = _set_node_location(tree.nodes.new("ShaderNodeValToRGB"), 100, 150)
    palette.name = "BPS Constant Toon Palette"
    palette.color_ramp.interpolation = "CONSTANT"
    shadow = palette.color_ramp.elements[0]
    light = palette.color_ramp.elements[1]
    middle = palette.color_ramp.elements.new(0.54)
    shadow.position = 0.30
    middle.position = 0.54
    light.position = 0.76
    shadow.color = _shade(base_color, 0.24)
    middle.color = _shade(base_color, 0.66)
    light.color = _shade(base_color, 1.18)

    shader_to_rgb = _set_node_location(tree.nodes.new("ShaderNodeShaderToRGB"), -160, 150)
    shader_to_rgb.name = "BPS Eevee Shader to RGB"

    diffuse = _set_node_location(tree.nodes.new("ShaderNodeBsdfDiffuse"), -420, 150)
    diffuse.name = "BPS Lighting Probe"
    diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    diffuse.inputs["Roughness"].default_value = 0.25

    variation_ramp = _set_node_location(tree.nodes.new("ShaderNodeValToRGB"), 100, -170)
    variation_ramp.name = "BPS Restrained Material Variation"
    variation_ramp.color_ramp.elements[0].position = 0.28
    variation_ramp.color_ramp.elements[0].color = (0.80, 0.80, 0.80, 1.0)
    variation_ramp.color_ramp.elements[1].position = 0.74
    variation_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    noise = _set_node_location(tree.nodes.new("ShaderNodeTexNoise"), -170, -180)
    noise.name = "BPS Stable Surface Variation"
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.45

    texcoord = _set_node_location(tree.nodes.new("ShaderNodeTexCoord"), -420, -190)
    texcoord.name = "BPS Object Coordinates"

    tree.links.new(diffuse.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    tree.links.new(shader_to_rgb.outputs["Color"], palette.inputs["Factor"])
    tree.links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    tree.links.new(noise.outputs["Factor"], variation_ramp.inputs["Factor"])
    tree.links.new(palette.outputs["Color"], multiply.inputs["Color1"])
    tree.links.new(variation_ramp.outputs["Color"], multiply.inputs["Color2"])
    tree.links.new(multiply.outputs["Color"], emission.inputs["Color"])
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def build_outline_material(
    outline_color: Sequence[float] = (0.005, 0.008, 0.012, 1.0),
) -> bpy.types.Material:
    """Create or rebuild the dark backface-culled Eevee outline material."""

    material = _claim_material(OUTLINE_MATERIAL_NAME, "outline")
    material.use_nodes = True
    material.diffuse_color = tuple(outline_color)
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True

    tree = material.node_tree
    _clear_nodes(tree)
    output = _set_node_location(tree.nodes.new("ShaderNodeOutputMaterial"), 240, 0)
    emission = _set_node_location(tree.nodes.new("ShaderNodeEmission"), 0, 0)
    emission.inputs["Color"].default_value = tuple(outline_color)
    emission.inputs["Strength"].default_value = 1.0
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def build_outline_group(
    outline_material: bpy.types.Material,
    *,
    width: float = 0.025,
    noise_scale: float = 5.0,
    wobble_amount: float = 0.0,
) -> bpy.types.NodeTree:
    """Create or rebuild the production inverted-hull Geometry Nodes group."""

    group = _claim_node_group(OUTLINE_GROUP_NAME, "inverted_hull")
    _clear_nodes(group)
    _clear_interface(group)

    _new_socket(group, "Geometry", "INPUT", "NodeSocketGeometry")
    _new_socket(group, "Enable", "INPUT", "NodeSocketBool", default=True)
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
        "Noise Scale",
        "INPUT",
        "NodeSocketFloat",
        default=noise_scale,
        minimum=0.01,
        maximum=1000.0,
    )
    _new_socket(
        group,
        "Wobble Amount",
        "INPUT",
        "NodeSocketFloat",
        default=wobble_amount,
        minimum=0.0,
        maximum=max(width * 4.0, 0.25),
    )
    _new_socket(
        group,
        "Outline Material",
        "INPUT",
        "NodeSocketMaterial",
        default=outline_material,
    )
    _new_socket(group, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = group.nodes
    links = group.links

    group_input = _set_node_location(nodes.new("NodeGroupInput"), -1100, 60)
    group_input.name = "BPS Outline Controls"
    group_output = _set_node_location(nodes.new("NodeGroupOutput"), 980, 60)
    group_output.name = "BPS Outlined Geometry"

    extrude = _set_node_location(nodes.new("GeometryNodeExtrudeMesh"), -860, 160)
    extrude.name = "BPS Expand Along Evaluated Normals"
    extrude.mode = "FACES"
    extrude.inputs["Selection"].default_value = True
    extrude.inputs["Individual"].default_value = False

    separate = _set_node_location(nodes.new("GeometryNodeSeparateGeometry"), -630, 160)
    separate.name = "BPS Keep Extruded Top Shell"
    separate.domain = "FACE"

    set_position = _set_node_location(nodes.new("GeometryNodeSetPosition"), -170, 170)
    set_position.name = "BPS Optional Hand-Drawn Wobble"

    flip = _set_node_location(nodes.new("GeometryNodeFlipFaces"), 60, 170)
    flip.name = "BPS Flip Outline Faces"

    set_material = _set_node_location(nodes.new("GeometryNodeSetMaterial"), 280, 170)
    set_material.name = "BPS Assign Outline Material"

    join = _set_node_location(nodes.new("GeometryNodeJoinGeometry"), 520, 140)
    join.name = "BPS Join Source And Outline"

    switch = _set_node_location(nodes.new("GeometryNodeSwitch"), 760, 60)
    switch.name = "BPS Outline Enable"
    switch.input_type = "GEOMETRY"

    position = _set_node_location(nodes.new("GeometryNodeInputPosition"), -850, -210)
    position.name = "BPS Spatial Noise Coordinates"
    normal = _set_node_location(nodes.new("GeometryNodeInputNormal"), -400, -310)
    normal.name = "BPS Evaluated Normal"

    noise = _set_node_location(nodes.new("ShaderNodeTexNoise"), -630, -220)
    noise.name = "BPS Position-Driven Wobble"
    noise.noise_dimensions = "3D"
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.5

    center_noise = _set_node_location(nodes.new("ShaderNodeMapRange"), -400, -130)
    center_noise.name = "BPS Center Noise Around Zero"
    center_noise.clamp = True
    center_noise.data_type = "FLOAT"
    center_noise.inputs["From Min"].default_value = 0.0
    center_noise.inputs["From Max"].default_value = 1.0
    center_noise.inputs["To Min"].default_value = -1.0
    center_noise.inputs["To Max"].default_value = 1.0

    wobble_scale = _set_node_location(nodes.new("ShaderNodeMath"), -160, -120)
    wobble_scale.name = "BPS Wobble Amplitude"
    wobble_scale.operation = "MULTIPLY"

    normal_scale = _set_node_location(nodes.new("ShaderNodeVectorMath"), 50, -110)
    normal_scale.name = "BPS Project Wobble Along Normal"
    normal_scale.operation = "SCALE"

    links.new(group_input.outputs["Geometry"], extrude.inputs["Mesh"])
    links.new(group_input.outputs["Width"], extrude.inputs["Offset Scale"])
    links.new(extrude.outputs["Mesh"], separate.inputs["Geometry"])
    links.new(extrude.outputs["Top"], separate.inputs["Selection"])
    links.new(separate.outputs["Selection"], set_position.inputs["Geometry"])

    links.new(position.outputs["Position"], noise.inputs["Vector"])
    links.new(group_input.outputs["Noise Scale"], noise.inputs["Scale"])
    links.new(noise.outputs["Factor"], center_noise.inputs["Value"])
    links.new(center_noise.outputs["Result"], wobble_scale.inputs[0])
    links.new(group_input.outputs["Wobble Amount"], wobble_scale.inputs[1])
    links.new(normal.outputs["Normal"], normal_scale.inputs["Vector"])
    links.new(wobble_scale.outputs[0], normal_scale.inputs["Scale"])
    links.new(normal_scale.outputs["Vector"], set_position.inputs["Offset"])

    links.new(set_position.outputs["Geometry"], flip.inputs["Mesh"])
    links.new(flip.outputs["Mesh"], set_material.inputs["Geometry"])
    links.new(group_input.outputs["Outline Material"], set_material.inputs["Material"])
    links.new(group_input.outputs["Geometry"], join.inputs["Geometry"])
    links.new(set_material.outputs["Geometry"], join.inputs["Geometry"])
    links.new(group_input.outputs["Enable"], switch.inputs["Switch"])
    links.new(group_input.outputs["Geometry"], switch.inputs["False"])
    links.new(join.outputs["Geometry"], switch.inputs["True"])
    links.new(switch.outputs["Output"], group_output.inputs["Geometry"])
    return group


def _interface_input_identifiers(group: bpy.types.NodeTree) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for item in group.interface.items_tree:
        if (
            getattr(item, "item_type", "") == "SOCKET"
            and getattr(item, "in_out", "") == "INPUT"
        ):
            identifiers[item.name] = item.identifier
    return identifiers


def _ensure_outline_modifier(
    obj: bpy.types.Object,
    group: bpy.types.NodeTree,
    *,
    outline_material: bpy.types.Material,
    width: float,
    noise_scale: float,
    wobble_amount: float,
) -> bpy.types.Modifier:
    modifier = next(
        (
            candidate
            for candidate in obj.modifiers
            if (
                candidate.type == "NODES"
                and candidate.node_group is not None
                and candidate.node_group.get(OWNER_PROP) == OWNER
                and candidate.node_group.get(ROLE_PROP) == "inverted_hull"
            )
        ),
        None,
    )
    if modifier is None:
        modifier = obj.modifiers.new(OUTLINE_MODIFIER_NAME, "NODES")
    modifier.node_group = group

    identifiers = _interface_input_identifiers(group)
    values = {
        "Enable": True,
        "Width": float(width),
        "Noise Scale": float(noise_scale),
        "Wobble Amount": float(wobble_amount),
        "Outline Material": outline_material,
    }
    for name, value in values.items():
        identifier = identifiers.get(name)
        if not identifier:
            continue
        interface_input = getattr(modifier.properties.inputs, identifier, None)
        if interface_input is not None and hasattr(interface_input, "value"):
            interface_input.value = value
            continue
        try:
            modifier[identifier] = value
        except TypeError as exc:
            raise RuntimeError(
                f"Unable to set Geometry Nodes input {name!r} ({identifier})"
            ) from exc
    return modifier


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


def _set_eevee_engine() -> str:
    for identifier in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            bpy.context.scene.render.engine = identifier
            return identifier
        except (TypeError, ValueError):
            continue
    raise RuntimeError("Eevee is unavailable in this Blender runtime")


def apply_to_objects(
    objects: Iterable[bpy.types.Object],
    *,
    width: float = 0.025,
    noise_scale: float = 5.0,
    wobble_amount: float = 0.0,
    base_color: Sequence[float] = (0.48, 0.07, 0.12, 1.0),
    outline_color: Sequence[float] = (0.005, 0.008, 0.012, 1.0),
    replace_material: bool = False,
) -> dict[str, Any]:
    """Apply the owned NPR setup to explicit mesh objects."""

    mesh_objects = [obj for obj in objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("No mesh objects were provided")

    _set_eevee_engine()
    toon_material = build_toon_material(base_color)
    outline_material = build_outline_material(outline_color)
    outline_group = build_outline_group(
        outline_material,
        width=width,
        noise_scale=noise_scale,
        wobble_amount=wobble_amount,
    )

    results = []
    for obj in mesh_objects:
        assignment = _assign_material(
            obj,
            toon_material,
            replace_material=replace_material,
        )
        modifier = _ensure_outline_modifier(
            obj,
            outline_group,
            outline_material=outline_material,
            width=width,
            noise_scale=noise_scale,
            wobble_amount=wobble_amount,
        )
        results.append(
            {
                "object": obj.name,
                "material_action": assignment,
                "outline_modifier": modifier.name,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "render_engine": bpy.context.scene.render.engine,
        "objects": results,
        "toon_material": toon_material.name,
        "outline_material": outline_material.name,
        "outline_group": outline_group.name,
        "outline_width": width,
        "noise_scale": noise_scale,
        "wobble_amount": wobble_amount,
        "replace_material": replace_material,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=float, default=0.025)
    parser.add_argument("--noise-scale", type=float, default=5.0)
    parser.add_argument("--wobble", type=float, default=0.0)
    parser.add_argument("--base-color", type=float, nargs=3, default=(0.48, 0.07, 0.12))
    parser.add_argument("--outline-color", type=float, nargs=3, default=(0.005, 0.008, 0.012))
    parser.add_argument("--replace-material", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args(_script_args())

    objects = selected_mesh_objects()
    if not objects:
        raise RuntimeError("Select at least one visible mesh object before running this script")
    report = apply_to_objects(
        objects,
        width=args.width,
        noise_scale=args.noise_scale,
        wobble_amount=args.wobble,
        base_color=(*args.base_color, 1.0),
        outline_color=(*args.outline_color, 1.0),
        replace_material=args.replace_material,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        output = Path(args.report).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print("BPS_EEVEE_NPR " + json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
