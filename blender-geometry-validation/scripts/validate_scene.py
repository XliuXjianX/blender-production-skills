#!/usr/bin/env python3
"""Validate Blender geometry, relationships, and protected scene state."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


RELATIONSHIP_TYPES = {
    "continuous_surface",
    "boolean_fused",
    "mechanical_seam",
    "embedded_component",
    "constraint_connection",
    "physical_contact",
    "instanced_element",
    "intentionally_independent",
}
MODELING_STAGES = [
    "analysis",
    "blockout",
    "topology_construction",
    "structural_forms",
    "transition_forms",
    "functional_parts",
    "surface_details",
    "systems",
    "surfacing",
    "lighting",
    "final",
]
BUILDABLE_ROLES = {
    "primary_form",
    "structural_part",
    "functional_detail",
    "decorative_detail",
    "cutter",
}


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _check(check_id: str, status: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"id": check_id, "status": status, "evidence": evidence}


def _bbox_diagonal(obj: bpy.types.Object) -> float:
    return max(float(obj.dimensions.length), 1e-9)


def _part_object_name(part: dict[str, Any]) -> str:
    for key in ("object", "final_object_name"):
        value = part.get(key)
        if isinstance(value, str) and value and value != "unresolved":
            return value
    return str(part.get("id", ""))


def _evaluated_mesh_summary(
    obj: bpy.types.Object,
    depsgraph: bpy.types.Depsgraph,
) -> dict[str, Any]:
    evaluated = obj.evaluated_get(depsgraph)
    mesh = None
    bm = bmesh.new()
    try:
        mesh = evaluated.to_mesh()
        bm.from_mesh(mesh)
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "connected_components": _connected_component_count(bm),
        }
    finally:
        bm.free()
        if mesh is not None:
            evaluated.to_mesh_clear()


def _connected_component_count(bm: bmesh.types.BMesh) -> int:
    remaining = set(bm.verts)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    return count


def _liquid_material_metrics(obj: bpy.types.Object) -> dict[str, Any]:
    principled: list[dict[str, float]] = []
    volume_absorption_count = 0
    connected_volume_absorption = 0
    for slot in obj.material_slots:
        material = slot.material
        if material is None or not material.use_nodes or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                ior = next((socket.default_value for socket in node.inputs if socket.name == "IOR"), 0.0)
                transmission = next(
                    (socket.default_value for socket in node.inputs if socket.name in {"Transmission Weight", "Transmission"}),
                    0.0,
                )
                roughness = next((socket.default_value for socket in node.inputs if socket.name == "Roughness"), 1.0)
                principled.append(
                    {"ior": float(ior), "transmission": float(transmission), "roughness": float(roughness)}
                )
            elif node.bl_idname == "ShaderNodeVolumeAbsorption":
                volume_absorption_count += 1
                if any(link.from_node == node and link.to_socket.name == "Volume" for link in material.node_tree.links):
                    connected_volume_absorption += 1
    plausible_surface = any(
        1.30 <= item["ior"] <= 1.36 and item["transmission"] >= 0.5 and item["roughness"] <= 0.25
        for item in principled
    )
    return {
        "principled_surfaces": principled,
        "plausible_liquid_surface": plausible_surface,
        "volume_absorption_nodes": volume_absorption_count,
        "connected_volume_absorption": connected_volume_absorption,
    }


def _mesh_metrics(obj: bpy.types.Object, allow_open: bool) -> tuple[dict[str, Any], list[str]]:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    diagonal = _bbox_diagonal(obj)
    position_tolerance = max(diagonal * 1e-6, 1e-7)
    area_tolerance = max(diagonal * diagonal * 1e-12, 1e-14)
    length_tolerance = position_tolerance

    boundary_edges = [edge for edge in bm.edges if len(edge.link_faces) == 1]
    non_manifold_edges = [edge for edge in bm.edges if not edge.is_manifold]
    wire_edges = [edge for edge in bm.edges if edge.is_wire]
    loose_vertices = [vert for vert in bm.verts if not vert.link_edges and not vert.link_faces]
    zero_length_edges = [edge for edge in bm.edges if edge.calc_length() <= length_tolerance]
    zero_area_faces = [face for face in bm.faces if face.calc_area() <= area_tolerance]
    connected_components = _connected_component_count(bm)
    smooth_faces = sum(bool(face.smooth) for face in bm.faces)
    flat_faces = len(bm.faces) - smooth_faces

    buckets: dict[tuple[int, int, int], int] = {}
    duplicate_positions = 0
    for vert in bm.verts:
        key = tuple(int(round(float(component) / position_tolerance)) for component in vert.co)
        if key in buckets:
            duplicate_positions += 1
        buckets[key] = buckets.get(key, 0) + 1

    aspect_ratios: list[float] = []
    face_angles: list[float] = []
    for face in bm.faces:
        lengths = [edge.calc_length() for edge in face.edges if edge.calc_length() > length_tolerance]
        if lengths:
            aspect_ratios.append(max(lengths) / max(min(lengths), length_tolerance))
    for edge in bm.edges:
        if edge.is_manifold:
            try:
                face_angles.append(math.degrees(abs(edge.calc_face_angle(0.0))))
            except Exception:
                pass

    scale = [float(value) for value in obj.scale]
    non_uniform_scale = max(scale) - min(scale) > 1e-4
    dimensions = [abs(float(value)) for value in obj.dimensions]
    bbox_volume = dimensions[0] * dimensions[1] * dimensions[2]
    bbox_volume_ratio = bbox_volume / max(diagonal ** 3, 1e-12)
    primitive_signature = None
    if (len(bm.verts), len(bm.edges), len(bm.faces)) == (8, 12, 6):
        primitive_signature = "box"
    elif (len(bm.verts), len(bm.edges), len(bm.faces)) == (4, 4, 1):
        primitive_signature = "plane"
    elif (
        len(bm.faces) >= 5
        and len(bm.verts) == 2 * (len(bm.faces) - 2)
        and len(bm.edges) == 3 * (len(bm.faces) - 2)
    ):
        primitive_signature = "capped_cylinder"
    metrics = {
        "object": obj.name,
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "bbox_diagonal": diagonal,
        "position_tolerance": position_tolerance,
        "boundary_edges": len(boundary_edges),
        "non_manifold_edges": len(non_manifold_edges),
        "wire_edges": len(wire_edges),
        "loose_vertices": len(loose_vertices),
        "zero_length_edges": len(zero_length_edges),
        "zero_area_faces": len(zero_area_faces),
        "duplicate_positions": duplicate_positions,
        "connected_components": connected_components,
        "smooth_faces": smooth_faces,
        "flat_faces": flat_faces,
        "smooth_face_ratio": smooth_faces / max(len(bm.faces), 1),
        "bbox_volume": bbox_volume,
        "bbox_volume_ratio": bbox_volume_ratio,
        "primitive_signature": primitive_signature,
        "max_face_aspect_ratio": max(aspect_ratios, default=0.0),
        "faces_aspect_ratio_over_12": sum(value > 12.0 for value in aspect_ratios),
        "max_manifold_face_angle_degrees": max(face_angles, default=0.0),
        "scale": scale,
        "non_uniform_scale": non_uniform_scale,
        "allow_open": allow_open,
        "modifiers": [
            {
                "name": modifier.name,
                "type": modifier.type,
                "show_viewport": bool(modifier.show_viewport),
                "show_render": bool(modifier.show_render),
            }
            for modifier in obj.modifiers
        ],
    }
    failures: list[str] = []
    if zero_length_edges:
        failures.append("zero_length_edges")
    if zero_area_faces:
        failures.append("zero_area_faces")
    if loose_vertices:
        failures.append("loose_vertices")
    if wire_edges and not allow_open:
        failures.append("wire_edges")
    if non_manifold_edges and not allow_open:
        failures.append("non_manifold_edges")
    if non_uniform_scale:
        failures.append("non_uniform_scale")
    bm.free()
    return metrics, failures


def _part_requirement_checks(
    graph: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not graph:
        return [], [], []
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    for part in graph.get("parts", []):
        requirements = part.get("requirements", {}) if isinstance(part, dict) else {}
        if not requirements:
            continue
        part_id = str(part.get("id", "unknown"))
        validation_mode = str(requirements.get("validation_mode", part.get("validation_mode", "geometry")))
        if validation_mode == "visual_only":
            allowed_roles = {"presentation", "lighting_region", "camera_effect", "helper"}
            role = str(part.get("role", ""))
            evidence_paths = [str(item) for item in part.get("evidence", []) if isinstance(item, str)]
            missing_evidence = [item for item in evidence_paths if not Path(item).is_file()]
            invalid_evidence = [
                item
                for item in evidence_paths
                if Path(item).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".exr"}
            ]
            reasons: list[str] = []
            if role not in allowed_roles:
                reasons.append("visual_only_role_not_allowed")
            if not evidence_paths:
                reasons.append("visual_only_evidence_missing")
            if missing_evidence:
                reasons.append("visual_only_evidence_not_found")
            if invalid_evidence:
                reasons.append("visual_only_evidence_not_visual")
            status = "FAIL" if reasons else "PASS"
            check_id = f"part_requirements_{part_id}"
            checks.append(
                _check(
                    check_id,
                    status,
                    {
                        "validation_mode": validation_mode,
                        "role": role,
                        "evidence": evidence_paths,
                        "missing_evidence": missing_evidence,
                        "invalid_evidence": invalid_evidence,
                        "failed_requirements": reasons,
                    },
                )
            )
            if reasons:
                failures.append(check_id)
            continue
        object_name = _part_object_name(part)
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != "MESH":
            check_id = f"part_requirements_{part_id}"
            checks.append(_check(check_id, "FAIL", {"object": object_name, "reason": "mesh object missing"}))
            failures.append(check_id)
            continue
        allow_open = not bool(requirements.get("closed_volume", False))
        metrics, _ = _mesh_metrics(obj, allow_open)
        reasons: list[str] = []
        if requirements.get("single_component") and metrics["connected_components"] != 1:
            reasons.append("connected_components")
        if requirements.get("closed_volume") and (
            metrics["boundary_edges"] or metrics["wire_edges"] or metrics["non_manifold_edges"]
        ):
            reasons.append("closed_volume")
        min_smooth_ratio = requirements.get("min_smooth_ratio")
        if isinstance(min_smooth_ratio, (int, float)) and metrics["smooth_face_ratio"] < float(min_smooth_ratio):
            reasons.append("smooth_face_ratio")
        min_volume_ratio = requirements.get("min_bbox_volume_ratio")
        if isinstance(min_volume_ratio, (int, float)) and metrics["bbox_volume_ratio"] < float(min_volume_ratio):
            reasons.append("bbox_volume_ratio")
        evidence: dict[str, Any] = {"object": object_name, "requirements": requirements, "mesh": metrics}
        if requirements.get("material_class") == "liquid":
            liquid = _liquid_material_metrics(obj)
            evidence["liquid_material"] = liquid
            if not liquid["plausible_liquid_surface"]:
                reasons.append("liquid_surface")
            if requirements.get("require_volume_absorption", True) and not liquid["connected_volume_absorption"]:
                reasons.append("liquid_volume_absorption")
        status = "FAIL" if reasons else "PASS"
        evidence["failed_requirements"] = reasons
        check_id = f"part_requirements_{part_id}"
        checks.append(_check(check_id, status, evidence))
        if reasons:
            failures.append(check_id)
    return checks, failures, warnings


def _matrix_values(obj: bpy.types.Object) -> list[float]:
    return [round(float(value), 9) for row in obj.matrix_world for value in row]


def _protected_state(obj: bpy.types.Object) -> dict[str, Any]:
    return {
        "type": obj.type,
        "data_name": obj.data.name if obj.data else None,
        "matrix_world": _matrix_values(obj),
        "hide_viewport": bool(obj.hide_viewport),
        "hide_render": bool(obj.hide_render),
        "collections": sorted(collection.name for collection in obj.users_collection),
        "materials": [
            slot.material.name if slot.material is not None else None for slot in obj.material_slots
        ],
    }


def _compare_snapshot(snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    changes: list[dict[str, Any]] = []
    failures: list[str] = []
    for name, expected in snapshot.get("objects", {}).items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            changes.append({"object": name, "change": "missing"})
            failures.append(name)
            continue
        actual = _protected_state(obj)
        relevant_expected = {key: expected.get(key) for key in actual}
        for key, value in actual.items():
            if value != relevant_expected.get(key):
                changes.append(
                    {
                        "object": name,
                        "change": key,
                        "before": relevant_expected.get(key),
                        "after": value,
                    }
                )
                failures.append(name)
    scene_expected = snapshot.get("scene", {})
    scene = bpy.context.scene
    scene_actual = {
        "camera": scene.camera.name if scene.camera else None,
        "world": scene.world.name if scene.world else None,
        "render_engine": scene.render.engine,
        "render_filepath": scene.render.filepath,
    }
    for key, value in scene_actual.items():
        if key in scene_expected and value != scene_expected[key]:
            changes.append(
                {
                    "scene": scene.name,
                    "change": key,
                    "before": scene_expected[key],
                    "after": value,
                }
            )
            failures.append(f"scene.{key}")
    return changes, sorted(set(failures))


def _world_bbox(obj: bpy.types.Object) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = tuple(min(point[index] for point in points) for index in range(3))
    maximum = tuple(max(point[index] for point in points) for index in range(3))
    return minimum, maximum


def _bbox_overlaps(a: bpy.types.Object, b: bpy.types.Object) -> bool:
    a_min, a_max = _world_bbox(a)
    b_min, b_max = _world_bbox(b)
    return all(a_min[index] <= b_max[index] and b_min[index] <= a_max[index] for index in range(3))


def _bbox_gap(a: bpy.types.Object, b: bpy.types.Object) -> float:
    a_min, a_max = _world_bbox(a)
    b_min, b_max = _world_bbox(b)
    squared = 0.0
    for index in range(3):
        if a_max[index] < b_min[index]:
            delta = b_min[index] - a_max[index]
        elif b_max[index] < a_min[index]:
            delta = a_min[index] - b_max[index]
        else:
            delta = 0.0
        squared += delta * delta
    return math.sqrt(squared)


def _bvh(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph) -> BVHTree | None:
    evaluated = obj.evaluated_get(depsgraph)
    mesh = None
    try:
        mesh = evaluated.to_mesh()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        polygons = [tuple(poly.vertices) for poly in mesh.polygons if len(poly.vertices) >= 3]
        if not vertices or not polygons:
            return None
        return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()


def _objects_intersect(
    a: bpy.types.Object,
    b: bpy.types.Object,
    depsgraph: bpy.types.Depsgraph,
) -> tuple[bool, int]:
    if not _bbox_overlaps(a, b):
        return False, 0
    tree_a = _bvh(a, depsgraph)
    tree_b = _bvh(b, depsgraph)
    if tree_a is None or tree_b is None:
        return False, 0
    overlaps = tree_a.overlap(tree_b)
    return bool(overlaps), len(overlaps)


def _relationship_checks(
    graph: dict[str, Any] | None,
    max_unclassified_pairs: int,
    strict_unclassified: bool,
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    if not graph:
        return [], [], ["construction_graph_missing"], []
    parts = {
        part.get("id"): _part_object_name(part)
        for part in graph.get("parts", [])
        if isinstance(part, dict) and part.get("id")
    }
    relationships = graph.get("relationships", [])
    declared_pairs: set[frozenset[str]] = set()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    not_evaluated: list[str] = []
    topology_strikes: list[str] = []
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for index, relation in enumerate(relationships):
        relation_type = relation.get("type")
        if relation_type not in RELATIONSHIP_TYPES:
            failures.append(f"relationship_{index}_invalid_type")
            continue
        a_name = parts.get(relation.get("a"))
        b_name = parts.get(relation.get("b"))
        if not a_name or not b_name:
            failures.append(f"relationship_{index}_unknown_part")
            continue
        declared_pairs.add(frozenset((a_name, b_name)))
        a = bpy.data.objects.get(a_name)
        b = bpy.data.objects.get(b_name)
        if a is None or b is None or a.type != "MESH" or b.type != "MESH":
            not_evaluated.append(f"relationship_{index}_objects_not_mapped")
            continue
        if relation_type in {"continuous_surface", "boolean_fused"}:
            same_object = a == b
            component_count = None
            if same_object:
                bm = bmesh.new()
                bm.from_mesh(a.data)
                component_count = _connected_component_count(bm)
                bm.free()
            status = "PASS" if same_object and component_count == 1 else "FAIL"
            evidence = {
                "a": a_name,
                "b": b_name,
                "type": relation_type,
                "same_mesh_object": same_object,
                "connected_components": component_count,
            }
            if status == "FAIL" and not strict_unclassified:
                status = "WARN"
            if status == "FAIL":
                topology_strikes.append(
                    "boolean_union_not_cleanly_fused"
                    if relation_type == "boolean_fused"
                    else "continuous_surface_not_topology_fused"
                )
        else:
            intersects, overlap_count = _objects_intersect(a, b, depsgraph)
            gap = _bbox_gap(a, b)
            status = "PASS"
            if relation_type in {"mechanical_seam", "intentionally_independent"} and intersects:
                status = "FAIL"
            elif relation_type == "physical_contact" and intersects:
                status = "WARN"
            elif relation.get("require_overlap") and not intersects:
                status = "FAIL"
            elif relation_type in {"embedded_component", "constraint_connection"} and not intersects:
                status = "WARN"
            max_gap = relation.get("max_gap")
            min_gap = relation.get("min_gap")
            if isinstance(max_gap, (int, float)) and gap > float(max_gap):
                status = "FAIL"
            if isinstance(min_gap, (int, float)) and gap < float(min_gap):
                status = "FAIL"
            if status == "FAIL" and not strict_unclassified:
                status = "WARN"
            evidence = {
                "a": a_name,
                "b": b_name,
                "type": relation_type,
                "surface_overlap": intersects,
                "overlap_pairs": overlap_count,
                "bbox_gap": gap,
                "require_overlap": bool(relation.get("require_overlap", False)),
                "max_gap": max_gap,
                "min_gap": min_gap,
            }
        checks.append(_check(f"relationship_{index}", status, evidence))
        if status == "FAIL":
            failures.append(f"relationship_{index}")

    if not graph.get("unclassified_visible_intersections_allowed", False):
        mapped_names = {
            _part_object_name(part)
            for part in graph.get("parts", [])
            if isinstance(part, dict) and part.get("role") in BUILDABLE_ROLES
        }
        meshes = [
            bpy.data.objects[name]
            for name in sorted(mapped_names)
            if name in bpy.data.objects
            and bpy.data.objects[name].type == "MESH"
            and not bpy.data.objects[name].hide_render
        ]
        tested = 0
        for a, b in combinations(meshes, 2):
            if tested >= max_unclassified_pairs:
                not_evaluated.append("unclassified_pair_limit_reached")
                break
            pair = frozenset((a.name, b.name))
            if pair in declared_pairs:
                continue
            if not _bbox_overlaps(a, b):
                continue
            tested += 1
            intersects, overlap_count = _objects_intersect(a, b, depsgraph)
            if intersects:
                status = "FAIL" if strict_unclassified else "WARN"
                check_id = f"unclassified_overlap_{a.name}_{b.name}"
                smoothing_concealment = any(
                    any(poly.use_smooth for poly in obj.data.polygons)
                    or any(modifier.type in {"WEIGHTED_NORMAL", "NORMAL_EDIT"} for modifier in obj.modifiers)
                    for obj in (a, b)
                )
                checks.append(
                    _check(
                        check_id,
                        status,
                        {
                            "a": a.name,
                            "b": b.name,
                            "overlap_pairs": overlap_count,
                            "smoothing_or_normal_concealment": smoothing_concealment,
                        },
                    )
                )
                if strict_unclassified:
                    topology_strikes.append("unclassified_visible_intersection")
                    if smoothing_concealment:
                        topology_strikes.append("smooth_or_weighted_normals_hide_intersection")
                if status == "FAIL":
                    failures.append(check_id)
    return checks, failures, not_evaluated, topology_strikes


def _point_inside_world_bbox(point: Vector, obj: bpy.types.Object, tolerance: float = 1e-5) -> bool:
    minimum, maximum = _world_bbox(obj)
    return all(
        minimum[index] - tolerance <= point[index] <= maximum[index] + tolerance
        for index in range(3)
    )


def _spatial_scene_checks(
    spatial: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not spatial:
        return [], [], []
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    not_evaluated: list[str] = []
    camera_context = spatial.get("camera_context", {})
    if camera_context.get("lock_state") != "locked":
        not_evaluated.append("spatial_scene_mapping_before_camera_lock")
        return checks, failures, not_evaluated

    regions = {
        item.get("id"): item
        for item in spatial.get("regions", [])
        if isinstance(item, dict) and item.get("id")
    }
    for region_id, region in regions.items():
        if (
            region.get("completion_tier") == "deferred"
            or region.get("visibility") == "off_frame_deferred"
        ):
            continue
        object_names = [
            str(value) for value in region.get("object_names", []) if isinstance(value, str)
        ]
        bounds_name = region.get("bounds_object")
        if isinstance(bounds_name, str) and bounds_name:
            object_names.append(bounds_name)
        missing = sorted({name for name in object_names if bpy.data.objects.get(name) is None})
        reasons: list[str] = []
        if not object_names:
            reasons.append("region_scene_mapping_empty")
        if missing:
            reasons.append("region_scene_objects_missing")
        if bounds_name:
            bounds_object = bpy.data.objects.get(str(bounds_name))
            if bounds_object is not None and min(float(value) for value in bounds_object.dimensions) <= 1e-6:
                reasons.append("region_bounds_degenerate")
        status = "FAIL" if reasons else "PASS"
        check_id = f"spatial_region_scene_{region_id}"
        checks.append(
            _check(
                check_id,
                status,
                {
                    "region": region_id,
                    "object_names": sorted(set(object_names)),
                    "bounds_object": bounds_name,
                    "missing": missing,
                    "failed_requirements": reasons,
                },
            )
        )
        if reasons:
            failures.append(check_id)

    camera_region_id = camera_context.get("region_id")
    camera_region = regions.get(camera_region_id, {})
    camera = bpy.context.scene.camera
    camera_bounds_name = camera_region.get("bounds_object") if camera_region else None
    camera_bounds = bpy.data.objects.get(str(camera_bounds_name)) if camera_bounds_name else None
    camera_reasons: list[str] = []
    if camera is None:
        camera_reasons.append("active_camera_missing")
    if camera_bounds is None:
        camera_reasons.append("camera_region_bounds_missing")
    elif camera is not None and not _point_inside_world_bbox(camera.matrix_world.translation, camera_bounds):
        camera_reasons.append("camera_outside_declared_region")
    camera_check_id = "spatial_camera_region_membership"
    checks.append(
        _check(
            camera_check_id,
            "FAIL" if camera_reasons else "PASS",
            {
                "camera": camera.name if camera else None,
                "camera_region": camera_region_id,
                "bounds_object": camera_bounds_name,
                "failed_requirements": camera_reasons,
            },
        )
    )
    if camera_reasons:
        failures.append(camera_check_id)

    depth_types = {
        "opens_into",
        "connected_by_stairs",
        "connected_by_ramp",
        "connected_by_platform",
        "corridor_continuation",
        "continues_beyond_frame",
    }
    for connection in spatial.get("connections", []):
        if not isinstance(connection, dict) or connection.get("type") not in depth_types:
            continue
        connection_id = str(connection.get("id", "unknown"))
        depth_names = [
            str(value)
            for value in connection.get("depth_object_names", [])
            if isinstance(value, str)
        ]
        missing = [name for name in depth_names if bpy.data.objects.get(name) is None]
        degenerate = [
            name
            for name in depth_names
            if bpy.data.objects.get(name) is not None
            and float(bpy.data.objects[name].dimensions.length) <= 1e-6
        ]
        reasons = []
        if not depth_names:
            reasons.append("connection_depth_mapping_empty")
        if missing:
            reasons.append("connection_depth_objects_missing")
        if degenerate:
            reasons.append("connection_depth_objects_degenerate")
        check_id = f"spatial_connection_scene_{connection_id}"
        checks.append(
            _check(
                check_id,
                "FAIL" if reasons else "PASS",
                {
                    "connection": connection_id,
                    "depth_object_names": depth_names,
                    "missing": missing,
                    "degenerate": degenerate,
                    "failed_requirements": reasons,
                },
            )
        )
        if reasons:
            failures.append(check_id)

    for structure in spatial.get("directional_structures", []):
        if not isinstance(structure, dict):
            continue
        structure_id = str(structure.get("id", "unknown"))
        control_names = [
            str(value)
            for value in structure.get("control_object_names", [])
            if isinstance(value, str) and value
        ]
        generated_names = [
            str(value)
            for value in structure.get("generated_object_names", [])
            if isinstance(value, str) and value
        ]
        anchor_names = structure.get("anchor_object_names", {})
        start_name = anchor_names.get("start") if isinstance(anchor_names, dict) else None
        end_name = anchor_names.get("end") if isinstance(anchor_names, dict) else None
        all_names = control_names + generated_names + [
            name for name in (start_name, end_name) if isinstance(name, str) and name
        ]
        missing = sorted({name for name in all_names if bpy.data.objects.get(name) is None})
        reasons: list[str] = []
        if not control_names:
            reasons.append("directional_control_mapping_empty")
        if not generated_names:
            reasons.append("directional_generated_mapping_empty")
        if not start_name or not end_name:
            reasons.append("directional_anchor_mapping_empty")
        if missing:
            reasons.append("directional_scene_objects_missing")
        generated_objects = [
            bpy.data.objects[name]
            for name in generated_names
            if bpy.data.objects.get(name) is not None
        ]
        degenerate = [
            obj.name for obj in generated_objects if _bbox_diagonal(obj) <= 1e-6
        ]
        if degenerate:
            reasons.append("directional_generated_objects_degenerate")
        direction_dot = None
        anchor_clearance = None
        start_object = bpy.data.objects.get(str(start_name)) if start_name else None
        end_object = bpy.data.objects.get(str(end_name)) if end_name else None
        if start_object is not None and end_object is not None:
            anchor_vector = end_object.matrix_world.translation - start_object.matrix_world.translation
            declared = structure.get("direction_vector")
            if (
                isinstance(declared, list)
                and len(declared) == 3
                and all(isinstance(value, (int, float)) for value in declared)
            ):
                direction_dot = anchor_vector.dot(Vector(tuple(float(value) for value in declared)))
                if direction_dot <= 0:
                    reasons.append("directional_anchor_order_mismatch")
            if generated_objects:
                boxes = [_world_bbox(obj) for obj in generated_objects]
                minimum = Vector(tuple(min(box[0][axis] for box in boxes) for axis in range(3)))
                maximum = Vector(tuple(max(box[1][axis] for box in boxes) for axis in range(3)))
                anchor_clearance = max((maximum - minimum).length * 0.05, 1e-4)
                for label, point in {
                    "start": start_object.matrix_world.translation,
                    "end": end_object.matrix_world.translation,
                }.items():
                    if any(
                        point[axis] < minimum[axis] - anchor_clearance
                        or point[axis] > maximum[axis] + anchor_clearance
                        for axis in range(3)
                    ):
                        reasons.append(f"directional_{label}_anchor_outside_generated_bounds")
        check_id = f"directional_structure_scene_{structure_id}"
        checks.append(
            _check(
                check_id,
                "FAIL" if reasons else "PASS",
                {
                    "structure": structure_id,
                    "control_object_names": control_names,
                    "generated_object_names": generated_names,
                    "anchor_object_names": {"start": start_name, "end": end_name},
                    "missing": missing,
                    "degenerate": degenerate,
                    "direction_dot": direction_dot,
                    "anchor_clearance": anchor_clearance,
                    "failed_requirements": reasons,
                },
            )
        )
        if reasons:
            failures.append(check_id)
    return checks, failures, not_evaluated


def _topology_stage_checks(
    graph: dict[str, Any] | None,
    stage_state: dict[str, Any] | None,
) -> tuple[
    list[dict[str, Any]],
    list[str],
    list[str],
    list[str],
    list[str],
    str | None,
]:
    if not stage_state:
        return [], [], [], ["stage_state_missing"], [], None

    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    not_evaluated: list[str] = []
    detected_strikes: list[str] = []
    stage = str(stage_state.get("modeling_stage", "analysis"))
    if stage not in MODELING_STAGES:
        checks.append(_check("production_stage", "FAIL", {"modeling_stage": stage}))
        return checks, ["production_stage"], warnings, not_evaluated, [], None
    stage_index = MODELING_STAGES.index(stage)

    stage_reasons: list[str] = []
    if stage == "analysis":
        if stage_state.get("mutations_blocked") is not True:
            stage_reasons.append("analysis_mutation_lock_missing")
    elif stage == "blockout":
        if stage_state.get("analysis_gate_status") not in {"provisional", "passed"}:
            stage_reasons.append("minimum_analysis_gate_not_passed")
        if not graph or graph.get("part_graph_status") not in {"provisional", "approved"}:
            stage_reasons.append("provisional_part_graph_not_approved")
    else:
        if stage_state.get("analysis_gate_status") != "passed":
            stage_reasons.append("analysis_gate_not_passed")
        if not graph or graph.get("part_graph_status") != "approved":
            stage_reasons.append("part_graph_not_approved")
    if stage_state.get("project_disposition", {}).get("status") == "awaiting_deletion_decision":
        if stage_state.get("mutations_blocked") is not True:
            stage_reasons.append("deletion_decision_does_not_block_mutation")
    checks.append(
        _check(
            "production_stage",
            "FAIL" if stage_reasons else "PASS",
            {"modeling_stage": stage, "failed_requirements": stage_reasons},
        )
    )
    if stage_reasons:
        failures.append("production_stage")

    form_gates = stage_state.get("form_gates", {})
    gate_requirements = {
        "structural_forms": [("primary_masses", "passed"), ("topology_gate_status", "passed")],
        "transition_forms": [("structural_forms", "passed")],
        "functional_parts": [("transition_forms", "passed"), ("topology_gate_status", "passed")],
        "surface_details": [("functional_parts", "passed")],
        "systems": [("surface_details", "passed")],
        "surfacing": [("surface_details", "passed")],
        "lighting": [("surface_details", "passed")],
        "final": [("surface_details", "passed")],
    }
    form_reasons: list[str] = []
    for required_gate, expected in gate_requirements.get(stage, []):
        actual = (
            stage_state.get(required_gate)
            if required_gate == "topology_gate_status"
            else form_gates.get(required_gate)
        )
        if actual != expected:
            form_reasons.append(f"{required_gate}_not_passed")
    if form_reasons:
        detected_strikes.append(
            "missing_structural_or_transition_forms"
            if stage_index >= MODELING_STAGES.index("functional_parts")
            else "form_gate_order_violation"
        )
    checks.append(
        _check(
            "form_gate_order",
            "FAIL" if form_reasons else "PASS",
            {"modeling_stage": stage, "failed_requirements": form_reasons},
        )
    )
    if form_reasons:
        failures.append("form_gate_order")

    parts = [
        part
        for part in (graph or {}).get("parts", [])
        if isinstance(part, dict) and part.get("role") in BUILDABLE_ROLES
    ]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for part in parts:
        part_id = str(part.get("id", "unknown"))
        object_name = _part_object_name(part)
        obj = bpy.data.objects.get(object_name)
        form_level = str(part.get("form_level", ""))
        topology_status = str(part.get("topology_status", "planned"))
        reasons: list[str] = []
        part_strikes: list[str] = []

        active_late_part = (
            form_level in {"functional", "detail"}
            and (obj is not None or topology_status in {"in_progress", "passed"})
        )
        if active_late_part and form_gates.get("transition_forms") != "passed":
            reasons.append("functional_or_detail_before_transition_forms")
            part_strikes.append("functional_or_detail_before_transition_forms")
        if (
            active_late_part
            and stage_index >= MODELING_STAGES.index("functional_parts")
            and part.get("separation_policy") not in {"instance_source", "temporary_construction"}
            and not part.get("assembly_interfaces")
        ):
            reasons.append("functional_part_has_no_receiving_interface")
            part_strikes.append("functional_part_missing_assembly_interface")

        if (
            stage_index > MODELING_STAGES.index("topology_construction")
            and form_level in {"primary", "structural", "transition"}
        ):
            if part.get("blockout_proxy") is not False:
                reasons.append("blockout_proxy_remains")
                part_strikes.append("blockout_proxy_as_final_topology")
            if topology_status not in {"passed", "deferred", "not_applicable"}:
                reasons.append("formal_topology_not_passed")
                part_strikes.append("formal_topology_incomplete")

        raw_evidence = part.get("topology_evidence", {})
        evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
        if topology_status == "passed":
            if obj is None or obj.type != "MESH":
                reasons.append("final_mesh_object_missing")
                part_strikes.append("final_object_mapping_missing")
            else:
                operations = evidence.get("construction_operations", [])
                if not operations:
                    reasons.append("construction_operations_missing")
                    part_strikes.append("primitive_only_formal_modeling")
                try:
                    evaluated = _evaluated_mesh_summary(obj, depsgraph)
                except Exception as exc:
                    evaluated = {"error": repr(exc)}
                    reasons.append("evaluated_mesh_unavailable")
                base_metrics, _ = _mesh_metrics(obj, allow_open=True)
                declared_components = evidence.get("connected_component_count")
                actual_components = evaluated.get("connected_components")
                if not isinstance(declared_components, int) or declared_components < 1:
                    reasons.append("component_evidence_missing")
                    part_strikes.append("unexplained_mesh_islands")
                elif isinstance(actual_components, int) and actual_components != declared_components:
                    reasons.append("component_evidence_mismatch")
                    part_strikes.append("unexplained_mesh_islands")
                if part.get("separation_policy") == "continuous_shell":
                    if part.get("combination_level") != "D_TOPOLOGY_FUSION":
                        reasons.append("continuous_shell_not_level_d")
                        part_strikes.append("join_or_grouping_as_topology_fusion")
                    if actual_components != 1:
                        reasons.append("continuous_shell_not_single_component")
                        part_strikes.append("unexplained_mesh_islands")
                if (
                    part.get("combination_level") == "B_OBJECT_JOIN"
                    and part.get("separation_policy") == "continuous_shell"
                ):
                    reasons.append("object_join_claimed_as_fusion")
                    part_strikes.append("join_or_grouping_as_topology_fusion")

                modifiers = {modifier.type for modifier in obj.modifiers}
                topology_generating_modifiers = {
                    "BOOLEAN",
                    "SCREW",
                    "SOLIDIFY",
                    "NODES",
                    "REMESH",
                    "SKIN",
                    "WELD",
                }
                primitive_retained_reason = evidence.get("primitive_retained_reason")
                if (
                    stage_index > MODELING_STAGES.index("structural_forms")
                    and form_level in {"primary", "structural", "transition"}
                    and base_metrics.get("primitive_signature") is not None
                    and not topology_generating_modifiers.intersection(modifiers)
                    and not (
                        isinstance(primitive_retained_reason, str)
                        and primitive_retained_reason.strip()
                    )
                ):
                    reasons.append("unexplained_primitive_signature")
                    part_strikes.append("primitive_only_formal_modeling")
                bevel_policy = part.get("bevel_policy", {})
                bevel_classes = bevel_policy.get("classes", []) if isinstance(bevel_policy, dict) else []
                bevel_method = str(bevel_policy.get("method", "unresolved")) if isinstance(bevel_policy, dict) else "unresolved"
                if bevel_classes:
                    if bevel_method in {"", "unresolved", "not_applicable"}:
                        reasons.append("bevel_method_missing")
                        part_strikes.append("required_bevel_has_no_transition_geometry")
                    elif "MODIFIER" in bevel_method.upper():
                        base_faces = len(obj.data.polygons)
                        evaluated_faces = evaluated.get("faces")
                        if "BEVEL" not in modifiers or not isinstance(evaluated_faces, int) or evaluated_faces <= base_faces:
                            reasons.append("bevel_modifier_has_no_evaluated_geometry")
                            part_strikes.append("required_bevel_has_no_transition_geometry")
                    else:
                        normalized_ops = " ".join(str(value).lower() for value in operations)
                        if evidence.get("evaluated_bevel_geometry") is not True or not any(
                            token in normalized_ops for token in ("bevel", "support_loop", "crease")
                        ):
                            reasons.append("direct_bevel_evidence_missing")
                            part_strikes.append("required_bevel_has_no_transition_geometry")
                    width_values = []
                    widths = bevel_policy.get("widths", {}) if isinstance(bevel_policy, dict) else {}
                    for edge_class in bevel_classes:
                        if str(edge_class).upper() == "SHARP_EDGE":
                            continue
                        value = widths.get(edge_class) if isinstance(widths, dict) else None
                        if isinstance(value, (int, float)):
                            width_values.append(round(float(value), 9))
                    non_sharp_count = sum(str(value).upper() != "SHARP_EDGE" for value in bevel_classes)
                    if non_sharp_count > 1 and len(set(width_values)) < 2:
                        reasons.append("bevel_classes_share_one_or_missing_width")
                        part_strikes.append("single_bevel_width_for_all_edge_classes")

                construction_method = str(part.get("construction_method", part.get("construction", ""))).upper()
                if ("BOOLEAN" in construction_method or "BOOLEAN" in modifiers) and evidence.get("boolean_cleanup_passed") is not True:
                    reasons.append("boolean_cleanup_evidence_missing")
                    part_strikes.append("boolean_result_without_cleanup")

                wireframe = evidence.get("wireframe")
                if not isinstance(wireframe, str) or not Path(wireframe).is_file():
                    reasons.append("part_wireframe_missing")
                    part_strikes.append("wireframe_acceptance_missing")

        part_strikes = sorted(set(part_strikes))
        detected_strikes.extend(part_strikes)
        checks.append(
            _check(
                f"topology_part_{part_id}",
                "FAIL" if reasons else "PASS",
                {
                    "object": object_name,
                    "form_level": form_level,
                    "topology_status": topology_status,
                    "failed_requirements": sorted(set(reasons)),
                    "topology_strikes": part_strikes,
                },
            )
        )
        if reasons:
            failures.append(f"topology_part_{part_id}")

    if stage_index > MODELING_STAGES.index("topology_construction"):
        review = stage_state.get("review_evidence", {})
        required_views = ("front_clay", "side_clay", "top_clay", "hero_clay", "wireframe")
        valid_paths = [
            str(Path(value).resolve())
            for key in required_views
            for value in [review.get(key)]
            if isinstance(value, str) and Path(value).is_file()
        ]
        missing_views = [
            key
            for key in required_views
            if not isinstance(review.get(key), str) or not Path(str(review.get(key))).is_file()
        ]
        duplicate_paths = len(valid_paths) != len(set(valid_paths))
        review_reasons = [f"missing_{key}" for key in missing_views]
        if duplicate_paths:
            review_reasons.append("review_paths_not_unique")
        if review_reasons:
            detected_strikes.append("wireframe_or_multiview_acceptance_missing")
        checks.append(
            _check(
                "topology_review_evidence",
                "FAIL" if review_reasons else "PASS",
                {"paths": review, "failed_requirements": review_reasons},
            )
        )
        if review_reasons:
            failures.append("topology_review_evidence")

    persisted = [str(value) for value in stage_state.get("topology_rollback_strikes", [])]
    topology_strikes = sorted(set(persisted + detected_strikes))
    structural_strikes = {
        "missing_structural_or_transition_forms",
        "form_gate_order_violation",
        "functional_or_detail_before_transition_forms",
    }
    rollback_target = None
    if len(topology_strikes) >= 2:
        rollback_target = (
            "structural_forms"
            if structural_strikes.intersection(topology_strikes)
            else "topology_construction"
        )
    return (
        checks,
        failures,
        warnings,
        not_evaluated,
        topology_strikes,
        rollback_target,
    )


def _system_scene_checks(
    graph: dict[str, Any] | None,
    stage_state: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    if not graph:
        return [], [], [], ["system_checks_without_construction_graph"]
    stage = str((stage_state or {}).get("modeling_stage", "analysis"))
    stage_index = MODELING_STAGES.index(stage) if stage in MODELING_STAGES else 0
    strict = stage_index >= MODELING_STAGES.index("systems")
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    not_evaluated: list[str] = []
    simulation_modifier_types = {
        "CLOTH",
        "SOFT_BODY",
        "FLUID",
        "DYNAMIC_PAINT",
        "OCEAN",
        "WAVE",
        "PARTICLE_SYSTEM",
        "COLLISION",
    }
    expected_modifiers = {
        "cloth": {"CLOTH"},
        "soft_body": {"SOFT_BODY"},
        "fluid": {"FLUID"},
        "dynamic_paint": {"DYNAMIC_PAINT"},
        "ocean": {"OCEAN"},
        "wave": {"WAVE"},
        "particle": {"PARTICLE_SYSTEM"},
        "particles": {"PARTICLE_SYSTEM"},
        "collision": {"COLLISION"},
        "rigid_body": set(),
    }
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for part in graph.get("parts", []):
        if not isinstance(part, dict) or part.get("role") not in BUILDABLE_ROLES:
            continue
        part_id = str(part.get("id", "unknown"))
        object_name = _part_object_name(part)
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            continue
        modifier_types = {modifier.type for modifier in obj.modifiers}
        actual_simulation = sorted(simulation_modifier_types.intersection(modifier_types))
        if obj.rigid_body is not None:
            actual_simulation.append("RIGID_BODY")
        simulation = part.get("simulation")
        sim_reasons: list[str] = []
        sim_evidence: dict[str, Any] = {
            "object": object_name,
            "actual_systems": actual_simulation,
        }
        if actual_simulation and not isinstance(simulation, dict):
            sim_reasons.append("simulation_spec_missing")
        elif isinstance(simulation, dict):
            system = str(simulation.get("system", "")).lower()
            expected = expected_modifiers.get(system)
            if expected is None:
                sim_reasons.append("simulation_system_unknown")
            elif system == "rigid_body":
                if obj.rigid_body is None:
                    sim_reasons.append("rigid_body_missing")
            elif expected and not expected.intersection(modifier_types):
                sim_reasons.append("simulation_modifier_missing")
            low_test = simulation.get("low_resolution_test", {})
            sim_evidence["declared"] = simulation
            if strict:
                if not isinstance(low_test, dict) or low_test.get("status") != "passed":
                    sim_reasons.append("low_resolution_test_not_passed")
                elif not low_test.get("evidence"):
                    sim_reasons.append("low_resolution_test_evidence_missing")
                if system in {"cloth", "soft_body", "rigid_body", "fluid"}:
                    if not isinstance(low_test.get("max_penetration"), (int, float)):
                        sim_reasons.append("penetration_metric_missing")
                    if not isinstance(low_test.get("penetration_threshold"), (int, float)):
                        sim_reasons.append("penetration_threshold_missing")
                if simulation.get("cache_required") is True:
                    cache_states = []
                    for modifier in obj.modifiers:
                        point_cache = getattr(modifier, "point_cache", None)
                        if point_cache is not None:
                            cache_states.append(bool(getattr(point_cache, "is_baked", False)))
                    sim_evidence["cache_states"] = cache_states
                    if cache_states and not any(cache_states):
                        sim_reasons.append("required_cache_not_baked")
                    elif not cache_states and system == "rigid_body":
                        world = bpy.context.scene.rigidbody_world
                        point_cache = getattr(world, "point_cache", None) if world else None
                        rigid_baked = bool(getattr(point_cache, "is_baked", False))
                        sim_evidence["rigid_body_cache_baked"] = rigid_baked
                        if not rigid_baked:
                            sim_reasons.append("required_rigid_body_cache_not_baked")
                    elif not cache_states and system == "fluid":
                        cache_path = simulation.get("cache_path")
                        sim_evidence["cache_path"] = cache_path
                        if not isinstance(cache_path, str) or not Path(cache_path).exists():
                            sim_reasons.append("required_fluid_cache_path_missing")
                    elif not cache_states:
                        sim_reasons.append("required_cache_not_inspectable")
        if actual_simulation or isinstance(simulation, dict):
            sim_status = "FAIL" if strict and sim_reasons else ("WARN" if sim_reasons else "PASS")
            check_id = f"simulation_part_{part_id}"
            sim_evidence["failed_requirements"] = sim_reasons
            checks.append(_check(check_id, sim_status, sim_evidence))
            if sim_status == "FAIL":
                failures.append(check_id)
            elif sim_status == "WARN":
                warnings.append(check_id)

        procedural = part.get("procedural")
        procedural_modifiers = [
            modifier for modifier in obj.modifiers if modifier.type in {"NODES", "ARRAY"}
        ]
        if not procedural_modifiers and not isinstance(procedural, dict):
            continue
        proc_reasons: list[str] = []
        proc_evidence: dict[str, Any] = {
            "object": object_name,
            "modifiers": [modifier.type for modifier in procedural_modifiers],
        }
        if procedural_modifiers and not isinstance(procedural, dict):
            proc_reasons.append("procedural_spec_missing")
        elif isinstance(procedural, dict):
            proc_evidence["declared"] = procedural
            if strict and procedural.get("status") != "passed":
                proc_reasons.append("procedural_test_not_passed")
            source_names = [str(value) for value in procedural.get("source_objects", [])]
            missing_sources = [name for name in source_names if bpy.data.objects.get(name) is None]
            if not source_names:
                proc_reasons.append("procedural_sources_empty")
            if missing_sources:
                proc_reasons.append("procedural_sources_missing")
            realize_nodes: list[str] = []
            node_groups: list[str] = []
            for modifier in procedural_modifiers:
                if modifier.type != "NODES" or modifier.node_group is None:
                    continue
                node_groups.append(modifier.node_group.name)
                realize_nodes.extend(
                    node.name
                    for node in modifier.node_group.nodes
                    if node.bl_idname == "GeometryNodeRealizeInstances"
                )
            proc_evidence["node_groups"] = node_groups
            proc_evidence["realize_instances_nodes"] = realize_nodes
            if realize_nodes and not str(procedural.get("realize_reason", "")).strip():
                proc_reasons.append("realize_instances_without_reason")
            if procedural.get("animated_random") is True and procedural.get("stable_ids") is not True:
                proc_reasons.append("animated_random_without_stable_ids")
            try:
                evaluated = _evaluated_mesh_summary(obj, depsgraph)
            except Exception as exc:
                evaluated = {"error": repr(exc)}
                proc_reasons.append("procedural_evaluated_mesh_unavailable")
            proc_evidence["evaluated_mesh"] = evaluated
            vertex_budget = procedural.get("viewport_vertex_budget")
            if (
                isinstance(vertex_budget, int)
                and isinstance(evaluated.get("vertices"), int)
                and evaluated["vertices"] > vertex_budget
            ):
                proc_reasons.append("procedural_vertex_budget_exceeded")
            for count_key in ("instance_count", "realized_count"):
                value = procedural.get(count_key)
                if strict and (not isinstance(value, int) or value < 0):
                    proc_reasons.append(f"{count_key}_missing")
        proc_status = "FAIL" if strict and proc_reasons else ("WARN" if proc_reasons else "PASS")
        check_id = f"procedural_part_{part_id}"
        proc_evidence["failed_requirements"] = proc_reasons
        checks.append(_check(check_id, proc_status, proc_evidence))
        if proc_status == "FAIL":
            failures.append(check_id)
        elif proc_status == "WARN":
            warnings.append(check_id)
    return checks, failures, warnings, not_evaluated


def validate_scene(
    graph: dict[str, Any] | None,
    snapshot: dict[str, Any] | None,
    object_names: list[str],
    allow_open_objects: set[str],
    max_unclassified_pairs: int,
    spatial_hypothesis: dict[str, Any] | None = None,
    stage_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    not_evaluated: list[str] = []
    repair: list[str] = []
    targets = [
        bpy.data.objects[name]
        for name in object_names
        if name in bpy.data.objects and bpy.data.objects[name].type == "MESH"
    ] if object_names else [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

    for obj in targets:
        metrics, mesh_failures = _mesh_metrics(obj, obj.name in allow_open_objects)
        status = "FAIL" if mesh_failures else ("WARN" if metrics["duplicate_positions"] else "PASS")
        checks.append(_check(f"mesh_{obj.name}", status, metrics))
        if mesh_failures:
            failures.extend(f"{obj.name}:{failure}" for failure in mesh_failures)
            repair.append(f"Repair mesh legality and transforms on {obj.name}")
        elif metrics["duplicate_positions"]:
            warnings.append(f"{obj.name}:duplicate_positions")

    if snapshot:
        changes, protected_failures = _compare_snapshot(snapshot)
        checks.append(
            _check(
                "protected_scene_state",
                "FAIL" if protected_failures else "PASS",
                {"changes": changes},
            )
        )
        if protected_failures:
            failures.extend(f"protected:{name}" for name in protected_failures)
            repair.append("Restore unauthorized protected-scene changes from the checkpoint")
    else:
        not_evaluated.append("protected_scene_state")

    modeling_stage = str((stage_state or {}).get("modeling_stage", "analysis"))
    strict_relationships = (
        modeling_stage in MODELING_STAGES
        and MODELING_STAGES.index(modeling_stage) >= MODELING_STAGES.index("topology_construction")
    )
    relation_checks, relation_failures, relation_unknown, relation_strikes = _relationship_checks(
        graph, max_unclassified_pairs, strict_relationships
    )
    checks.extend(relation_checks)
    failures.extend(relation_failures)
    not_evaluated.extend(relation_unknown)

    requirement_checks, requirement_failures, requirement_warnings = _part_requirement_checks(graph)
    checks.extend(requirement_checks)
    failures.extend(requirement_failures)
    warnings.extend(requirement_warnings)

    spatial_checks, spatial_failures, spatial_unknown = _spatial_scene_checks(
        spatial_hypothesis
    )
    checks.extend(spatial_checks)
    failures.extend(spatial_failures)
    not_evaluated.extend(spatial_unknown)

    (
        topology_checks,
        topology_failures,
        topology_warnings,
        topology_unknown,
        topology_strikes,
        rollback_target,
    ) = _topology_stage_checks(graph, stage_state)
    checks.extend(topology_checks)
    failures.extend(topology_failures)
    warnings.extend(topology_warnings)
    not_evaluated.extend(topology_unknown)
    topology_strikes = sorted(set(topology_strikes + relation_strikes))
    if len(topology_strikes) >= 2 and rollback_target is None:
        rollback_target = "topology_construction"
    if rollback_target is not None:
        repair.append(
            f"Restore the last accepted task-owned checkpoint and return to {rollback_target}"
        )

    system_checks, system_failures, system_warnings, system_unknown = _system_scene_checks(
        graph, stage_state
    )
    checks.extend(system_checks)
    failures.extend(system_failures)
    warnings.extend(system_warnings)
    not_evaluated.extend(system_unknown)

    status = "FAIL" if failures else ("WARN" if warnings or not_evaluated or any(check["status"] == "WARN" for check in checks) else "PASS")
    return {
        "schema_version": "1.0",
        "generator": "blender-geometry-validation/scripts/validate_scene.py",
        "manual_status_override_allowed": False,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "overall_status": status,
        "modeling_stage": modeling_stage,
        "topology_rollback_strikes": topology_strikes,
        "rollback": {
            "required": rollback_target is not None,
            "target": rollback_target,
            "reasons": topology_strikes,
            "decision_owner": "blender-production-router",
        },
        "checks": checks,
        "thresholds": {
            "position_tolerance": "max(bbox_diagonal * 1e-6, 1e-7 m)",
            "face_aspect_ratio_warning": 12.0,
            "non_uniform_scale_delta": 1e-4,
            "max_unclassified_pairs": max_unclassified_pairs,
        },
        "intentional_exceptions": [
            {"object": name, "exception": "open boundaries allowed"}
            for name in sorted(allow_open_objects)
        ],
        "not_evaluated": sorted(set(not_evaluated)),
        "repair_suggestions": sorted(set(repair)),
        "failures": sorted(set(failures)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--construction-graph")
    parser.add_argument("--snapshot")
    parser.add_argument("--object", action="append", default=[])
    parser.add_argument("--allow-open-object", action="append", default=[])
    parser.add_argument("--max-unclassified-pairs", type=int, default=200)
    parser.add_argument("--spatial-hypothesis")
    parser.add_argument("--stage-state")
    args = parser.parse_args(_script_args())
    graph = (
        json.loads(Path(args.construction_graph).read_text(encoding="utf-8"))
        if args.construction_graph
        else None
    )
    snapshot = (
        json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        if args.snapshot
        else None
    )
    spatial_hypothesis = (
        json.loads(Path(args.spatial_hypothesis).read_text(encoding="utf-8"))
        if args.spatial_hypothesis
        else None
    )
    stage_state_path = Path(args.stage_state).expanduser().resolve() if args.stage_state else None
    stage_state = (
        json.loads(stage_state_path.read_text(encoding="utf-8"))
        if stage_state_path
        else None
    )
    report = validate_scene(
        graph,
        snapshot,
        args.object,
        set(args.allow_open_object),
        args.max_unclassified_pairs,
        spatial_hypothesis,
        stage_state,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "VALIDATION_REPORT "
        + json.dumps(
            {
                "output": str(output),
                "status": report["overall_status"],
                "check_count": len(report["checks"]),
                "failures": len(report["failures"]),
                "not_evaluated": len(report["not_evaluated"]),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["overall_status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
