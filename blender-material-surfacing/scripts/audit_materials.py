#!/usr/bin/env python3
"""Audit Blender materials for production mapping and physical-response evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import bpy


NON_COLOR_TARGETS = {
    "roughness",
    "metallic",
    "normal",
    "height",
    "distance",
    "strength",
    "scale",
    "displacement",
}


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _socket(node: bpy.types.Node, names: Iterable[str]) -> bpy.types.NodeSocket | None:
    wanted = {name.lower() for name in names}
    return next((socket for socket in node.inputs if socket.name.lower() in wanted), None)


def _float_socket(node: bpy.types.Node, names: Iterable[str], fallback: float = 0.0) -> tuple[float, bool]:
    socket = _socket(node, names)
    if socket is None:
        return fallback, False
    try:
        return float(socket.default_value), bool(socket.is_linked)
    except (TypeError, ValueError):
        return fallback, bool(socket.is_linked)


def _material_class(material: bpy.types.Material) -> str:
    explicit = str(material.get("production_material_class", "")).strip().lower()
    if explicit:
        return explicit
    name = material.name.lower()
    for material_class, terms in {
        "metal": ("metal", "steel", "iron", "aluminum", "aluminium", "brass", "铜", "铁", "钢"),
        "wood": ("wood", "timber", "plank", "board", "木", "板"),
        "liquid": ("water", "liquid", "水", "液体"),
    }.items():
        if any(term in name for term in terms):
            return material_class
    return "generic"


def _direct_image_roles(node: bpy.types.Node) -> list[str]:
    roles: list[str] = []
    for output in node.outputs:
        for link in output.links:
            roles.append(f"{link.to_node.bl_idname}:{link.to_socket.name}")
    return sorted(set(roles))


def _expects_non_color(roles: list[str]) -> bool:
    for role in roles:
        lowered = role.lower()
        if any(target in lowered for target in NON_COLOR_TARGETS):
            return True
        if "shadernodenormalmap" in lowered or "shadernodebump" in lowered:
            return True
    return False


def _material_users(material: bpy.types.Material) -> list[bpy.types.Object]:
    users: list[bpy.types.Object] = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if any(slot.material == material for slot in obj.material_slots):
            users.append(obj)
    return users


def audit_material(material: bpy.types.Material) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    material_class = _material_class(material)
    users = _material_users(material)
    evidence: dict[str, Any] = {
        "name": material.name,
        "class": material_class,
        "users": [obj.name for obj in users],
        "texture_scale_m": material.get("production_texture_scale_m"),
        "hero": bool(material.get("production_hero", False)),
    }

    if material.node_tree is None:
        failures.append("node_material_required")
        return {"status": "FAIL", "failures": failures, "warnings": warnings, "evidence": evidence}

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    outputs = [node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial"]
    active_output = next((node for node in outputs if getattr(node, "is_active_output", False)), None)
    if active_output is None and outputs:
        active_output = outputs[0]
    if active_output is None:
        failures.append("material_output_missing")
        return {"status": "FAIL", "failures": failures, "warnings": warnings, "evidence": evidence}

    output_links = {
        socket.name: any(link.to_node == active_output and link.to_socket == socket for link in links)
        for socket in active_output.inputs
    }
    evidence["output_links"] = output_links
    if not output_links.get("Surface", False):
        failures.append("surface_output_unlinked")

    principled: list[dict[str, Any]] = []
    for node in nodes:
        if node.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        metallic, metallic_linked = _float_socket(node, ["Metallic"])
        roughness, roughness_linked = _float_socket(node, ["Roughness"], 0.5)
        ior, ior_linked = _float_socket(node, ["IOR"], 1.5)
        transmission, transmission_linked = _float_socket(node, ["Transmission Weight", "Transmission"])
        anisotropy, anisotropy_linked = _float_socket(
            node,
            ["Anisotropic IOR Level", "Anisotropic", "Anisotropy"],
        )
        tangent = _socket(node, ["Tangent"])
        principled.append(
            {
                "name": node.name,
                "metallic": metallic,
                "metallic_linked": metallic_linked,
                "roughness": roughness,
                "roughness_linked": roughness_linked,
                "ior": ior,
                "ior_linked": ior_linked,
                "transmission": transmission,
                "transmission_linked": transmission_linked,
                "anisotropy": anisotropy,
                "anisotropy_linked": anisotropy_linked,
                "tangent_linked": bool(tangent and tangent.is_linked),
            }
        )
    evidence["principled"] = principled
    if not principled:
        warnings.append("principled_not_found_review_custom_shader")

    image_nodes: list[dict[str, Any]] = []
    bad_color_spaces: list[str] = []
    for node in nodes:
        if node.bl_idname != "ShaderNodeTexImage":
            continue
        roles = _direct_image_roles(node)
        color_space = node.image.colorspace_settings.name if node.image else None
        image_nodes.append(
            {
                "node": node.name,
                "image": node.image.filepath if node.image else None,
                "color_space": color_space,
                "roles": roles,
            }
        )
        if color_space and _expects_non_color(roles) and color_space.lower() not in {"non-color", "raw"}:
            bad_color_spaces.append(node.name)
    evidence["image_textures"] = image_nodes
    if bad_color_spaces:
        failures.append("non_color_map_color_space")
        evidence["bad_color_space_nodes"] = bad_color_spaces

    mapping_nodes = [
        node.name
        for node in nodes
        if node.bl_idname in {"ShaderNodeTexCoord", "ShaderNodeUVMap", "ShaderNodeMapping", "ShaderNodeTangent"}
    ]
    evidence["mapping_nodes"] = mapping_nodes
    uv_users = {
        obj.name: [layer.name for layer in obj.data.uv_layers]
        for obj in users
        if obj.type == "MESH"
    }
    evidence["uv_layers"] = uv_users

    normal_nodes = [node.name for node in nodes if node.bl_idname in {"ShaderNodeNormalMap", "ShaderNodeBump"}]
    displacement_nodes = [node.name for node in nodes if node.bl_idname == "ShaderNodeDisplacement"]
    evidence["normal_or_bump_nodes"] = normal_nodes
    evidence["displacement_nodes"] = displacement_nodes

    if material.get("production_texture_scale_m") is None:
        warnings.append("physical_texture_scale_not_recorded")

    if material_class == "metal":
        variant = str(material.get("production_surface_variant", "bare")).lower()
        evidence["surface_variant"] = variant
        bare_metal_evidence = any(item["metallic_linked"] or item["metallic"] >= 0.8 for item in principled)
        if variant in {"bare", "brushed", "machined", "cast", "galvanized"} and not bare_metal_evidence:
            failures.append("bare_metal_conductor_response_missing")
        if any(item["anisotropy"] > 0.05 or item["anisotropy_linked"] for item in principled):
            if not any(item["tangent_linked"] for item in principled):
                warnings.append("anisotropy_without_explicit_tangent")

    if material_class == "wood":
        if users and not any(uv_users.values()):
            failures.append("wood_uv_missing")
        if not mapping_nodes and image_nodes:
            warnings.append("wood_directional_mapping_not_explicit")
        if not any(item["roughness_linked"] for item in principled):
            warnings.append("wood_roughness_not_varied")
        if evidence["hero"] and not normal_nodes and not displacement_nodes:
            warnings.append("hero_wood_surface_relief_missing")

    if material_class in {"liquid", "water"}:
        plausible_surface = any(
            (item["transmission_linked"] or item["transmission"] >= 0.5)
            and (item["ior_linked"] or 1.30 <= item["ior"] <= 1.36)
            and item["roughness"] <= 0.3
            for item in principled
        )
        if not plausible_surface:
            failures.append("water_surface_response_implausible")
        if bool(material.get("production_require_volume_absorption", True)) and not output_links.get("Volume", False):
            failures.append("water_volume_absorption_unlinked")

    status = "FAIL" if failures else "WARN" if warnings else "PASS"
    return {"status": status, "failures": failures, "warnings": warnings, "evidence": evidence}


def _new_principled_material(name: str, material_class: str) -> tuple[bpy.types.Material, bpy.types.Node]:
    material = bpy.data.materials.new(name)
    material["production_material_class"] = material_class
    material["production_texture_scale_m"] = 0.25
    node = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    return material, node


def _assign_test_cube(name: str, material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def _set_socket(node: bpy.types.Node, names: Iterable[str], value: float) -> None:
    socket = _socket(node, names)
    if socket is not None:
        socket.default_value = value


def _build_self_test() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    metal, metal_bsdf = _new_principled_material("TEST_BareMetal", "metal")
    metal["production_surface_variant"] = "bare"
    _set_socket(metal_bsdf, ["Metallic"], 1.0)
    _set_socket(metal_bsdf, ["Roughness"], 0.22)
    _assign_test_cube("TEST_Metal", metal)

    wood, wood_bsdf = _new_principled_material("TEST_Wood", "wood")
    wood["production_hero"] = True
    nodes = wood.node_tree.nodes
    links = wood.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    color_noise = nodes.new("ShaderNodeTexNoise")
    rough_noise = nodes.new("ShaderNodeTexNoise")
    bump = nodes.new("ShaderNodeBump")
    links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], color_noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], rough_noise.inputs["Vector"])
    links.new(color_noise.outputs["Color"], wood_bsdf.inputs["Base Color"])
    links.new(rough_noise.outputs["Fac"], wood_bsdf.inputs["Roughness"])
    links.new(color_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], wood_bsdf.inputs["Normal"])
    _assign_test_cube("TEST_Wood", wood)

    water, water_bsdf = _new_principled_material("TEST_Water", "liquid")
    water["production_require_volume_absorption"] = True
    _set_socket(water_bsdf, ["Transmission Weight", "Transmission"], 1.0)
    _set_socket(water_bsdf, ["IOR"], 1.333)
    _set_socket(water_bsdf, ["Roughness"], 0.05)
    absorption = water.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    output = next(node for node in water.node_tree.nodes if node.bl_idname == "ShaderNodeOutputMaterial")
    water.node_tree.links.new(absorption.outputs["Volume"], output.inputs["Volume"])
    _assign_test_cube("TEST_Water", water)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--materials", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(_script_args())

    if args.self_test:
        _build_self_test()

    requested = {name.strip() for name in args.materials.split(",") if name.strip()}
    if args.self_test and not requested:
        requested = {"TEST_BareMetal", "TEST_Wood", "TEST_Water"}
    materials = [material for material in bpy.data.materials if not requested or material.name in requested]
    results = [audit_material(material) for material in materials]
    failed = [result for result in results if result["status"] == "FAIL"]
    warnings = [result for result in results if result["status"] == "WARN"]
    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "status": "FAIL" if failed else "WARN" if warnings else "PASS",
        "materials": results,
        "summary": {"total": len(results), "failed": len(failed), "warnings": len(warnings)},
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(output), "status": report["status"], **report["summary"]}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
