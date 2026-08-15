#!/usr/bin/env python3
"""Build and verify native construction-method fixtures in isolated Blender."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import bpy
from mathutils import Vector


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _box(
    name: str,
    dimensions: tuple[float, float, float],
    location: tuple[float, float, float],
) -> bpy.types.Object:
    hx, hy, hz = (value * 0.5 for value in dimensions)
    vertices = [
        (-hx, -hy, -hz),
        (hx, -hy, -hz),
        (hx, hy, -hz),
        (-hx, hy, -hz),
        (-hx, -hy, hz),
        (hx, -hy, hz),
        (hx, hy, hz),
        (-hx, hy, hz),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(f"{name}-MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def _evaluated_mesh_stats(obj: bpy.types.Object) -> dict[str, Any]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        coordinates = [vertex.co.copy() for vertex in mesh.vertices]
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "min": [min(co[index] for co in coordinates) for index in range(3)],
            "max": [max(co[index] for co in coordinates) for index in range(3)],
        }
    finally:
        evaluated.to_mesh_clear()


def _test_architectural_opening() -> dict[str, Any]:
    wall = _box("WALL-HOST", (6.0, 0.4, 3.0), (0.0, 0.0, 1.5))
    cutter = _box("CUT-DOORWAY", (1.2, 0.8, 2.3), (0.0, 0.0, 1.05))
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    modifier = wall.modifiers.new("BOOL-DOORWAY", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.operand_type = "OBJECT"
    modifier.object = cutter
    modifier.solver = "EXACT"
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = wall.evaluated_get(depsgraph)
    opening_hit, *_ = evaluated.ray_cast(
        Vector((0.0, -2.0, -0.5)), Vector((0.0, 1.0, 0.0))
    )
    solid_hit, *_ = evaluated.ray_cast(
        Vector((2.0, -2.0, -0.5)), Vector((0.0, 1.0, 0.0))
    )
    stats = _evaluated_mesh_stats(wall)
    if opening_hit or not solid_hit or stats["faces"] <= 6:
        raise RuntimeError(
            f"Boolean doorway did not evaluate as a through opening: {stats}"
        )
    return {
        "host": wall.name,
        "cutter": cutter.name,
        "modifier": modifier.type,
        "operation": modifier.operation,
        "solver": modifier.solver,
        "opening_ray_clear": not opening_hit,
        "solid_wall_ray_hits": solid_hit,
        "evaluated": stats,
    }


def _test_stair_array() -> dict[str, Any]:
    step = _box("STAIR-STEP-SOURCE", (1.2, 0.32, 0.18), (0.0, 0.0, 0.09))
    modifier = step.modifiers.new("ARRAY-STAIR-FLIGHT", "ARRAY")
    modifier.count = 7
    modifier.use_relative_offset = False
    modifier.use_constant_offset = True
    modifier.constant_offset_displace = (0.0, 0.30, 0.18)
    bpy.context.view_layer.update()
    stats = _evaluated_mesh_stats(step)
    y_extent = stats["max"][1] - stats["min"][1]
    z_extent = stats["max"][2] - stats["min"][2]
    expected_y = 0.32 + 0.30 * (modifier.count - 1)
    expected_z = 0.18 + 0.18 * (modifier.count - 1)
    if not math.isclose(y_extent, expected_y, abs_tol=1e-5):
        raise RuntimeError(f"Unexpected stair run extent: {y_extent} != {expected_y}")
    if not math.isclose(z_extent, expected_z, abs_tol=1e-5):
        raise RuntimeError(f"Unexpected stair rise extent: {z_extent} != {expected_z}")
    return {
        "source": step.name,
        "modifier": modifier.type,
        "count": modifier.count,
        "constant_offset": list(modifier.constant_offset_displace),
        "run_extent": y_extent,
        "rise_extent": z_extent,
        "evaluated": stats,
    }


def _test_curve_profile() -> dict[str, Any]:
    profile_data = bpy.data.curves.new("PROFILE-RAIL-DATA", type="CURVE")
    profile_data.dimensions = "2D"
    profile_spline = profile_data.splines.new("POLY")
    profile_spline.points.add(3)
    for point, coordinate in zip(
        profile_spline.points,
        [
            (-0.05, -0.035, 0.0, 1.0),
            (0.05, -0.035, 0.0, 1.0),
            (0.05, 0.035, 0.0, 1.0),
            (-0.05, 0.035, 0.0, 1.0),
        ],
    ):
        point.co = coordinate
    profile_spline.use_cyclic_u = True
    profile = bpy.data.objects.new("PROFILE-RAIL", profile_data)
    bpy.context.scene.collection.objects.link(profile)
    profile.hide_render = True

    path_data = bpy.data.curves.new("PATH-BEZIER-RAIL-DATA", type="CURVE")
    path_data.dimensions = "3D"
    path_data.resolution_u = 12
    path_data.render_resolution_u = 16
    path_data.bevel_mode = "OBJECT"
    path_data.bevel_object = profile
    path_data.use_fill_caps = True
    spline = path_data.splines.new("BEZIER")
    spline.bezier_points.add(3)
    coordinates = [
        (0.0, 0.0, 0.0),
        (1.0, 0.3, 0.2),
        (1.8, 1.2, 0.5),
        (2.2, 2.2, 0.8),
    ]
    for point, coordinate in zip(spline.bezier_points, coordinates):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    path = bpy.data.objects.new("PATH-BEZIER-RAIL", path_data)
    bpy.context.scene.collection.objects.link(path)
    bpy.context.view_layer.update()
    stats = _evaluated_mesh_stats(path)
    if stats["vertices"] <= 8 or stats["faces"] <= 4:
        raise RuntimeError(f"Bezier profile did not evaluate to usable mesh geometry: {stats}")
    if path_data.bevel_object != profile or spline.type != "BEZIER":
        raise RuntimeError("Curve profile ownership was not preserved")
    return {
        "path": path.name,
        "path_type": spline.type,
        "control_points": len(spline.bezier_points),
        "profile": profile.name,
        "bevel_mode": path_data.bevel_mode,
        "evaluated": stats,
    }


def _test_precision_face_placement() -> dict[str, Any]:
    target = _box("SNAP-TARGET", (2.0, 2.0, 0.2), (0.0, 0.0, 0.0))
    source = _box("SNAP-SOURCE", (0.5, 0.5, 0.1), (0.0, 0.0, 2.0))
    tool_settings = bpy.context.scene.tool_settings
    snap_enum = {
        item.identifier
        for item in tool_settings.bl_rna.properties["snap_elements"].enum_items
    }
    if "FACE" not in snap_enum:
        raise RuntimeError(f"FACE snapping is unavailable: {sorted(snap_enum)}")
    tool_settings.use_snap = True
    tool_settings.snap_elements = {"FACE"}
    if hasattr(tool_settings, "use_snap_align_rotation"):
        tool_settings.use_snap_align_rotation = True

    hit, location, normal, _index = target.ray_cast(
        Vector((0.0, 0.0, 2.0)), Vector((0.0, 0.0, -1.0))
    )
    if not hit:
        raise RuntimeError("Declared snap target face could not be resolved")
    offset = 0.02
    half_height = 0.05
    world_location = target.matrix_world @ location
    world_normal = (target.matrix_world.to_3x3() @ normal).normalized()
    source.location = world_location + world_normal * (half_height + offset)
    bpy.context.view_layer.update()
    target_top = 0.1
    source_bottom = source.location.z - half_height
    measured_gap = source_bottom - target_top
    if not math.isclose(measured_gap, offset, abs_tol=1e-6):
        raise RuntimeError(f"Snapped placement gap mismatch: {measured_gap} != {offset}")
    return {
        "source": source.name,
        "target": target.name,
        "snap_elements": sorted(tool_settings.snap_elements),
        "align_rotation": getattr(tool_settings, "use_snap_align_rotation", None),
        "measured_gap": measured_gap,
        "target_normal": list(world_normal),
    }


def _grid(name: str, count: int, spacing: float) -> bpy.types.Object:
    half = (count - 1) * spacing * 0.5
    vertices = [
        (x * spacing - half, y * spacing - half, 0.0)
        for y in range(count)
        for x in range(count)
    ]
    faces = []
    for y in range(count - 1):
        for x in range(count - 1):
            a = y * count + x
            faces.append((a, a + 1, a + count + 1, a + count))
    mesh = bpy.data.meshes.new(f"{name}-MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _test_displace_surface() -> dict[str, Any]:
    surface = _grid("DISPLACE-SURFACE", count=11, spacing=0.2)
    coordinate_object = bpy.data.objects.new("DISPLACE-COORDINATES", None)
    coordinate_object.location = (-0.35, 0.2, 0.0)
    bpy.context.scene.collection.objects.link(coordinate_object)
    subdivision = surface.modifiers.new("SUBDIVIDE-FOR-DISPLACE", "SUBSURF")
    subdivision.subdivision_type = "SIMPLE"
    subdivision.levels = 1
    texture = bpy.data.textures.new("TEX-DISPLACE-RELIEF", type="CLOUDS")
    texture.noise_scale = 0.35
    modifier = surface.modifiers.new("DISPLACE-RELIEF", "DISPLACE")
    modifier.texture = texture
    modifier.texture_coords = "OBJECT"
    modifier.texture_coords_object = coordinate_object
    modifier.direction = "Z"
    modifier.mid_level = 0.5
    modifier.strength = 0.25
    bpy.context.view_layer.update()
    stats = _evaluated_mesh_stats(surface)
    z_range = stats["max"][2] - stats["min"][2]
    stack = [item.type for item in surface.modifiers]
    if stack != ["SUBSURF", "DISPLACE"]:
        raise RuntimeError(f"Unexpected Displace stack: {stack}")
    if stats["vertices"] <= len(surface.data.vertices) or z_range <= 0.01:
        raise RuntimeError(f"Displace did not create evaluated geometric relief: {stats}")
    return {
        "surface": surface.name,
        "stack": stack,
        "source_vertices": len(surface.data.vertices),
        "evaluated_vertices": stats["vertices"],
        "texture": texture.name,
        "texture_coords": modifier.texture_coords,
        "coordinate_object": coordinate_object.name,
        "direction": modifier.direction,
        "midlevel": modifier.mid_level,
        "strength": modifier.strength,
        "z_range": z_range,
    }


def _run(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return {"id": name, "status": "PASS", "evidence": fn()}
    except Exception as exc:
        return {"id": name, "status": "FAIL", "error": repr(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    tests: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("architectural_opening_boolean", _test_architectural_opening),
        ("stair_array_rise_run", _test_stair_array),
        ("bezier_curve_profile", _test_curve_profile),
        ("precision_face_placement", _test_precision_face_placement),
        ("subdivision_displace", _test_displace_surface),
    ]
    results = [_run(name, function) for name, function in tests]
    failed = [result for result in results if result["status"] == "FAIL"]
    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "factory_startup_fixture": True,
        "status": "PASS" if not failed else "FAIL",
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("CONSTRUCTION_METHOD_INTEGRATION " + json.dumps(report, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
