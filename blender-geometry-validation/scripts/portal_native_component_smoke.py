#!/usr/bin/env python3
"""Validate the portal case without touching a visible Blender project."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import bpy


DEFAULT_PORTAL_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "blender-procedural-systems"
    / "scripts"
    / "blender_forced_perspective_portal_case.py"
)


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("portal_native_case", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sentinel() -> bpy.types.Object:
    mesh = bpy.data.meshes.new("USER_SENTINEL_MESH")
    mesh.from_pydata(
        [(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    obj = bpy.data.objects.new("USER_SENTINEL", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def _evaluated_bounds(obj: bpy.types.Object) -> dict[str, float]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        coords = [vertex.co for vertex in mesh.vertices]
        return {
            "x": max(item.x for item in coords) - min(item.x for item in coords),
            "y": max(item.y for item in coords) - min(item.y for item in coords),
            "z": max(item.z for item in coords) - min(item.z for item in coords),
            "vertices": len(coords),
        }
    finally:
        evaluated.to_mesh_clear()


def _run_test(portal_path: Path) -> tuple[dict[str, bool], dict[str, Any]]:
    portal = _load(portal_path)
    sentinel = _sentinel()
    portal.SETTINGS.update(
        {
            "add_preview_materials": True,
            "add_preview_light": True,
            "distant_instances": [
                {"name": "PORTAL_FAR_A", "location": (6.0, 18.0, 0.0), "scale": 0.45},
                {"name": "PORTAL_FAR_B", "location": (-8.0, 28.0, 0.0), "scale": 0.30},
            ],
        }
    )
    first = portal.build_portal()
    production = bpy.data.collections[portal.SETTINGS["collection_name"]]
    preview = bpy.data.collections[portal.SETTINGS["preview_collection_name"]]
    instance_collection = bpy.data.collections[portal.SETTINGS["instance_collection_name"]]
    first_names = sorted(item.name for item in production.objects)
    first_count = len(first_names)

    second = portal.build_portal()
    production = bpy.data.collections[portal.SETTINGS["collection_name"]]
    second_names = sorted(item.name for item in production.objects)
    stairs = bpy.data.objects.get("PORTAL_STAIR_SOURCE")
    frame = bpy.data.objects.get("PORTAL_FRAME_HOST")
    array = stairs.modifiers.get("PORTAL_STAIR_ARRAY") if stairs else None
    boolean = frame.modifiers.get("PORTAL_OPENING_BOOLEAN") if frame else None

    before = _evaluated_bounds(stairs)
    original_count = int(array.count)
    original_offset = tuple(array.constant_offset_displace)
    array.count = original_count + 3
    array.constant_offset_displace = (
        original_offset[0],
        original_offset[1] * 1.1,
        original_offset[2] * 0.9,
    )
    bpy.context.view_layer.update()
    after = _evaluated_bounds(stairs)

    instances = list(instance_collection.objects)
    production_lights = [item.name for item in production.objects if item.type == "LIGHT"]
    preview_lights = [item.name for item in preview.objects if item.type == "LIGHT"]
    manual_steps = [
        item.name
        for item in bpy.data.objects
        if item.name.startswith("PORTAL_STAIR_STEP")
    ]

    before_conflict_count = len(production.objects)
    conflict_collection = bpy.data.collections.new("USER_PORTAL_CONFLICT")
    bpy.context.scene.collection.children.link(conflict_collection)
    original_collection_name = portal.SETTINGS["collection_name"]
    portal.SETTINGS["collection_name"] = conflict_collection.name
    collection_conflict_refused = False
    try:
        portal.build_portal()
    except RuntimeError:
        collection_conflict_refused = True
    finally:
        portal.SETTINGS["collection_name"] = original_collection_name

    stone = bpy.data.materials.get("MAT_Portal_Stone")
    for obj in production.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
    if stone is not None:
        bpy.data.materials.remove(stone)
    bpy.data.materials.new("MAT_Portal_Stone")
    material_conflict_refused = False
    try:
        portal.build_portal()
    except RuntimeError:
        material_conflict_refused = True

    checks = {
        "first_build_passed": first.get("status") == "PASS",
        "second_build_passed": second.get("status") == "PASS",
        "rerun_object_names_stable": first_names == second_names and first_count == len(second_names),
        "sentinel_survives": bpy.data.objects.get(sentinel.name) is sentinel,
        "selection_and_active_preserved": bpy.context.view_layer.objects.active is sentinel and sentinel.select_get(),
        "boolean_frame_exists": boolean is not None and boolean.type == "BOOLEAN" and boolean.object is not None,
        "single_array_source": stairs is not None and array is not None and array.type == "ARRAY",
        "array_owns_count_and_rise_run": (
            array is not None
            and original_count == int(portal.SETTINGS["step_count"])
            and math.isclose(original_offset[1], float(portal.SETTINGS["step_run"]), rel_tol=1e-6)
            and math.isclose(original_offset[2], float(portal.SETTINGS["step_rise"]), rel_tol=1e-6)
        ),
        "array_edit_updates_evaluated_flight": after["y"] > before["y"] and after["vertices"] > before["vertices"],
        "no_manual_step_objects": not manual_steps,
        "object_offset_taper_retained": array is not None and array.use_object_offset and array.offset_object is not None,
        "preview_light_not_instanced": not production_lights and bool(preview_lights),
        "distant_portals_are_collection_instances": (
            len(instances) == 2
            and all(item.instance_type == "COLLECTION" for item in instances)
            and all(item.instance_collection is production for item in instances)
        ),
        "unowned_collection_conflict_refused": collection_conflict_refused,
        "unowned_material_conflict_refused": material_conflict_refused,
        "conflicts_do_not_clear_owned_geometry": len(production.objects) == before_conflict_count,
    }
    evidence = {
        "first": first,
        "second": second,
        "evaluated_before": before,
        "evaluated_after": after,
        "production_objects": second_names,
        "preview_lights": preview_lights,
        "instances": [item.name for item in instances],
    }
    return checks, evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portal-script", default=str(DEFAULT_PORTAL_SCRIPT))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    portal_path = Path(args.portal_script).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    checks, evidence = _run_test(portal_path)
    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "evidence": evidence,
    }
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("PORTAL_NATIVE_COMPONENT_SMOKE " + json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
