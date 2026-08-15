#!/usr/bin/env python3
"""Validate reference-reconstruction artifacts without changing Blender state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
FILES = {
    "reference_derivatives.json",
    "reference_observation.json",
    "spatial_hypothesis.json",
    "camera_match.json",
    "material_hypotheses.json",
    "visual_targets.json",
    "reference_gate.json",
}
REQUIRED_CHECKS = {
    "preflight": {
        "p0_observation_completeness",
        "spatial_hypothesis_completeness",
        "camera_evidence",
        "blocking_uncertainty",
    },
    "blockout": {
        "camera_overlay",
        "negative_space_and_occlusion",
        "portal_and_region_connectivity",
        "camera_spatial_consistency",
        "cross_view_blockout",
        "directional_structure_skeleton",
        "blockout_similarity_score",
    },
    "primary_surface": {
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
    },
    "lookdev": {"causal_aging_and_wetness", "lighting_and_depth"},
    "final": {"final_overlay", "final_semantic_review"},
}
STAGE_ORDER = ["preflight", "blockout", "primary_surface", "lookdev", "final"]
PRODUCTION_DOMAINS = {
    "geometry",
    "material",
    "lighting",
    "atmosphere",
    "post",
    "presentation",
    "spatial_region",
}
SPATIAL_CONNECTION_TYPES = {
    "opens_into",
    "connected_by_stairs",
    "connected_by_ramp",
    "connected_by_platform",
    "corridor_continuation",
    "contains",
    "adjacent",
    "separated_by_boundary",
    "support_contact",
    "continues_beyond_frame",
}
SPATIAL_LAYERS = {
    "camera_enclosure",
    "extreme_foreground",
    "foreground",
    "midground",
    "background",
    "occluded",
    "off_frame",
}


def _bbox_valid(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(item, (int, float)) for item in value)
        and all(0.0 <= float(item) <= 1.0 for item in value)
        and float(value[2]) > 0.0
        and float(value[3]) > 0.0
    )


def _confidence_valid(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0


def _unresolved(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value in {"", "unresolved"})


def _validate_derivatives(
    payload: dict[str, Any],
    require_resolved: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("blocking") is not False:
        errors.append("reference_derivatives_must_be_non_blocking")
    if payload.get("authority") != "auxiliary_hypothesis_only":
        errors.append("reference_derivatives_authority_invalid")
    if payload.get("attempt_limit") != 1:
        errors.append("reference_derivatives_attempt_limit_invalid")
    if payload.get("generation_capability") not in {"unknown", "available", "unavailable"}:
        errors.append("reference_derivatives_capability_invalid")
    allowed = {
        "pending",
        "generated",
        "skipped_capability_unavailable",
        "failed_non_blocking",
        "skipped_no_reference",
    }
    for key in ("depth_map", "white_model_guide"):
        record = payload.get(key, {})
        status = record.get("status")
        attempts = record.get("attempts")
        if status not in allowed:
            errors.append(f"reference_derivative_status:{key}")
            continue
        if not isinstance(attempts, int) or attempts < 0 or attempts > 1:
            errors.append(f"reference_derivative_attempts:{key}")
        if status == "generated":
            if attempts != 1 or not record.get("method"):
                errors.append(f"reference_derivative_generated_metadata:{key}")
            if not Path(str(record.get("path", ""))).is_file():
                errors.append(f"reference_derivative_generated_file:{key}")
        elif status == "failed_non_blocking" and attempts != 1:
            errors.append(f"reference_derivative_failure_attempt:{key}")
        elif status in {"skipped_capability_unavailable", "skipped_no_reference"} and attempts != 0:
            errors.append(f"reference_derivative_skip_attempt:{key}")
        elif status == "pending":
            if require_resolved:
                errors.append(f"reference_derivative_pending:{key}")
            else:
                warnings.append(f"reference_derivative_pending_non_blocking:{key}")
    return errors, warnings


def _validate_directional_structures(
    payload: dict[str, Any],
    stage: str,
    connections: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    structures = [item for item in payload.get("directional_structures", []) if isinstance(item, dict)]
    required_by_connection = any(
        item.get("type") in {"connected_by_stairs", "connected_by_ramp"}
        for item in connections
    )
    if stage in {"blockout", "primary_surface", "lookdev", "final"} and required_by_connection and not structures:
        errors.append("directional_structure_missing_for_elevation_connection")
    valid_types = {
        "stair_flight",
        "stair_system",
        "railing",
        "handrail",
        "ramp",
        "escalator",
        "path_structure",
    }
    seen: set[str] = set()
    for item in structures:
        structure_id = str(item.get("id", "unknown"))
        if structure_id in seen:
            errors.append(f"duplicate_directional_structure:{structure_id}")
        seen.add(structure_id)
        structure_type = item.get("type")
        if structure_type not in valid_types:
            errors.append(f"directional_structure_type:{structure_id}")
        if _unresolved(item.get("start_anchor")):
            errors.append(f"directional_start_anchor:{structure_id}")
        if _unresolved(item.get("end_anchor")):
            errors.append(f"directional_end_anchor:{structure_id}")
        direction = item.get("direction_vector")
        if not (
            isinstance(direction, list)
            and len(direction) == 3
            and all(isinstance(value, (int, float)) for value in direction)
            and sum(float(value) ** 2 for value in direction) > 1e-12
        ):
            errors.append(f"directional_vector:{structure_id}")
        if item.get("up_axis") not in {"X", "Y", "Z", "-X", "-Y", "-Z"}:
            errors.append(f"directional_up_axis:{structure_id}")
        control_path = item.get("control_path")
        points_valid = (
            isinstance(control_path, list)
            and len(control_path) >= 2
            and all(
                isinstance(point, list)
                and len(point) == 3
                and all(isinstance(value, (int, float)) for value in point)
                for point in control_path
            )
        )
        if not points_valid:
            errors.append(f"directional_control_path:{structure_id}")
        elif isinstance(direction, list) and len(direction) == 3:
            path_vector = [
                float(control_path[-1][axis]) - float(control_path[0][axis])
                for axis in range(3)
            ]
            if sum(path_vector[axis] * float(direction[axis]) for axis in range(3)) <= 0:
                errors.append(f"directional_path_order_mismatch:{structure_id}")
        if _unresolved(item.get("construction_route")):
            errors.append(f"directional_construction_route:{structure_id}")
        if not item.get("validation"):
            errors.append(f"directional_validation_empty:{structure_id}")
        if stage in {"blockout", "primary_surface", "lookdev", "final"}:
            anchor_objects = item.get("anchor_object_names")
            if not (
                isinstance(anchor_objects, dict)
                and isinstance(anchor_objects.get("start"), str)
                and anchor_objects.get("start")
                and isinstance(anchor_objects.get("end"), str)
                and anchor_objects.get("end")
            ):
                errors.append(f"directional_anchor_objects:{structure_id}")
            if not item.get("control_object_names"):
                errors.append(f"directional_control_objects_empty:{structure_id}")
            if not item.get("generated_object_names"):
                errors.append(f"directional_generated_objects_empty:{structure_id}")
        if structure_type in {"stair_flight", "stair_system", "escalator"}:
            if not isinstance(item.get("step_count"), int) or int(item.get("step_count", 0)) < 1:
                errors.append(f"directional_step_count:{structure_id}")
            if not isinstance(item.get("rise"), (int, float)) or float(item.get("rise", 0)) <= 0:
                errors.append(f"directional_rise:{structure_id}")
            if not isinstance(item.get("run"), (int, float)) or float(item.get("run", 0)) <= 0:
                errors.append(f"directional_run:{structure_id}")
            if _unresolved(item.get("ascending_from")):
                errors.append(f"directional_ascending_from:{structure_id}")
            if _unresolved(item.get("ascending_to")):
                errors.append(f"directional_ascending_to:{structure_id}")
            if not item.get("landing_anchors"):
                errors.append(f"directional_landing_anchors:{structure_id}")
            if points_valid:
                axis_name = str(item.get("up_axis", "Z"))
                axis_index = {"X": 0, "Y": 1, "Z": 2}.get(axis_name.replace("-", ""), 2)
                axis_sign = -1.0 if axis_name.startswith("-") else 1.0
                elevation_delta = (
                    float(control_path[-1][axis_index]) - float(control_path[0][axis_index])
                ) * axis_sign
                if item.get("ascending_from") == item.get("start_anchor") and elevation_delta <= 0:
                    errors.append(f"directional_ascent_mismatch:{structure_id}")
                if item.get("ascending_from") == item.get("end_anchor") and elevation_delta >= 0:
                    errors.append(f"directional_ascent_mismatch:{structure_id}")
        if structure_type in {"railing", "handrail"}:
            if _unresolved(item.get("supported_edge_id")):
                errors.append(f"directional_supported_edge:{structure_id}")
            if _unresolved(item.get("profile")):
                errors.append(f"directional_profile:{structure_id}")
            if not isinstance(item.get("post_spacing"), (int, float)) or float(item.get("post_spacing", 0)) <= 0:
                errors.append(f"directional_post_spacing:{structure_id}")
            if points_valid and len(control_path) > 2 and _unresolved(item.get("bend_side")):
                errors.append(f"directional_bend_side:{structure_id}")
    return errors


def _validate_blockout_state(gate: dict[str, Any], stage: str) -> list[str]:
    errors: list[str] = []
    scoring = gate.get("blockout_scoring")
    if not isinstance(scoring, dict):
        return ["blockout_scoring_missing"]
    maxima = scoring.get("component_maxima")
    expected_maxima = {
        "primary_form_proportion": 30,
        "spatial_layout_connectivity": 25,
        "directional_structures": 25,
        "structural_contact_support_clearance": 20,
    }
    if maxima != expected_maxima:
        errors.append("blockout_component_maxima_invalid")
    if scoring.get("emergency_rebuild_threshold") != 40:
        errors.append("blockout_rebuild_threshold_invalid")
    if scoring.get("stop_after_consecutive_under_threshold") != 2:
        errors.append("blockout_stop_count_invalid")
    history = [item for item in scoring.get("history", []) if isinstance(item, dict)]
    attempt_ids = [item.get("attempt_id") for item in history]
    if len(attempt_ids) != len(set(attempt_ids)):
        errors.append("blockout_attempt_ids_not_unique")
    current_score = scoring.get("current_score")
    if current_score is not None and not (
        isinstance(current_score, (int, float)) and 0 <= float(current_score) <= 100
    ):
        errors.append("blockout_score_out_of_range")
    disposition = scoring.get("disposition")
    if disposition not in {"not_scored", "continue", "rebuild_required", "awaiting_deletion_decision"}:
        errors.append("blockout_disposition_invalid")
    consecutive = scoring.get("consecutive_under_40")
    if not isinstance(consecutive, int) or consecutive < 0:
        errors.append("blockout_consecutive_count_invalid")
        consecutive = 0
    if stage in {"blockout", "primary_surface", "lookdev", "final"}:
        if current_score is None or not history:
            errors.append("blockout_score_required")
        elif float(current_score) < 40:
            errors.append("blockout_score_below_40")
        if disposition != "continue":
            errors.append(f"blockout_not_clear_to_continue:{disposition}")
    if current_score is not None and float(current_score) < 40:
        if consecutive >= 2:
            if disposition != "awaiting_deletion_decision":
                errors.append("second_low_score_did_not_stop")
            if gate.get("gate_status") != "waiting_for_user":
                errors.append("second_low_score_gate_not_waiting")
        elif consecutive == 1:
            if disposition != "rebuild_required":
                errors.append("first_low_score_did_not_require_rebuild")
            if gate.get("gate_status") != "failed":
                errors.append("first_low_score_gate_not_failed")
    project = gate.get("project_disposition")
    if not isinstance(project, dict):
        errors.append("project_disposition_missing")
        return errors
    if project.get("explicit_user_confirmation_required") is not True:
        errors.append("project_deletion_confirmation_not_required")
    project_status = project.get("status")
    if project_status not in {
        "active",
        "rebuild_required",
        "awaiting_deletion_decision",
        "deletion_rejected",
        "deletion_approved",
    }:
        errors.append("project_disposition_status_invalid")
    if project_status == "awaiting_deletion_decision":
        if project.get("confirmation") is not None:
            errors.append("project_waiting_state_has_confirmation")
        if gate.get("gate_status") != "waiting_for_user":
            errors.append("project_waiting_state_gate_mismatch")
        errors.append("project_waiting_for_user_deletion_decision")
    if project_status == "deletion_approved":
        confirmation = project.get("confirmation")
        if not (
            isinstance(confirmation, dict)
            and confirmation.get("decision") == "delete"
            and confirmation.get("confirmed_by") == "user"
            and confirmation.get("confirmed_paths") == project.get("deletion_candidate_paths")
        ):
            errors.append("project_deletion_approval_invalid")
    return errors


def _validate_spatial_hypothesis(
    payload: dict[str, Any],
    stage: str,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scope = payload.get("deliverable_scope")
    if scope not in {"asset", "animated_asset", "environment", "shot"}:
        errors.append("spatial_deliverable_scope_unresolved")
    scene_kind = payload.get("scene_kind")
    if scene_kind not in {
        "interior",
        "exterior",
        "transitional",
        "object_stage",
        "mixed",
    }:
        errors.append("spatial_scene_kind_unresolved")
    environment_like = scope == "environment" or scene_kind in {
        "interior",
        "exterior",
        "transitional",
        "mixed",
    }

    frame = payload.get("coordinate_frame", {})
    if frame.get("up_axis") not in {"X", "Y", "Z", "-X", "-Y", "-Z"}:
        errors.append("coordinate_up_axis_invalid")
    if frame.get("origin_policy") in {None, "", "unresolved"}:
        errors.append("coordinate_origin_policy_unresolved")
    if environment_like and not isinstance(frame.get("ground_elevation"), (int, float)):
        errors.append("coordinate_ground_elevation_missing")
    if not frame.get("evidence"):
        errors.append("coordinate_frame_evidence_empty")

    regions = [item for item in payload.get("regions", []) if isinstance(item, dict)]
    region_ids = [item.get("id") for item in regions if item.get("id")]
    if not region_ids:
        errors.append("spatial_regions_empty")
    if len(region_ids) != len(set(region_ids)):
        errors.append("duplicate_spatial_region_ids")
    if environment_like and len(region_ids) < 2:
        errors.append("environment_spatial_regions_below_2")
    for region in regions:
        region_id = str(region.get("id", "unknown"))
        if region.get("layer") not in SPATIAL_LAYERS:
            errors.append(f"spatial_region_layer:{region_id}")
        if region.get("visibility") not in {
            "observed",
            "inferred",
            "required_support",
            "off_frame_deferred",
        }:
            errors.append(f"spatial_region_visibility:{region_id}")
        if region.get("completion_tier") not in {
            "hero",
            "support",
            "structural_stub",
            "deferred",
        }:
            errors.append(f"spatial_region_completion_tier:{region_id}")
        if not _confidence_valid(region.get("confidence")):
            errors.append(f"spatial_region_confidence:{region_id}")
        if not region.get("evidence"):
            errors.append(f"spatial_region_evidence:{region_id}")

    camera_context = payload.get("camera_context", {})
    camera_region = camera_context.get("region_id")
    if camera_region not in set(region_ids):
        errors.append("camera_spatial_region_invalid")
    if camera_context.get("inside_outside") not in {
        "inside",
        "outside",
        "threshold",
        "object_stage",
    }:
        errors.append("camera_inside_outside_unresolved")
    if not _confidence_valid(camera_context.get("confidence")):
        errors.append("camera_context_confidence_invalid")
    if not camera_context.get("evidence"):
        errors.append("camera_context_evidence_empty")

    axes = [item for item in payload.get("axes", []) if isinstance(item, dict)]
    if environment_like and not any(item.get("role") == "depth" for item in axes):
        errors.append("depth_axis_missing")
    for axis in axes:
        axis_id = str(axis.get("id", "unknown"))
        if axis.get("role") not in {"depth", "lateral", "vertical", "diagonal"}:
            errors.append(f"spatial_axis_role:{axis_id}")
        if not axis.get("evidence"):
            errors.append(f"spatial_axis_evidence:{axis_id}")

    connections = [item for item in payload.get("connections", []) if isinstance(item, dict)]
    adjacency: dict[str, set[str]] = {str(region_id): set() for region_id in region_ids}
    depth_connections = {
        "opens_into",
        "connected_by_stairs",
        "connected_by_ramp",
        "connected_by_platform",
        "corridor_continuation",
        "continues_beyond_frame",
    }
    for connection in connections:
        connection_id = str(connection.get("id", "unknown"))
        source = connection.get("from_region")
        target = connection.get("to_region")
        relation = connection.get("type")
        if source not in adjacency or target not in adjacency:
            errors.append(f"spatial_connection_endpoint:{connection_id}")
            continue
        if relation not in SPATIAL_CONNECTION_TYPES:
            errors.append(f"spatial_connection_type:{connection_id}")
        if not _confidence_valid(connection.get("confidence")):
            errors.append(f"spatial_connection_confidence:{connection_id}")
        if not connection.get("evidence"):
            errors.append(f"spatial_connection_evidence:{connection_id}")
        if relation in depth_connections and connection.get("depth_required") is not True:
            errors.append(f"spatial_connection_depth_required:{connection_id}")
        adjacency[str(source)].add(str(target))
        adjacency[str(target)].add(str(source))

    errors.extend(_validate_directional_structures(payload, stage, connections))

    if environment_like and camera_region in adjacency:
        reachable = {str(camera_region)}
        frontier = [str(camera_region)]
        while frontier:
            current = frontier.pop()
            for neighbor in adjacency[current] - reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)
        for region in regions:
            region_id = str(region.get("id"))
            if (
                region.get("completion_tier") != "deferred"
                and region.get("visibility") != "off_frame_deferred"
                and region_id not in reachable
            ):
                errors.append(f"spatial_region_unreachable:{region_id}")

    if environment_like and not payload.get("occlusion_order"):
        errors.append("spatial_occlusion_order_empty")
    anchors = [item for item in payload.get("scale_anchors", []) if isinstance(item, dict)]
    if not anchors:
        errors.append("spatial_scale_anchors_empty")
    for anchor in anchors:
        anchor_id = str(anchor.get("id", "unknown"))
        value_range = anchor.get("plausible_range")
        if not (
            isinstance(value_range, list)
            and len(value_range) == 2
            and all(isinstance(value, (int, float)) and float(value) > 0.0 for value in value_range)
            and float(value_range[1]) >= float(value_range[0])
        ):
            errors.append(f"spatial_scale_anchor_range:{anchor_id}")
        if anchor.get("region_id") not in set(region_ids):
            errors.append(f"spatial_scale_anchor_region:{anchor_id}")
        if not _confidence_valid(anchor.get("confidence")):
            errors.append(f"spatial_scale_anchor_confidence:{anchor_id}")
        if not anchor.get("evidence"):
            errors.append(f"spatial_scale_anchor_evidence:{anchor_id}")

    blockers = [
        item
        for item in payload.get("alternative_hypotheses", [])
        if isinstance(item, dict)
        and item.get("impact") == "blocking"
        and item.get("status") not in {"resolved", "accepted_variant"}
    ]
    if blockers:
        errors.append("unresolved_blocking_spatial_hypothesis")
    if not payload.get("spatial_invariants"):
        errors.append("spatial_invariants_empty")

    if stage in {"blockout", "primary_surface", "lookdev", "final"}:
        if camera_context.get("lock_state") != "locked":
            errors.append("spatial_camera_not_locked_after_blockout")
        views = [item for item in payload.get("blockout_views", []) if isinstance(item, dict)]
        passed_types = {
            item.get("type")
            for item in views
            if item.get("status") == "passed" and Path(str(item.get("path", ""))).is_file()
        }
        required_types = {"camera", "top", "front", "side"} if environment_like else {"camera"}
        missing_types = sorted(required_types - passed_types)
        for view_type in missing_types:
            errors.append(f"blockout_view_missing:{view_type}")
        if not environment_like and not passed_types.intersection({"top", "front", "side"}):
            warnings.append("structural_review_view_missing")

    return errors, warnings


def validate(directory: Path, stage: str, construction_graph: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name in sorted(FILES):
        path = directory / name
        if not path.is_file():
            errors.append(f"missing:{name}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid_json:{name}:{exc}")
            continue
        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"schema:{name}")
        payloads[name] = payload
    if errors:
        return {"schema_version": SCHEMA_VERSION, "status": "FAIL", "stage": stage, "errors": errors, "warnings": warnings}

    derivative_errors, derivative_warnings = _validate_derivatives(
        payloads["reference_derivatives.json"],
        require_resolved=stage != "blockout_entry",
    )
    errors.extend(derivative_errors)
    warnings.extend(derivative_warnings)

    observation = payloads["reference_observation.json"]
    sources = observation.get("reference_files", [])
    if not sources:
        errors.append("reference_files_empty")
    for source in sources:
        path = Path(str(source.get("path", "")))
        if not path.is_file():
            errors.append(f"reference_missing:{path}")
        if int(source.get("width", 0)) <= 0 or int(source.get("height", 0)) <= 0:
            errors.append(f"reference_dimensions:{path}")

    if stage == "blockout_entry":
        gate = payloads["reference_gate.json"]
        if gate.get("current_gate") != "R0":
            errors.append("blockout_entry_requires_r0")
        if gate.get("gate_status") not in {"open", "provisional", "passed"}:
            errors.append("blockout_entry_gate_status_invalid")
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
            "stage": stage,
            "errors": sorted(set(errors)),
            "warnings": sorted(set(warnings)),
        }

    observations = observation.get("observations", [])
    p0 = [item for item in observations if item.get("priority") == "P0"]
    if not p0:
        errors.append("p0_observations_empty")
    ids = [item.get("id") for item in observations]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_observation_ids")
    for item in p0:
        item_id = item.get("id", "unknown")
        if not _bbox_valid(item.get("bbox_normalized")):
            errors.append(f"p0_bbox:{item_id}")
        confidence = item.get("confidence")
        if not _confidence_valid(confidence):
            errors.append(f"p0_confidence:{item_id}")
        if not item.get("evidence"):
            errors.append(f"p0_evidence:{item_id}")
        if not item.get("required_visible_cues"):
            errors.append(f"p0_visible_cues:{item_id}")
        if item.get("production_domain") not in PRODUCTION_DOMAINS:
            errors.append(f"p0_production_domain:{item_id}")

    blockers = [
        item for item in observation.get("uncertainty_register", [])
        if item.get("impact") == "blocking" and item.get("status") not in {"resolved", "accepted_variant"}
    ]
    if blockers:
        errors.append("unresolved_blocking_uncertainty")

    spatial = payloads["spatial_hypothesis.json"]
    spatial_errors, spatial_warnings = _validate_spatial_hypothesis(spatial, stage)
    errors.extend(spatial_errors)
    warnings.extend(spatial_warnings)

    camera = payloads["camera_match.json"]
    if len(camera.get("anchors", [])) < 3:
        errors.append("camera_anchors_below_3")
    if not camera.get("projection_hypotheses"):
        errors.append("projection_hypotheses_empty")
    if not camera.get("line_families"):
        errors.append("camera_line_families_empty")
    if not camera.get("negative_space"):
        errors.append("negative_space_empty")
    if camera.get("lock_state") not in {"provisional", "locked"}:
        errors.append("camera_lock_state_invalid")
    if stage in {"blockout", "primary_surface", "lookdev", "final"}:
        if camera.get("lock_state") != "locked":
            errors.append("camera_not_locked_after_blockout")
        if camera.get("revision") != spatial.get("camera_context", {}).get("revision"):
            errors.append("camera_spatial_revision_mismatch")

    materials = payloads["material_hypotheses.json"].get("materials", [])
    material_entities = {item.get("entity_id") for item in materials}
    for item in p0:
        if item.get("requires_material") is True and item.get("id") not in material_entities:
            errors.append(f"p0_material_missing:{item.get('id')}")
    for item in materials:
        if not item.get("hypotheses"):
            errors.append(f"material_hypotheses_empty:{item.get('entity_id')}")
        if not item.get("required_cues"):
            errors.append(f"material_cues_empty:{item.get('entity_id')}")
        if stage in {"primary_surface", "lookdev", "final"}:
            if not item.get("selected_hypothesis"):
                errors.append(f"material_selection_missing:{item.get('entity_id')}")
            if not item.get("validation_requirements"):
                errors.append(f"material_validation_requirements_missing:{item.get('entity_id')}")

    if stage in {"primary_surface", "lookdev", "final"}:
        if not construction_graph:
            errors.append("construction_graph_required")
        else:
            if construction_graph.get("part_graph_status") != "approved":
                errors.append("part_graph_not_approved")
            graph_parts = {
                item.get("id"): item
                for item in construction_graph.get("parts", [])
                if isinstance(item, dict) and item.get("id")
            }
            spatial_region_ids = {
                item.get("id")
                for item in spatial.get("regions", [])
                if isinstance(item, dict) and item.get("id")
            }
            for item in p0:
                item_id = item.get("id")
                domain = item.get("production_domain")
                if domain == "geometry":
                    part = graph_parts.get(item_id)
                    if part is None:
                        errors.append(f"p0_construction_part_missing:{item_id}")
                    elif not part.get("requirements"):
                        errors.append(f"p0_construction_requirements_empty:{item_id}")
                    else:
                        if part.get("blockout_proxy") is not False:
                            errors.append(f"p0_blockout_proxy_remains:{item_id}")
                        if part.get("topology_status") != "passed":
                            errors.append(f"p0_formal_topology_not_passed:{item_id}")
                        if part.get("final_object_name") in {None, "", "unresolved"}:
                            errors.append(f"p0_final_object_missing:{item_id}")
                        topology_evidence = part.get("topology_evidence", {})
                        if not topology_evidence.get("construction_operations"):
                            errors.append(f"p0_construction_operations_empty:{item_id}")
                        component_count = topology_evidence.get("connected_component_count")
                        if not isinstance(component_count, int) or component_count < 1:
                            errors.append(f"p0_component_evidence_missing:{item_id}")
                        wireframe = topology_evidence.get("wireframe")
                        if not isinstance(wireframe, str) or not Path(wireframe).is_file():
                            errors.append(f"p0_wireframe_evidence_missing:{item_id}")
                        bevel_policy = part.get("bevel_policy", {})
                        if bevel_policy.get("method") in {None, "", "unresolved"}:
                            errors.append(f"p0_bevel_policy_missing:{item_id}")
                elif domain == "material":
                    receiver_id = item.get("receiver_id")
                    if receiver_id not in graph_parts:
                        errors.append(f"p0_material_receiver_missing:{item_id}")
                elif domain == "spatial_region":
                    region_id = item.get("region_id", item_id)
                    if region_id not in spatial_region_ids:
                        errors.append(f"p0_spatial_region_missing:{item_id}")
            for index, relation in enumerate(construction_graph.get("relationships", [])):
                if not isinstance(relation, dict) or not relation.get("validation"):
                    errors.append(f"construction_relationship_validation_empty:{index}")
            if construction_graph.get("unclassified_visible_intersections_allowed") is not False:
                errors.append("unclassified_visible_intersections_not_forbidden")

    visual = payloads["visual_targets.json"]
    for key in ("attention_order", "luminance_zones", "light_sources", "depth_layers"):
        if not visual.get(key):
            errors.append(f"visual_targets_empty:{key}")

    gate = payloads["reference_gate.json"]
    expected_stage_mapping = {
        "R0": "analysis",
        "R1": "blockout",
        "R2": "primary_surface",
        "R3": "surfacing_lighting",
        "R4": "final",
    }
    if gate.get("state_authority") != "stage_state.json":
        errors.append("reference_gate_state_authority_invalid")
    if gate.get("stage_mapping") != expected_stage_mapping:
        errors.append("reference_gate_stage_mapping_invalid")
    errors.extend(_validate_blockout_state(gate, stage))
    gate_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}
    required_gate = {"preflight": "R0", "blockout": "R1", "primary_surface": "R2", "lookdev": "R3", "final": "R4"}[stage]
    if gate_order.get(gate.get("current_gate"), -1) < gate_order[required_gate]:
        errors.append(f"gate_below_stage:{gate.get('current_gate')}<{required_gate}")
    if stage != "preflight" and gate.get("gate_status") != "passed":
        errors.append("gate_not_passed")
    if gate.get("unresolved_blockers"):
        errors.append("reference_gate_has_blockers")
    if stage in {"blockout", "primary_surface", "lookdev", "final"} and not gate.get("evidence_paths"):
        errors.append("gate_evidence_empty")
    if stage in {"blockout", "primary_surface", "lookdev", "final"}:
        if gate.get("camera_revision") != camera.get("revision"):
            errors.append("gate_camera_revision_mismatch")
    required_check_ids: set[str] = set()
    for current in STAGE_ORDER[: STAGE_ORDER.index(stage) + 1]:
        required_check_ids.update(REQUIRED_CHECKS[current])
    gate_checks = {
        item.get("id"): item for item in gate.get("checks", [])
        if isinstance(item, dict) and item.get("id")
    }
    for check_id in sorted(required_check_ids):
        check = gate_checks.get(check_id)
        if check is None:
            errors.append(f"gate_check_missing:{check_id}")
        elif check.get("status") != "passed":
            errors.append(f"gate_check_not_passed:{check_id}")
        elif not check.get("evidence"):
            errors.append(f"gate_check_evidence_empty:{check_id}")
    for evidence in gate.get("evidence_paths", []):
        if not Path(str(evidence)).is_file():
            errors.append(f"evidence_missing:{evidence}")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
        "stage": stage,
        "p0_count": len(p0),
        "material_count": len(materials),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument(
        "--stage",
        choices=["blockout_entry", "preflight", "blockout", "primary_surface", "lookdev", "final"],
        default="preflight",
    )
    parser.add_argument("--output")
    parser.add_argument("--construction-graph")
    args = parser.parse_args()
    graph = None
    if args.construction_graph:
        graph = json.loads(Path(args.construction_graph).expanduser().resolve().read_text(encoding="utf-8"))
    report = validate(Path(args.artifact_dir).expanduser().resolve(), args.stage, graph)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
