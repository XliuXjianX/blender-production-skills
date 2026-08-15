#!/usr/bin/env python3
"""Exercise reference artifacts, uncertainty blocking, and image comparison."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    init = _load("reference_init", SCRIPT_DIR / "init_reference_artifacts.py")
    validate = _load("reference_validate", SCRIPT_DIR / "validate_reference_artifacts.py")
    compare = _load("reference_compare", SCRIPT_DIR / "compare_reference_render.py")
    with tempfile.TemporaryDirectory(prefix="blender_reference_smoke_") as temp:
        root = Path(temp)
        reference = root / "reference.png"
        render = root / "render.png"
        Image.new("RGB", (240, 100), (32, 28, 22)).save(reference)
        Image.new("RGB", (240, 100), (34, 29, 23)).save(render)
        view_paths = {}
        for view_type in ("camera", "top", "front", "side"):
            view_path = root / f"blockout_{view_type}.png"
            Image.new("RGB", (120, 80), (42, 42, 42)).save(view_path)
            view_paths[view_type] = view_path
        artifacts = init.build([reference], deliverable="environment")
        derivatives = artifacts["reference_derivatives.json"]
        derivatives["generation_capability"] = "unavailable"
        for key in ("depth_map", "white_model_guide"):
            derivatives[key]["status"] = "skipped_capability_unavailable"
        for name, payload in artifacts.items():
            (root / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        entry_report = validate.validate(root, "blockout_entry")
        observation = artifacts["reference_observation.json"]
        observation["observations"] = [
            {
                "id": "p0_subject",
                "label": "observed subject",
                "priority": "P0",
                "bbox_normalized": [0.35, 0.15, 0.40, 0.70],
                "confidence": 0.9,
                "evidence": ["visible silhouette", "contact edge"],
                "required_visible_cues": ["outer contour", "contact point"],
                "production_domain": "geometry",
                "requires_material": True,
            },
            {
                "id": "p0_window_light",
                "label": "observed projected light",
                "priority": "P0",
                "bbox_normalized": [0.05, 0.05, 0.20, 0.30],
                "confidence": 0.8,
                "evidence": ["soft-edged bright region"],
                "required_visible_cues": ["projected direction", "receiver contact"],
                "production_domain": "lighting",
                "requires_material": False,
            },
        ]
        observation["uncertainty_register"] = [
            {
                "id": "surface_state",
                "impact": "blocking",
                "status": "resolved",
                "hypotheses": ["wet metal", "water"],
                "disposition": "test_variants",
            }
        ]
        observation["visual_priorities"] = ["p0_subject", "p0_window_light"]
        spatial = artifacts["spatial_hypothesis.json"]
        spatial.update(
            {
                "scene_kind": "interior",
                "coordinate_frame": {
                    "up_axis": "Z",
                    "forward_axis": "+Y",
                    "lateral_axis": "+X",
                    "ground_elevation": 0.0,
                    "origin_policy": "camera-region floor datum",
                    "evidence": ["floor boundary", "vertical wall edges"],
                },
                "camera_context": {
                    "region_id": "camera_region",
                    "inside_outside": "inside",
                    "height_range": [1.4, 1.8],
                    "lateral_bias": "center-left",
                    "view_direction": "+Y",
                    "lock_state": "locked",
                    "revision": 1,
                    "confidence": 0.8,
                    "evidence": ["foreground enclosure", "floor convergence"],
                },
                "axes": [
                    {
                        "id": "depth_axis",
                        "role": "depth",
                        "evidence": ["floor and ceiling convergence"],
                    },
                    {
                        "id": "lateral_axis",
                        "role": "lateral",
                        "evidence": ["wall baseline"],
                    },
                ],
                "regions": [
                    {
                        "id": "camera_region",
                        "layer": "camera_enclosure",
                        "visibility": "observed",
                        "completion_tier": "support",
                        "confidence": 0.8,
                        "evidence": ["foreground crop", "floor boundary"],
                    },
                    {
                        "id": "subject_region",
                        "layer": "midground",
                        "visibility": "observed",
                        "completion_tier": "hero",
                        "confidence": 0.9,
                        "evidence": ["subject silhouette", "contact edge"],
                    },
                ],
                "connections": [
                    {
                        "id": "camera_to_subject",
                        "from_region": "camera_region",
                        "to_region": "subject_region",
                        "type": "opens_into",
                        "depth_required": True,
                        "traversable": True,
                        "confidence": 0.8,
                        "evidence": ["continuous floor", "unbroken sightline"],
                    }
                ],
                "occlusion_order": ["camera_region", "p0_subject", "subject_region"],
                "scale_anchors": [
                    {
                        "id": "door_scale",
                        "kind": "door",
                        "plausible_range": [1.9, 2.2],
                        "region_id": "subject_region",
                        "confidence": 0.7,
                        "evidence": ["door-like vertical proportions"],
                    }
                ],
                "alternative_hypotheses": [],
                "spatial_invariants": [
                    "camera and subject regions share a continuous floor",
                    "the opening retains physical depth",
                ],
                "directional_structures": [
                    {
                        "id": "rail_subject",
                        "type": "railing",
                        "start_anchor": "rail_start",
                        "end_anchor": "rail_end",
                        "direction_vector": [0.0, 1.0, 0.0],
                        "up_axis": "Z",
                        "control_path": [[0.0, 0.0, 0.0], [0.0, 3.0, 0.0]],
                        "construction_route": "curve_profile_plus_arc_length_posts",
                        "validation": ["camera", "top", "side", "support_contact"],
                        "supported_edge_id": "subject_platform_edge",
                        "profile": "round_steel_40mm",
                        "post_spacing": 1.0,
                        "anchor_object_names": {
                            "start": "ANCHOR_RAIL_START",
                            "end": "ANCHOR_RAIL_END",
                        },
                        "control_object_names": ["CTRL_RAIL_SUBJECT"],
                        "generated_object_names": ["RAIL_SUBJECT", "RAIL_POSTS_SUBJECT"],
                    }
                ],
                "blockout_views": [
                    {"type": key, "path": str(path), "status": "passed"}
                    for key, path in view_paths.items()
                ],
            }
        )
        artifacts["camera_match.json"].update(
            {
                "projection_hypotheses": [{"type": "perspective", "confidence": 0.8}],
                "line_families": [
                    {"id": "depth", "evidence": ["floor convergence"]},
                    {"id": "vertical", "evidence": ["upright edge"]},
                ],
                "anchors": [
                    {"id": "a", "position": [0.35, 0.15]},
                    {"id": "b", "position": [0.75, 0.15]},
                    {"id": "c", "position": [0.55, 0.85]},
                ],
                "negative_space": {"left": 0.35, "right": 0.25},
                "lock_state": "locked",
                "revision": 1,
            }
        )
        artifacts["material_hypotheses.json"]["materials"] = [
            {
                "entity_id": "p0_subject",
                "hypotheses": [{"substrate": "metal", "confidence": 0.8}],
                "selected_hypothesis": "metal",
                "validation_requirements": {"single_component": True, "min_smooth_ratio": 0.7},
                "required_cues": ["dielectric contamination", "controlled metal highlight"],
            }
        ]
        artifacts["visual_targets.json"].update(
            {
                "attention_order": ["p0_subject"],
                "luminance_zones": [{"id": "subject", "range": [0.1, 0.6]}],
                "light_sources": [{"id": "practical", "type": "visible"}],
                "depth_layers": ["foreground", "subject", "background"],
            }
        )
        artifacts["reference_gate.json"].update(
            {
                "current_gate": "R2",
                "gate_status": "passed",
                "unresolved_blockers": [],
                "evidence_paths": [str(reference)],
                "camera_revision": 1,
            }
        )
        artifacts["reference_gate.json"]["blockout_scoring"].update(
            {
                "attempt_index": 1,
                "current_score": 86,
                "raw_score": 86,
                "consecutive_under_40": 0,
                "disposition": "continue",
                "component_scores": {
                    "primary_form_proportion": 27,
                    "spatial_layout_connectivity": 22,
                    "directional_structures": 22,
                    "structural_contact_support_clearance": 15,
                },
                "history": [
                    {
                        "attempt_index": 1,
                        "attempt_id": "smoke-pass-1",
                        "score": 86,
                        "raw_score": 86,
                        "component_scores": {
                            "primary_form_proportion": 27,
                            "spatial_layout_connectivity": 22,
                            "directional_structures": 22,
                            "structural_contact_support_clearance": 15,
                        },
                        "critical_directional_failure": False,
                        "evidence": [str(reference)],
                    }
                ],
            }
        )
        passed_checks = {
            "p0_observation_completeness",
            "spatial_hypothesis_completeness",
            "camera_evidence",
            "blocking_uncertainty",
            "camera_overlay",
            "negative_space_and_occlusion",
            "portal_and_region_connectivity",
            "camera_spatial_consistency",
            "cross_view_blockout",
            "directional_structure_skeleton",
            "blockout_similarity_score",
            "p0_primary_geometry",
            "part_graph_complete",
            "blockout_replaced_by_formal_topology",
            "structural_forms",
            "transition_forms",
            "assembly_interfaces",
            "real_bevel_geometry",
            "wireframe_acceptance",
            "continuous_connections_and_smoothing",
            "semantic_material_identity",
        }
        for check in artifacts["reference_gate.json"]["checks"]:
            if check["id"] in passed_checks:
                check["status"] = "passed"
                check["evidence"] = [str(reference)]
        for name, payload in artifacts.items():
            (root / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        valid_report = validate.validate(root, "preflight")
        good_graph = {
            "schema_version": "1.0",
            "part_graph_status": "approved",
            "parts": [
                {
                    "id": "p0_subject",
                    "object": "P0_SUBJECT",
                    "final_object_name": "P0_SUBJECT",
                    "role": "primary_form",
                    "construction": "direct_mesh_editing",
                    "form_level": "primary",
                    "blockout_proxy": False,
                    "topology_status": "passed",
                    "bevel_policy": {"classes": ["SECONDARY_BEVEL"], "method": "BEVEL_MODIFIER"},
                    "assembly_interfaces": [],
                    "topology_evidence": {
                        "construction_operations": ["profile_extrusion", "edge_loop_refinement"],
                        "connected_component_count": 1,
                        "evaluated_bevel_geometry": True,
                        "boolean_cleanup_passed": None,
                        "wireframe": str(reference),
                    },
                    "requirements": {"single_component": True, "min_smooth_ratio": 0.7},
                }
            ],
            "relationships": [],
            "unclassified_visible_intersections_allowed": False,
        }
        primary_report = validate.validate(root, "primary_surface", good_graph)
        bad_graph = {**good_graph, "parts": [{**good_graph["parts"][0], "requirements": {}}]}
        missing_requirements_report = validate.validate(root, "primary_surface", bad_graph)
        original_views = spatial["blockout_views"]
        spatial["blockout_views"] = [
            item for item in original_views if item.get("type") != "side"
        ]
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        missing_side_report = validate.validate(root, "blockout")
        spatial["blockout_views"] = original_views
        spatial["camera_context"]["revision"] = 2
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        stale_camera_report = validate.validate(root, "primary_surface", good_graph)
        spatial["camera_context"]["revision"] = 1
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        original_connections = spatial["connections"]
        spatial["connections"] = []
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        disconnected_report = validate.validate(root, "preflight")
        spatial["connections"] = original_connections
        original_direction = spatial["directional_structures"][0]["direction_vector"]
        spatial["directional_structures"][0]["direction_vector"] = [0.0, 0.0, 0.0]
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        invalid_direction_report = validate.validate(root, "preflight")
        spatial["directional_structures"][0]["direction_vector"] = original_direction
        (root / "spatial_hypothesis.json").write_text(
            json.dumps(spatial, indent=2), encoding="utf-8"
        )
        observation["uncertainty_register"][0]["status"] = "unresolved"
        (root / "reference_observation.json").write_text(json.dumps(observation, indent=2), encoding="utf-8")
        blocked_report = validate.validate(root, "preflight")
        comparison = compare.compare(reference, render, root, "smoke", observation["observations"])
        checks = {
            "minimum_entry_allows_reversible_blockout": entry_report["status"] == "PASS",
            "valid_preflight_passes": valid_report["status"] == "PASS",
            "primary_surface_graph_passes": primary_report["status"] == "PASS",
            "missing_p0_requirements_fail": missing_requirements_report["status"] == "FAIL" and "p0_construction_requirements_empty:p0_subject" in missing_requirements_report["errors"],
            "non_geometry_p0_does_not_require_fake_mesh": "p0_construction_part_missing:p0_window_light" not in primary_report["errors"],
            "environment_requires_side_view": missing_side_report["status"] == "FAIL" and "blockout_view_missing:side" in missing_side_report["errors"],
            "camera_revision_change_invalidates_gate": stale_camera_report["status"] == "FAIL" and "camera_spatial_revision_mismatch" in stale_camera_report["errors"],
            "disconnected_spatial_region_fails": disconnected_report["status"] == "FAIL" and "spatial_region_unreachable:subject_region" in disconnected_report["errors"],
            "invalid_directional_skeleton_fails": invalid_direction_report["status"] == "FAIL" and "directional_vector:rail_subject" in invalid_direction_report["errors"],
            "blocking_uncertainty_fails": blocked_report["status"] == "FAIL" and "unresolved_blocking_uncertainty" in blocked_report["errors"],
            "comparison_outputs_exist": Path(comparison["overlay"]).is_file() and Path(comparison["difference"]).is_file(),
            "comparison_passes_near_match": comparison["status"] == "PASS",
        }
        report = {"schema_version": "1.0", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
