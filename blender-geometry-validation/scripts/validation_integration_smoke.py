#!/usr/bin/env python3
"""Exercise snapshot and scene validation in an isolated Blender process."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--validation-report", required=True)
    args = parser.parse_args(_script_args())

    snapshot_module = _load_module("snapshot_scene_module", SCRIPT_DIR / "snapshot_scene.py")
    validation_module = _load_module("validate_scene_module", SCRIPT_DIR / "validate_scene.py")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    subject = bpy.context.active_object
    subject.name = "TEST-VALID-SUBJECT"
    subject.modifiers.new("TEST-BEVEL", "BEVEL")

    bpy.ops.object.camera_add(location=(0.0, 0.0, 0.0))
    camera = bpy.context.active_object
    camera.name = "TEST-SPATIAL-CAMERA"
    bpy.context.scene.camera = camera

    bpy.ops.mesh.primitive_cube_add(size=10.0, location=(0.0, 0.0, 0.0))
    camera_region_bounds = bpy.context.active_object
    camera_region_bounds.name = "TEST-CAMERA-REGION-BOUNDS"
    camera_region_bounds.hide_render = True

    bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 5.0, 0.0))
    subject_region_bounds = bpy.context.active_object
    subject_region_bounds.name = "TEST-SUBJECT-REGION-BOUNDS"
    subject_region_bounds.hide_render = True

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 2.5, 0.0))
    corridor_depth = bpy.context.active_object
    corridor_depth.name = "TEST-CONNECTION-DEPTH"
    corridor_depth.scale = (1.0, 5.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    corridor_depth.hide_render = True

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.5, location=(4.0, 0.0, 0.0))
    smooth_subject = bpy.context.active_object
    smooth_subject.name = "TEST-SMOOTH-SUBJECT"
    for polygon in smooth_subject.data.polygons:
        polygon.use_smooth = True

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(8.0, 0.0, 0.0), scale=(1.0, 0.7, 0.01))
    bad_liquid = bpy.context.active_object
    bad_liquid.name = "TEST-BAD-LIQUID-SLAB"
    bad_material = bpy.data.materials.new("TEST-BAD-LIQUID-MATERIAL")
    bad_bsdf = next(node for node in bad_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bad_bsdf.inputs["IOR"].default_value = 1.333
    transmission = next(socket for socket in bad_bsdf.inputs if socket.name in {"Transmission Weight", "Transmission"})
    transmission.default_value = 1.0
    bad_liquid.data.materials.append(bad_material)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(12.0, 0.0, 0.0), scale=(1.0, 0.7, 0.25))
    good_liquid = bpy.context.active_object
    good_liquid.name = "TEST-GOOD-LIQUID-VOLUME"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    good_material = bpy.data.materials.new("TEST-GOOD-LIQUID-MATERIAL")
    good_nodes = good_material.node_tree.nodes
    good_links = good_material.node_tree.links
    good_bsdf = next(node for node in good_nodes if node.type == "BSDF_PRINCIPLED")
    good_bsdf.inputs["IOR"].default_value = 1.333
    good_bsdf.inputs["Roughness"].default_value = 0.05
    good_transmission = next(socket for socket in good_bsdf.inputs if socket.name in {"Transmission Weight", "Transmission"})
    good_transmission.default_value = 1.0
    absorption = good_nodes.new("ShaderNodeVolumeAbsorption")
    output_node = next(node for node in good_nodes if node.type == "OUTPUT_MATERIAL")
    good_links.new(absorption.outputs["Volume"], output_node.inputs["Volume"])
    good_liquid.data.materials.append(good_material)

    visual_evidence_path = Path(args.output).expanduser().resolve().with_name("visual-only-evidence.png")
    visual_evidence_path.parent.mkdir(parents=True, exist_ok=True)
    visual_evidence = bpy.data.images.new("TEST-VISUAL-ONLY-EVIDENCE", width=4, height=4)
    visual_evidence.filepath_raw = str(visual_evidence_path)
    visual_evidence.file_format = "PNG"
    visual_evidence.save()

    snapshot = snapshot_module.capture_snapshot([subject.name])
    graph = {
        "schema_version": "1.0",
        "part_graph_status": "approved",
        "parts": [
            {
                "id": "subject",
                "object": subject.name,
                "role": "primary_form",
                "construction": "direct_mesh_editing",
            }
        ],
        "relationships": [],
        "unclassified_visible_intersections_allowed": False,
    }
    stage_state = {
        "schema_version": "1.0",
        "current_stage": "blockout",
        "modeling_stage": "blockout",
        "analysis_gate_status": "passed",
        "topology_gate_status": "open",
        "form_gates": {
            "primary_masses": "open",
            "structural_forms": "open",
            "transition_forms": "open",
            "functional_parts": "open",
            "surface_details": "open",
        },
        "review_evidence": {},
        "topology_rollback_strikes": [],
        "rollback": {"required": False, "target": None, "reasons": []},
        "mutations_blocked": False,
        "project_disposition": {"status": "active"},
    }
    spatial = {
        "schema_version": "1.0",
        "deliverable_scope": "environment",
        "scene_kind": "interior",
        "camera_context": {
            "region_id": "camera_region",
            "lock_state": "locked",
            "revision": 1,
        },
        "regions": [
            {
                "id": "camera_region",
                "visibility": "observed",
                "completion_tier": "support",
                "object_names": [camera_region_bounds.name],
                "bounds_object": camera_region_bounds.name,
            },
            {
                "id": "subject_region",
                "visibility": "observed",
                "completion_tier": "hero",
                "object_names": [subject.name],
                "bounds_object": subject_region_bounds.name,
            },
        ],
        "connections": [
            {
                "id": "camera_to_subject",
                "from_region": "camera_region",
                "to_region": "subject_region",
                "type": "opens_into",
                "depth_object_names": [corridor_depth.name],
            }
        ],
    }
    baseline_report = validation_module.validate_scene(
        graph=graph,
        snapshot=snapshot,
        object_names=[subject.name],
        allow_open_objects=set(),
        max_unclassified_pairs=20,
        spatial_hypothesis=spatial,
        stage_state=stage_state,
    )

    original_x = subject.location.x
    subject.location.x += 1.0
    bpy.context.view_layer.update()
    mutation_report = validation_module.validate_scene(
        graph=graph,
        snapshot=snapshot,
        object_names=[subject.name],
        allow_open_objects=set(),
        max_unclassified_pairs=20,
        spatial_hypothesis=spatial,
        stage_state=stage_state,
    )
    subject.location.x = original_x
    bpy.context.view_layer.update()

    bad_spatial = json.loads(json.dumps(spatial))
    bad_spatial["connections"][0]["depth_object_names"] = []
    bad_spatial_report = validation_module.validate_scene(
        graph=graph,
        snapshot=snapshot,
        object_names=[subject.name],
        allow_open_objects=set(),
        max_unclassified_pairs=20,
        spatial_hypothesis=bad_spatial,
        stage_state=stage_state,
    )

    semantic_graph = {
        "schema_version": "1.0",
        "part_graph_status": "approved",
        "parts": [
            {
                "id": "smooth_subject",
                "object": smooth_subject.name,
                "role": "primary_form",
                "construction": "subdivision_control_cage",
                "requirements": {"single_component": True, "min_smooth_ratio": 0.8},
            },
            {
                "id": "bad_liquid",
                "object": bad_liquid.name,
                "role": "functional_detail",
                "construction": "static_liquid",
                "requirements": {
                    "single_component": True,
                    "closed_volume": True,
                    "material_class": "liquid",
                    "min_bbox_volume_ratio": 0.02,
                    "require_volume_absorption": True,
                },
            },
            {
                "id": "good_liquid",
                "object": good_liquid.name,
                "role": "functional_detail",
                "construction": "static_liquid",
                "requirements": {
                    "single_component": True,
                    "closed_volume": True,
                    "material_class": "liquid",
                    "min_bbox_volume_ratio": 0.02,
                    "require_volume_absorption": True,
                },
            },
            {
                "id": "presentation_band",
                "role": "presentation",
                "requirements": {"validation_mode": "visual_only"},
                "evidence": [str(visual_evidence_path)],
            },
            {
                "id": "invalid_visual_bypass",
                "role": "primary_form",
                "requirements": {"validation_mode": "visual_only"},
                "evidence": [str(visual_evidence_path)],
            },
        ],
        "relationships": [],
        "unclassified_visible_intersections_allowed": False,
    }
    semantic_report = validation_module.validate_scene(
        graph=semantic_graph,
        snapshot=snapshot,
        object_names=[smooth_subject.name, bad_liquid.name, good_liquid.name],
        allow_open_objects=set(),
        max_unclassified_pairs=20,
        stage_state=stage_state,
    )
    semantic_checks = {check["id"]: check["status"] for check in semantic_report["checks"]}

    checks = {
        "baseline_pass": baseline_report["overall_status"] == "PASS",
        "protected_mutation_detected": mutation_report["overall_status"] == "FAIL",
        "mesh_check_present": any(
            check["id"] == f"mesh_{subject.name}" for check in baseline_report["checks"]
        ),
        "protected_check_present": any(
            check["id"] == "protected_scene_state" for check in baseline_report["checks"]
        ),
        "spatial_scene_mapping_passes": any(
            check["id"] == "spatial_camera_region_membership" and check["status"] == "PASS"
            for check in baseline_report["checks"]
        ),
        "missing_connection_depth_fails": bad_spatial_report["overall_status"] == "FAIL"
        and "spatial_connection_scene_camera_to_subject" in bad_spatial_report["failures"],
        "smooth_requirement_passes": semantic_checks.get("part_requirements_smooth_subject") == "PASS",
        "thin_reflective_slab_fails_liquid": semantic_checks.get("part_requirements_bad_liquid") == "FAIL",
        "closed_absorbing_liquid_passes": semantic_checks.get("part_requirements_good_liquid") == "PASS",
        "visual_only_evidence_passes": semantic_checks.get("part_requirements_presentation_band") == "PASS",
        "visual_only_cannot_bypass_geometry": semantic_checks.get("part_requirements_invalid_visual_bypass") == "FAIL",
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    output = {
        "schema_version": "1.0",
        "status": status,
        "checks": checks,
        "baseline_status": baseline_report["overall_status"],
        "mutation_status": mutation_report["overall_status"],
    }

    smoke_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.validation_report).expanduser().resolve()
    smoke_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    smoke_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(
        json.dumps(baseline_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        "VALIDATION_INTEGRATION_SMOKE "
        + json.dumps(
            {
                "output": str(smoke_path),
                "validation_report": str(report_path),
                "status": status,
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
