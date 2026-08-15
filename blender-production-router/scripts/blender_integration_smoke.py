#!/usr/bin/env python3
"""Create an isolated in-memory test scene and verify core Blender systems."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Callable

import bpy


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _active(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _mesh_object(name: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _test_modifier(modifier_type: str) -> dict[str, Any]:
    obj = _mesh_object(f"TEST-{modifier_type}")
    modifier = obj.modifiers.new(f"TEST-{modifier_type}", modifier_type)
    return {"object": obj.name, "modifier": modifier.name, "type": modifier.type}


def _test_rigid_body() -> dict[str, Any]:
    obj = _mesh_object("TEST-RIGID-BODY")
    _active(obj)
    bpy.ops.rigidbody.object_add()
    return {
        "object": obj.name,
        "type": obj.rigid_body.type if obj.rigid_body else None,
    }


def _enum_ids(owner: Any, property_name: str) -> list[str]:
    return [item.identifier for item in owner.bl_rna.properties[property_name].enum_items]


def _test_boolean_solvers() -> dict[str, Any]:
    obj = _mesh_object("TEST-BOOLEAN-SOLVERS")
    modifier = obj.modifiers.new("TEST-BOOLEAN-SOLVERS", "BOOLEAN")
    solvers = _enum_ids(modifier, "solver")
    if "EXACT" not in solvers or not ({"FLOAT", "FAST"} & set(solvers)):
        raise RuntimeError(f"Unexpected Boolean solver enum: {solvers}")
    return {"object": obj.name, "solvers": solvers}


def _test_cloth_settings() -> dict[str, Any]:
    obj = _mesh_object("TEST-CLOTH-SETTINGS")
    modifier = obj.modifiers.new("TEST-CLOTH-SETTINGS", "CLOTH")
    settings = {prop.identifier for prop in modifier.settings.bl_rna.properties}
    collision = {prop.identifier for prop in modifier.collision_settings.bl_rna.properties}
    required_settings = {
        "quality",
        "mass",
        "tension_stiffness",
        "compression_stiffness",
        "shear_stiffness",
        "bending_stiffness",
        "vertex_group_mass",
        "use_sewing_springs",
        "sewing_force_max",
        "use_pressure",
    }
    required_collision = {
        "collision_quality",
        "distance_min",
        "use_collision",
        "use_self_collision",
        "self_distance_min",
    }
    missing = sorted((required_settings - settings) | (required_collision - collision))
    if missing:
        raise RuntimeError(f"Missing Cloth RNA properties: {missing}")
    return {
        "object": obj.name,
        "settings": sorted(required_settings),
        "collision_settings": sorted(required_collision),
    }


def _test_fluid_roles() -> dict[str, Any]:
    obj = _mesh_object("TEST-FLUID-ROLES")
    modifier = obj.modifiers.new("TEST-FLUID-ROLES", "FLUID")
    roles = _enum_ids(modifier, "fluid_type")
    required = {"DOMAIN", "FLOW", "EFFECTOR"}
    if not required.issubset(roles):
        raise RuntimeError(f"Missing Fluid roles: {sorted(required - set(roles))}")
    return {"object": obj.name, "roles": roles}


def _test_material_nodes() -> dict[str, Any]:
    material = bpy.data.materials.new("TEST-MATERIAL-NODES")
    tree = material.node_tree
    required_types = [
        "ShaderNodeBsdfPrincipled",
        "ShaderNodeTexCoord",
        "ShaderNodeTangent",
        "ShaderNodeBump",
        "ShaderNodeDisplacement",
        "ShaderNodeVolumeAbsorption",
    ]
    existing = {node.bl_idname for node in tree.nodes}
    created: list[str] = []
    for node_type in required_types:
        if node_type not in existing:
            tree.nodes.new(node_type)
        created.append(node_type)
    if not all(hasattr(bpy.types, node_type) for node_type in required_types):
        raise RuntimeError("Required production material node type is unavailable")
    return {"material": material.name, "node_types": created}


def _test_constraint() -> dict[str, Any]:
    obj = _mesh_object("TEST-CONSTRAINT")
    constraint = obj.constraints.new("LIMIT_ROTATION")
    return {"object": obj.name, "constraint": constraint.type}


def _test_geometry_nodes() -> dict[str, Any]:
    obj = _mesh_object("TEST-GEOMETRY-NODES")
    group = bpy.data.node_groups.new("TEST-GEOMETRY-NODES", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    group_input = group.nodes.new("NodeGroupInput")
    group_output = group.nodes.new("NodeGroupOutput")
    group.links.new(group_input.outputs["Geometry"], group_output.inputs["Geometry"])
    modifier = obj.modifiers.new("TEST-GEOMETRY-NODES", "NODES")
    modifier.node_group = group
    return {
        "object": obj.name,
        "modifier": modifier.type,
        "node_count": len(group.nodes),
        "simulation_zone_types_available": all(
            hasattr(bpy.types, name)
            for name in ("GeometryNodeSimulationInput", "GeometryNodeSimulationOutput")
        ),
    }


def _run(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        evidence = fn()
        return {"id": name, "status": "PASS", "evidence": evidence}
    except Exception as exc:
        return {"id": name, "status": "FAIL", "error": repr(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    tests: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("bevel", lambda: _test_modifier("BEVEL")),
        ("boolean", lambda: _test_modifier("BOOLEAN")),
        ("boolean_solvers", _test_boolean_solvers),
        ("subdivision", lambda: _test_modifier("SUBSURF")),
        ("simple_deform", lambda: _test_modifier("SIMPLE_DEFORM")),
        ("curve_deform", lambda: _test_modifier("CURVE")),
        ("lattice", lambda: _test_modifier("LATTICE")),
        ("shrinkwrap", lambda: _test_modifier("SHRINKWRAP")),
        ("cloth", lambda: _test_modifier("CLOTH")),
        ("cloth_settings", _test_cloth_settings),
        ("soft_body", lambda: _test_modifier("SOFT_BODY")),
        ("fluid", lambda: _test_modifier("FLUID")),
        ("fluid_roles", _test_fluid_roles),
        ("dynamic_paint", lambda: _test_modifier("DYNAMIC_PAINT")),
        ("ocean", lambda: _test_modifier("OCEAN")),
        ("wave", lambda: _test_modifier("WAVE")),
        ("array", lambda: _test_modifier("ARRAY")),
        ("rigid_body", _test_rigid_body),
        ("object_constraint", _test_constraint),
        ("geometry_nodes", _test_geometry_nodes),
        ("material_nodes", _test_material_nodes),
    ]
    results = [_run(name, fn) for name, fn in tests]
    failed = [result for result in results if result["status"] == "FAIL"]
    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "status": "PASS" if not failed else "FAIL",
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "BLENDER_INTEGRATION_SMOKE "
        + json.dumps(
            {
                "output": str(output),
                "status": report["status"],
                "passed": report["passed"],
                "failed": report["failed"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
