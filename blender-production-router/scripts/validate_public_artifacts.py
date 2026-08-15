#!/usr/bin/env python3
"""Validate Blender production-agent public JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA_VERSION = "1.0"
REQUIRED: dict[str, dict[str, type]] = {
    "blender_capabilities.json": {
        "schema_version": str,
        "generated_at": str,
        "blender": dict,
        "capabilities": dict,
    },
    "task_route.json": {
        "schema_version": str,
        "request": str,
        "deliverable": str,
        "classes": list,
        "physical_causes": list,
        "candidates": list,
        "selected_method": str,
        "selected_skill": str,
        "secondary_methods": list,
        "forbidden_substitutions": list,
        "prerequisites": list,
        "validation": list,
        "required_specialists": list,
        "design_owner": str,
        "native_component_decision": dict,
        "local_asset_library": dict,
        "official_doc_resolution": dict,
        "code_role": str,
        "application_policy": str,
        "fallback_reason": (str, type(None)),
    },
    "production_analysis.json": {
        "schema_version": str,
        "generated_at": str,
        "status": str,
        "execution_allowed": bool,
        "execution_scope": str,
        "deliverable": str,
        "completion_scope": str,
        "protected_scope": dict,
        "real_scale": dict,
        "minimum_viable_analysis": dict,
        "design_intent": dict,
        "focal_hierarchy": list,
        "depth_layers": list,
        "visual_flow": dict,
        "camera_mobility": dict,
        "representation_budget": dict,
        "performance_budget": dict,
        "failure_repair_policy": dict,
        "object_partition_basis": list,
        "geometry_vs_shading": list,
        "form_hierarchy": dict,
        "part_graph_status": str,
        "lighting_analysis": dict,
        "material_analysis": dict,
        "critical_blockers": list,
        "blocking_unknowns": list,
        "assumptions": list,
    },
    "reference_derivatives.json": {
        "schema_version": str,
        "generated_at": str,
        "source_references": list,
        "generation_capability": str,
        "attempt_limit": int,
        "blocking": bool,
        "authority": str,
        "depth_map": dict,
        "white_model_guide": dict,
    },
    "construction_graph.json": {
        "schema_version": str,
        "part_graph_status": str,
        "parts": list,
        "relationships": list,
        "unclassified_visible_intersections_allowed": bool,
        "modeling_contract": dict,
    },
    "part_review_scores.json": {
        "schema_version": str,
        "generated_at": str,
        "max_automatic_reviews_per_part_stage": int,
        "thresholds": dict,
        "stage_criteria": dict,
        "parts": list,
        "project_policy": dict,
    },
    "stage_state.json": {
        "schema_version": str,
        "current_stage": str,
        "modeling_stage": str,
        "iteration": int,
        "visual_gate": str,
        "gate_status": str,
        "protected_objects": list,
        "checkpoints": list,
        "mutations_blocked": bool,
        "allowed_operations": list,
        "project_disposition": dict,
        "analysis_gate_status": str,
        "topology_gate_status": str,
        "form_gates": dict,
        "review_evidence": dict,
        "topology_rollback_strikes": list,
        "rollback": dict,
        "part_progress": dict,
        "authority": dict,
        "review_budgets": dict,
        "route_conflict": dict,
        "local_repair_requests": list,
    },
    "lighting_plan.json": {
        "schema_version": str,
        "generated_at": str,
        "analysis_status": str,
        "reference_evidence": dict,
        "first_pass": dict,
        "lights": list,
        "unresolved_blockers": list,
    },
    "validation_report.json": {
        "schema_version": str,
        "generated_at": str,
        "overall_status": str,
        "checks": list,
        "thresholds": dict,
        "intentional_exceptions": list,
        "not_evaluated": list,
        "repair_suggestions": list,
    },
}
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
FORM_LEVELS = {"primary", "structural", "transition", "functional", "detail", "helper"}
TOPOLOGY_STATUSES = {"planned", "in_progress", "passed", "deferred", "not_applicable"}
BUILDABLE_ROLES = {
    "primary_form",
    "structural_part",
    "functional_detail",
    "decorative_detail",
    "cutter",
}
SEPARATION_POLICIES = {
    "continuous_shell",
    "separate_manufactured_part",
    "moving_part",
    "transparent_part",
    "instance_source",
    "temporary_construction",
}
COMBINATION_LEVELS = {
    "A_VISUAL_GROUPING",
    "B_OBJECT_JOIN",
    "C_PHYSICAL_ASSEMBLY",
    "D_TOPOLOGY_FUSION",
    "NOT_APPLICABLE",
    "unresolved",
}
PART_REVIEW_STAGES = {
    "analysis_readiness",
    "blockout",
    "formal_topology",
    "structural_transition",
    "systems",
    "surfacing",
    "final",
}
PART_REVIEW_DISPOSITIONS = {
    "not_scored",
    "pass",
    "repair_local",
    "rebuild_part",
    "needs_user_review",
    "deferred",
}
DERIVATIVE_STATUSES = {
    "pending",
    "generated",
    "skipped_capability_unavailable",
    "failed_non_blocking",
    "skipped_no_reference",
}
CODE_ROLES = {"orchestration", "direct_topology_exception", "none"}
APPLICATION_POLICIES = {
    "keep_non_destructive",
    "apply_for_downstream_topology",
    "realize_for_export",
    "bake_simulation",
    "not_applicable",
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
COARSE_STAGE_COMPATIBILITY = {
    "analysis": {"preflight", "route"},
    "blockout": {"blockout"},
    "topology_construction": {"primary_surface"},
    "structural_forms": {"primary_surface"},
    "transition_forms": {"primary_surface"},
    "functional_parts": {"primary_surface", "secondary"},
    "surface_details": {"secondary"},
    "systems": {"systems"},
    "surfacing": {"secondary"},
    "lighting": {"validation", "final"},
    "final": {"final"},
}
REFERENCE_REQUIRED: dict[str, list[str]] = {
    "reference_observation.json": ["schema_version", "reference_files", "observations", "uncertainty_register", "visual_priorities"],
    "spatial_hypothesis.json": [
        "schema_version",
        "deliverable_scope",
        "scene_kind",
        "coordinate_frame",
        "camera_context",
        "axes",
        "regions",
        "connections",
        "occlusion_order",
        "scale_anchors",
        "alternative_hypotheses",
        "spatial_invariants",
        "hypothesis_revision",
        "directional_structures",
        "blockout_views",
    ],
    "camera_match.json": ["schema_version", "projection_hypotheses", "anchors", "negative_space", "tolerances"],
    "material_hypotheses.json": ["schema_version", "materials", "global_aging_causes", "wetness_policy"],
    "visual_targets.json": ["schema_version", "attention_order", "luminance_zones", "light_sources", "depth_layers"],
    "reference_gate.json": [
        "schema_version",
        "state_authority",
        "stage_mapping",
        "current_gate",
        "gate_status",
        "checks",
        "evidence_paths",
        "blockout_scoring",
        "project_disposition",
        "unresolved_blockers",
    ],
}


def validate_artifact(name: str, payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{name}: root must be an object"]
    for key, expected_type in REQUIRED[name].items():
        if key not in payload:
            errors.append(f"{name}: missing {key}")
        elif not isinstance(payload[key], expected_type):
            if isinstance(expected_type, tuple):
                expected_name = " or ".join(item.__name__ for item in expected_type)
            else:
                expected_name = expected_type.__name__
            errors.append(f"{name}: {key} must be {expected_name}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{name}: unsupported schema_version {payload.get('schema_version')!r}")
    if name == "blender_capabilities.json":
        executable = payload.get("blender", {}).get("executable")
        if not isinstance(executable, str) or not Path(executable).is_absolute():
            errors.append(f"{name}: blender.executable must be an absolute path")
        elif Path(executable).name.lower().startswith("python"):
            errors.append(f"{name}: blender.executable points to embedded Python, not Blender")
    if name == "task_route.json":
        resolution = payload.get("official_doc_resolution", {})
        if resolution.get("status") not in {
            "pending_capability_probe",
            "cached",
            "live_built",
            "unavailable",
        }:
            errors.append(f"{name}: invalid official_doc_resolution.status")
        for source in resolution.get("resolved_sources", []):
            parsed = urlparse(str(source))
            if parsed.scheme != "https" or parsed.hostname not in {
                "docs.blender.org",
                "extensions.blender.org",
            }:
                errors.append(f"{name}: non-official documentation source {source}")
    if name == "construction_graph.json":
        if payload.get("part_graph_status") not in {"analysis_required", "provisional", "approved", "failed"}:
            errors.append(f"{name}: invalid part_graph_status")
        contract = payload.get("modeling_contract", {})
        required_contract = {
            "analysis_before_mutation": True,
            "minimum_viable_analysis_allows_reversible_blockout": True,
            "part_analysis_required_before_formal_topology": True,
            "primitive_blockout_is_final": False,
            "continuous_shell_requires_single_component": True,
            "difficulty_is_valid_separation_reason": False,
            "functional_or_detail_before_transition_allowed": False,
            "material_or_lighting_may_conceal_geometry_failure": False,
            "wireframe_acceptance_required": True,
            "real_bevel_geometry_required": True,
            "python_is_orchestration_layer": True,
            "native_component_ownership_required": True,
            "manual_count_driven_fragments_allowed": False,
        }
        for key, expected in required_contract.items():
            if contract.get(key) is not expected:
                errors.append(f"{name}: modeling_contract.{key} must be {expected}")
        part_ids = {part.get("id") for part in payload.get("parts", []) if isinstance(part, dict)}
        required_part_keys = {
            "id",
            "role",
            "form_level",
            "physical_function",
            "separation_policy",
            "separation_reason",
            "construction_method",
            "connection_method",
            "combination_level",
            "bevel_policy",
            "modifier_stack_intent",
            "native_system",
            "source_objects",
            "semantic_inputs",
            "generated_dependents",
            "code_role",
            "application_policy",
            "native_component_evidence",
            "final_object_name",
            "blockout_proxy",
            "topology_status",
            "blockout_object_names",
            "assembly_interfaces",
            "topology_evidence",
        }
        for index, part in enumerate(payload.get("parts", [])):
            if not isinstance(part, dict):
                errors.append(f"{name}: part {index} must be an object")
                continue
            for key in sorted(required_part_keys - set(part)):
                errors.append(f"{name}: part {index} missing {key}")
            if part.get("form_level") not in FORM_LEVELS:
                errors.append(f"{name}: part {index} invalid form_level")
            if part.get("combination_level") not in COMBINATION_LEVELS:
                errors.append(f"{name}: part {index} invalid combination_level")
            if part.get("topology_status") not in TOPOLOGY_STATUSES:
                errors.append(f"{name}: part {index} invalid topology_status")
            if not isinstance(part.get("blockout_proxy"), bool):
                errors.append(f"{name}: part {index} blockout_proxy must be bool")
            if not isinstance(part.get("blockout_object_names"), list):
                errors.append(f"{name}: part {index} blockout_object_names must be list")
            if not isinstance(part.get("assembly_interfaces"), list):
                errors.append(f"{name}: part {index} assembly_interfaces must be list")
            if not isinstance(part.get("topology_evidence"), dict):
                errors.append(f"{name}: part {index} topology_evidence must be object")
            if not isinstance(part.get("native_system"), str) or not part.get("native_system"):
                errors.append(f"{name}: part {index} native_system must be a non-empty string")
            if not isinstance(part.get("source_objects"), list):
                errors.append(f"{name}: part {index} source_objects must be list")
            if not isinstance(part.get("semantic_inputs"), dict):
                errors.append(f"{name}: part {index} semantic_inputs must be object")
            if not isinstance(part.get("generated_dependents"), list):
                errors.append(f"{name}: part {index} generated_dependents must be list")
            if part.get("code_role") not in CODE_ROLES:
                errors.append(f"{name}: part {index} invalid code_role")
            if part.get("application_policy") not in APPLICATION_POLICIES:
                errors.append(f"{name}: part {index} invalid application_policy")
            if not isinstance(part.get("native_component_evidence"), dict):
                errors.append(f"{name}: part {index} native_component_evidence must be object")
            if "asset_provenance" in part and not isinstance(part.get("asset_provenance"), dict):
                errors.append(f"{name}: part {index} asset_provenance must be object")
            if payload.get("part_graph_status") == "approved" and part.get("role") in BUILDABLE_ROLES:
                for key in (
                    "physical_function",
                    "separation_policy",
                    "separation_reason",
                    "construction_method",
                    "connection_method",
                    "combination_level",
                    "final_object_name",
                    "topology_status",
                ):
                    if part.get(key) in {None, "", "unresolved"}:
                        errors.append(f"{name}: approved part {index} has unresolved {key}")
                if part.get("separation_policy") not in SEPARATION_POLICIES:
                    errors.append(f"{name}: approved part {index} invalid separation_policy")
                bevel_policy = part.get("bevel_policy", {})
                if not isinstance(bevel_policy, dict) or bevel_policy.get("method") in {None, "", "unresolved"}:
                    errors.append(f"{name}: approved part {index} has unresolved bevel_policy")
                if not part.get("source_objects"):
                    errors.append(f"{name}: approved part {index} has no source_objects")
                if part.get("native_system") in {"", "NOT_APPLICABLE", "DEFERRED_PER_PART"}:
                    errors.append(f"{name}: approved part {index} has unresolved native_system")
        for index, relation in enumerate(payload.get("relationships", [])):
            if not isinstance(relation, dict):
                errors.append(f"{name}: relationship {index} must be an object")
                continue
            if relation.get("type") not in RELATIONSHIP_TYPES:
                errors.append(f"{name}: relationship {index} has invalid type")
            if relation.get("a") not in part_ids or relation.get("b") not in part_ids:
                errors.append(f"{name}: relationship {index} references unknown parts")
            if not relation.get("validation"):
                errors.append(f"{name}: relationship {index} validation must not be empty")
    if name == "task_route.json":
        candidate_count = len(payload.get("candidates", []))
        if not 2 <= candidate_count <= 4:
            errors.append(f"{name}: candidates must contain two to four methods")
        if payload.get("design_owner") not in {"blender-scene-design", "not_applicable"}:
            errors.append(f"{name}: invalid design_owner")
        if payload.get("code_role") not in CODE_ROLES:
            errors.append(f"{name}: invalid code_role")
        if payload.get("application_policy") not in APPLICATION_POLICIES:
            errors.append(f"{name}: invalid application_policy")
        native = payload.get("native_component_decision", {})
        for key in (
            "status",
            "primary_system",
            "parameter_owners",
            "source_policy",
            "python_role",
            "application_policy",
            "scene_design_required",
            "official_sources",
            "official_verification_policy",
        ):
            if key not in native:
                errors.append(f"{name}: native_component_decision missing {key}")
        system_choice = native.get("system_choice", {})
        for key in (
            "comparison_required",
            "direct_candidate",
            "node_candidate",
            "selected_system",
            "selection_reason",
            "rejected_alternative",
            "node_justification",
            "boolean_policy",
        ):
            if key not in system_choice:
                errors.append(f"{name}: native_component_decision.system_choice missing {key}")
        if system_choice:
            if not isinstance(system_choice.get("comparison_required"), bool):
                errors.append(f"{name}: system_choice.comparison_required must be bool")
            if not isinstance(system_choice.get("node_justification"), list):
                errors.append(f"{name}: system_choice.node_justification must be list")
            if system_choice.get("node_candidate") is None and system_choice.get("node_justification"):
                errors.append(f"{name}: system_choice cannot justify a missing node candidate")
            if native.get("primary_system") == "BOOLEAN" and system_choice.get("boolean_policy") != "native_boolean_required_for_normal_hard_surface_cuts":
                errors.append(f"{name}: Boolean route must declare the native Boolean policy")
        library = payload.get("local_asset_library", {})
        if library.get("status") not in {"not_requested", "available", "unavailable"}:
            errors.append(f"{name}: invalid local_asset_library.status")
        if not isinstance(library.get("requested"), bool):
            errors.append(f"{name}: local_asset_library.requested must be bool")
        request_origin = library.get("request_origin")
        if request_origin is not None and request_origin not in {"not_requested", "user_explicit", "router_node_candidate"}:
            errors.append(f"{name}: invalid local_asset_library.request_origin")
        if not isinstance(library.get("eligible_catalogs"), list):
            errors.append(f"{name}: local_asset_library.eligible_catalogs must be list")
        if library.get("status") == "not_requested" and library.get("requested") is not False:
            errors.append(f"{name}: not_requested local asset library must not be requested")
        if library.get("status") == "not_requested" and request_origin is not None and request_origin != "not_requested":
            errors.append(f"{name}: not_requested local asset library must use not_requested origin")
        if library.get("status") == "available" and (
            library.get("requested") is not True or not isinstance(library.get("root"), str)
        ):
            errors.append(f"{name}: available local asset library requires requested=true and a root")
    if name == "production_analysis.json":
        if payload.get("status") not in {"open", "provisional", "complete", "passed", "failed"}:
            errors.append(f"{name}: invalid status")
        if payload.get("execution_scope") not in {"none", "reversible_blockout", "formal_production"}:
            errors.append(f"{name}: invalid execution_scope")
        minimum = payload.get("minimum_viable_analysis", {})
        if minimum.get("status") not in {"open", "passed", "failed"}:
            errors.append(f"{name}: invalid minimum_viable_analysis.status")
        attempts = minimum.get("attempts")
        if not isinstance(attempts, int) or attempts < 0 or attempts > 2:
            errors.append(f"{name}: minimum analysis attempts must be between 0 and 2")
        if minimum.get("max_automatic_reviews") != 2:
            errors.append(f"{name}: minimum analysis review limit must be 2")
        design_intent = payload.get("design_intent", {})
        if design_intent.get("status") not in {"unresolved", "provisional", "resolved", "passed", "not_applicable"}:
            errors.append(f"{name}: invalid design_intent.status")
        if payload.get("camera_mobility", {}).get("mode") is None:
            errors.append(f"{name}: camera_mobility.mode is required")
        required_decisions = minimum.get("required_decisions", {})
        expected_decisions = {
            "deliverable_scope",
            "protected_scope",
            "major_parts_or_regions",
            "scale_strategy",
            "provisional_route",
        }
        if set(required_decisions) != expected_decisions or not all(
            isinstance(value, bool) for value in required_decisions.values()
        ):
            errors.append(f"{name}: invalid minimum analysis decision set")
        hierarchy = payload.get("form_hierarchy", {})
        for key in ("primary_masses", "structural_forms", "transition_forms", "functional_parts", "surface_details"):
            if not isinstance(hierarchy.get(key), list):
                errors.append(f"{name}: form_hierarchy.{key} must be list")
        if payload.get("completion_scope") not in {
            "unresolved",
            "hero_only",
            "camera_visible",
            "reusable_asset",
            "navigable_environment",
        }:
            errors.append(f"{name}: invalid completion_scope")
        real_scale = payload.get("real_scale", {})
        if real_scale.get("status") not in {"unresolved", "estimated", "confirmed", "not_applicable"}:
            errors.append(f"{name}: invalid real_scale.status")
    if name == "reference_derivatives.json":
        if payload.get("generation_capability") not in {"unknown", "available", "unavailable"}:
            errors.append(f"{name}: invalid generation_capability")
        if payload.get("attempt_limit") != 1:
            errors.append(f"{name}: attempt_limit must be 1")
        if payload.get("blocking") is not False:
            errors.append(f"{name}: derivatives must be non-blocking")
        if payload.get("authority") != "auxiliary_hypothesis_only":
            errors.append(f"{name}: invalid authority")
        for key in ("depth_map", "white_model_guide"):
            record = payload.get(key, {})
            status = record.get("status")
            attempts = record.get("attempts")
            if status not in DERIVATIVE_STATUSES:
                errors.append(f"{name}: invalid {key}.status")
            if not isinstance(attempts, int) or attempts < 0 or attempts > 1:
                errors.append(f"{name}: {key}.attempts must be 0 or 1")
            if status in {"generated", "failed_non_blocking"} and attempts != 1:
                errors.append(f"{name}: {key} terminal attempt state requires attempts=1")
            if status in {"skipped_capability_unavailable", "skipped_no_reference"} and attempts != 0:
                errors.append(f"{name}: {key} skipped state requires attempts=0")
            if status == "generated" and (
                not isinstance(record.get("path"), str) or not record.get("method")
            ):
                errors.append(f"{name}: generated {key} requires path and method")
    if name == "part_review_scores.json":
        if payload.get("max_automatic_reviews_per_part_stage") != 2:
            errors.append(f"{name}: automatic review limit must be 2")
        if payload.get("thresholds") != {
            "pass": 80,
            "pass_with_local_repairs": 60,
            "rebuild_part": 40,
        }:
            errors.append(f"{name}: invalid thresholds")
        policy = payload.get("project_policy", {})
        if policy.get("noncritical_failure_scope") != "part_only":
            errors.append(f"{name}: non-critical failure must remain part-local")
        if policy.get("critical_failure_scope") != "current_visual_gate_only":
            errors.append(f"{name}: critical failure scope must be the current visual gate")
        if policy.get("project_delete_from_part_failure") is not False:
            errors.append(f"{name}: part failure must not authorize project deletion")
        criteria = payload.get("stage_criteria", {})
        if not isinstance(criteria, dict):
            criteria = {}
        if set(criteria) != PART_REVIEW_STAGES:
            errors.append(f"{name}: invalid stage criteria set")
        for stage, components in criteria.items():
            numeric_values = list(components.values()) if isinstance(components, dict) else []
            if (
                not numeric_values
                or not all(isinstance(value, (int, float)) for value in numeric_values)
                or sum(numeric_values) != 100
            ):
                errors.append(f"{name}: {stage} criteria must sum to 100")
        part_ids: list[str] = []
        for index, part in enumerate(payload.get("parts", [])):
            if not isinstance(part, dict) or not isinstance(part.get("part_id"), str):
                errors.append(f"{name}: part {index} invalid")
                continue
            part_ids.append(part["part_id"])
            if not isinstance(part.get("critical"), bool):
                errors.append(f"{name}: part {index} critical must be bool")
            stages = part.get("stages", {})
            if not isinstance(stages, dict):
                errors.append(f"{name}: part {part['part_id']} stages must be an object")
                continue
            if set(stages) != PART_REVIEW_STAGES:
                errors.append(f"{name}: part {part['part_id']} stage set is incomplete")
                continue
            for stage, record in stages.items():
                if not isinstance(record, dict):
                    errors.append(f"{name}: {part['part_id']}:{stage} must be an object")
                    continue
                attempts = record.get("attempts")
                history = record.get("history")
                disposition = record.get("disposition")
                score = record.get("current_score")
                consecutive = record.get("consecutive_below_60")
                if not isinstance(attempts, int) or attempts < 0 or attempts > 2:
                    errors.append(f"{name}: {part['part_id']}:{stage} attempts exceed limit")
                if not isinstance(history, list) or len(history) > 2 or len(history) != attempts:
                    errors.append(f"{name}: {part['part_id']}:{stage} history/attempt mismatch")
                    history = []
                if disposition not in PART_REVIEW_DISPOSITIONS:
                    errors.append(f"{name}: {part['part_id']}:{stage} invalid disposition")
                if not isinstance(record.get("gate_clear"), bool):
                    errors.append(f"{name}: {part['part_id']}:{stage} gate_clear must be bool")
                if not isinstance(consecutive, int) or consecutive < 0 or consecutive > 2:
                    errors.append(f"{name}: {part['part_id']}:{stage} invalid failure count")
                if score is not None and not isinstance(score, (int, float)):
                    errors.append(f"{name}: {part['part_id']}:{stage} score must be numeric")
                elif isinstance(score, (int, float)) and not 0 <= float(score) <= 100:
                    errors.append(f"{name}: {part['part_id']}:{stage} score out of range")
                attempt_ids = [item.get("attempt_id") for item in history if isinstance(item, dict)]
                if len(attempt_ids) != len(set(attempt_ids)):
                    errors.append(f"{name}: {part['part_id']}:{stage} duplicate attempt IDs")
                for attempt in history:
                    if not isinstance(attempt, dict) or not attempt.get("evidence"):
                        errors.append(f"{name}: {part['part_id']}:{stage} attempt lacks evidence")
                        continue
                    components = attempt.get("components", {})
                    expected = criteria.get(stage, {})
                    if set(components) != set(expected):
                        errors.append(f"{name}: {part['part_id']}:{stage} component mismatch")
                        continue
                    if not all(isinstance(value, (int, float)) for value in components.values()):
                        errors.append(f"{name}: {part['part_id']}:{stage} components must be numeric")
                        continue
                    total_value = attempt.get("total")
                    if not isinstance(total_value, (int, float)):
                        errors.append(f"{name}: {part['part_id']}:{stage} total must be numeric")
                        continue
                    total = sum(float(value) for value in components.values())
                    if abs(total - float(total_value)) > 1e-4:
                        errors.append(f"{name}: {part['part_id']}:{stage} total mismatch")
                if disposition == "needs_user_review" and not (
                    attempts == 2 and consecutive == 2 and record.get("gate_clear") is False
                ):
                    errors.append(f"{name}: {part['part_id']}:{stage} invalid review stop state")
                if disposition == "deferred" and not (
                    attempts == 0 and score is None and record.get("gate_clear") is True
                ):
                    errors.append(f"{name}: {part['part_id']}:{stage} invalid deferred state")
        if len(part_ids) != len(set(part_ids)):
            errors.append(f"{name}: duplicate part IDs")
    if name == "lighting_plan.json":
        first = payload.get("first_pass", {})
        if first.get("allowed_sources") != ["SUN", "WORLD"]:
            errors.append(f"{name}: first pass must allow only SUN and WORLD")
        if first.get("gray_model_required") is not True:
            errors.append(f"{name}: gray model must be required")
        if first.get("topology_gate_required") is not True:
            errors.append(f"{name}: topology gate must be required")
    if name == "validation_report.json":
        if payload.get("overall_status") not in {"PASS", "WARN", "FAIL"}:
            errors.append(f"{name}: invalid overall_status")
    if name == "stage_state.json":
        authority = payload.get("authority", {})
        if authority.get("state_owner") != "blender-production-router":
            errors.append(f"{name}: Router must own production state")
        if authority.get("validator_can_reroute") is not False:
            errors.append(f"{name}: validator_can_reroute must be false")
        if authority.get("specialist_can_restart_analysis") is not False:
            errors.append(f"{name}: specialist_can_restart_analysis must be false")
        expected_budgets = {
            "minimum_analysis_reviews": 2,
            "technical_repairs_per_stage": 3,
            "part_reviews_per_part_stage": 2,
            "consecutive_white_model_under_40_stop": 2,
            "route_candidate_replacements": 1,
            "unchanged_geometry_render_counts_as_attempt": False,
        }
        for key, expected in expected_budgets.items():
            if payload.get("review_budgets", {}).get(key) != expected:
                errors.append(f"{name}: review_budgets.{key} must be {expected}")
        conflict = payload.get("route_conflict", {})
        replacement_count = conflict.get("replacement_count")
        if conflict.get("replacement_limit") != 1:
            errors.append(f"{name}: route replacement limit must be 1")
        if not isinstance(replacement_count, int) or not 0 <= replacement_count <= 1:
            errors.append(f"{name}: route replacement count must be 0 or 1")
        if payload.get("gate_status") not in {"open", "passed", "failed", "waiting_for_user"}:
            errors.append(f"{name}: invalid gate_status")
        project = payload.get("project_disposition", {})
        if project.get("explicit_user_confirmation_required") is not True:
            errors.append(f"{name}: project deletion must require explicit user confirmation")
        if project.get("status") == "awaiting_deletion_decision":
            if payload.get("gate_status") != "waiting_for_user" or payload.get("mutations_blocked") is not True:
                errors.append(f"{name}: deletion decision state must stop mutations and wait for user")
        if payload.get("modeling_stage") not in MODELING_STAGES:
            errors.append(f"{name}: invalid modeling_stage")
        elif payload.get("current_stage") not in COARSE_STAGE_COMPATIBILITY[payload["modeling_stage"]]:
            errors.append(f"{name}: current_stage contradicts modeling_stage")
        rollback = payload.get("rollback", {})
        if not isinstance(rollback.get("required"), bool):
            errors.append(f"{name}: rollback.required must be bool")
        if payload.get("analysis_gate_status") not in {"open", "provisional", "passed", "failed"}:
            errors.append(f"{name}: invalid analysis_gate_status")
        progress = payload.get("part_progress", {})
        if any(not isinstance(progress.get(key), list) for key in (
            "active", "continuable", "paused", "needs_user_review"
        )):
            errors.append(f"{name}: invalid part_progress")
        elif set(progress.get("active", [])) & set(progress.get("paused", [])):
            errors.append(f"{name}: a part cannot be active and paused")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--allow-missing-validation", action="store_true")
    args = parser.parse_args()
    root = Path(args.artifact_dir).expanduser().resolve()
    errors: list[str] = []
    checked: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name in REQUIRED:
        path = root / name
        if not path.exists():
            if name == "validation_report.json" and args.allow_missing_validation:
                continue
            errors.append(f"missing artifact: {name}")
            continue
        checked.append(name)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{name}: invalid JSON: {exc}")
            continue
        payloads[name] = payload
        errors.extend(validate_artifact(name, payload))
    task_route = payloads.get("task_route.json", {})
    stage_state = payloads.get("stage_state.json", {})
    analysis = payloads.get("production_analysis.json", {})
    derivatives = payloads.get("reference_derivatives.json", {})
    graph = payloads.get("construction_graph.json", {})
    part_reviews = payloads.get("part_review_scores.json", {})
    lighting_plan = payloads.get("lighting_plan.json", {})
    modeling_stage = stage_state.get("modeling_stage", "analysis")
    stage_index = MODELING_STAGES.index(modeling_stage) if modeling_stage in MODELING_STAGES else 0

    for key in ("depth_map", "white_model_guide"):
        record = derivatives.get(key, {})
        if record.get("status") == "generated":
            path_value = record.get("path")
            candidate = Path(path_value) if isinstance(path_value, str) else Path()
            if isinstance(path_value, str) and not candidate.is_absolute():
                candidate = root / candidate
            if not isinstance(path_value, str) or not candidate.is_file():
                errors.append(f"reference_derivatives.json: generated {key} file is missing")
    has_reference_sources = bool(derivatives.get("source_references"))
    if modeling_stage != "analysis" and has_reference_sources:
        for key in ("depth_map", "white_model_guide"):
            if derivatives.get(key, {}).get("status") == "pending":
                errors.append(f"reference_derivatives.json: resolve {key} attempt before Blockout")

    if modeling_stage == "analysis":
        if stage_state.get("mutations_blocked") is not True:
            errors.append("stage_state.json: Blender mutations must remain blocked during analysis")
    elif modeling_stage == "blockout":
        minimum = analysis.get("minimum_viable_analysis", {})
        decisions = minimum.get("required_decisions", {})
        if analysis.get("status") not in {"provisional", "complete", "passed"}:
            errors.append("production_analysis.json: Blockout requires provisional analysis")
        if analysis.get("execution_allowed") is not True or analysis.get("execution_scope") not in {
            "reversible_blockout",
            "formal_production",
        }:
            errors.append("production_analysis.json: reversible Blockout is not approved")
        if minimum.get("status") != "passed" or not decisions or not all(decisions.values()):
            errors.append("production_analysis.json: minimum viable analysis has not passed")
        if analysis.get("critical_blockers"):
            errors.append("production_analysis.json: critical blockers prevent Blockout")
        if analysis.get("completion_scope") == "unresolved":
            errors.append("production_analysis.json: completion scope remains unresolved")
        if analysis.get("protected_scope", {}).get("status") != "passed":
            errors.append("production_analysis.json: protected scope is not approved")
        if analysis.get("real_scale", {}).get("status") not in {"estimated", "confirmed", "not_applicable"}:
            errors.append("production_analysis.json: Blockout scale strategy remains unresolved")
        if analysis.get("design_intent", {}).get("status") not in {"provisional", "resolved", "passed", "not_applicable"}:
            errors.append("production_analysis.json: Blockout design intent remains unresolved")
        if analysis.get("design_intent", {}).get("status") != "not_applicable" and not analysis.get("focal_hierarchy"):
            errors.append("production_analysis.json: Blockout focal hierarchy is empty")
        if graph.get("part_graph_status") not in {"provisional", "approved"}:
            errors.append("construction_graph.json: provisional Part Graph required for Blockout")
        if analysis.get("part_graph_status") not in {"provisional", "approved"}:
            errors.append("production_analysis.json: provisional Part Graph status is not recorded")
        if stage_state.get("analysis_gate_status") not in {"provisional", "passed"}:
            errors.append("stage_state.json: analysis gate must be provisional or passed")
        if stage_state.get("mutations_blocked") is True and stage_state.get("gate_status") != "waiting_for_user":
            errors.append("stage_state.json: Blockout is unexpectedly mutation-blocked")
    else:
        if analysis.get("status") not in {"complete", "passed"} or analysis.get("execution_allowed") is not True:
            errors.append("production_analysis.json: execution is not approved")
        if analysis.get("execution_scope") != "formal_production":
            errors.append("production_analysis.json: formal production scope is not approved")
        if analysis.get("critical_blockers"):
            errors.append("production_analysis.json: critical blockers remain")
        if analysis.get("blocking_unknowns"):
            errors.append("production_analysis.json: blocking unknowns remain")
        if analysis.get("completion_scope") == "unresolved":
            errors.append("production_analysis.json: completion scope remains unresolved")
        if analysis.get("real_scale", {}).get("status") not in {"estimated", "confirmed", "not_applicable"}:
            errors.append("production_analysis.json: real scale remains unresolved")
        section_statuses = {
            "design_intent": {"resolved", "passed", "not_applicable"},
            "camera_and_perspective": {"resolved", "passed", "not_applicable"},
            "primary_silhouette_and_proportion": {"resolved", "passed"},
            "spatial_and_support_structure": {"resolved", "passed", "not_applicable"},
            "lighting_analysis": {"resolved", "passed", "not_applicable"},
            "material_analysis": {"resolved", "passed", "not_applicable"},
        }
        for section, allowed in section_statuses.items():
            if analysis.get(section, {}).get("status") not in allowed:
                errors.append(f"production_analysis.json: {section} remains unresolved")
        if not analysis.get("object_partition_basis"):
            errors.append("production_analysis.json: object partition basis is empty")
        if not analysis.get("geometry_vs_shading"):
            errors.append("production_analysis.json: geometry-versus-shading decisions are empty")
        if analysis.get("design_intent", {}).get("status") != "not_applicable":
            if not analysis.get("focal_hierarchy"):
                errors.append("production_analysis.json: focal hierarchy is empty")
            if not analysis.get("depth_layers"):
                errors.append("production_analysis.json: depth layers are empty")
            if analysis.get("representation_budget", {}).get("status") not in {"resolved", "passed"}:
                errors.append("production_analysis.json: representation budget remains unresolved")
            if analysis.get("performance_budget", {}).get("status") not in {"resolved", "passed"}:
                errors.append("production_analysis.json: performance budget remains unresolved")
        hierarchy = analysis.get("form_hierarchy", {})
        for key in ("primary_masses", "structural_forms", "transition_forms"):
            if not hierarchy.get(key):
                errors.append(f"production_analysis.json: form_hierarchy.{key} is empty")
        if graph.get("part_graph_status") != "approved":
            errors.append("construction_graph.json: Part Graph must be approved before execution")
        if analysis.get("part_graph_status") != "approved":
            errors.append("production_analysis.json: Part Graph approval not recorded")
        if stage_state.get("analysis_gate_status") != "passed":
            errors.append("stage_state.json: analysis gate not passed")

    review_parts = {
        item.get("part_id"): item
        for item in part_reviews.get("parts", [])
        if isinstance(item, dict) and item.get("part_id")
    }
    progress = stage_state.get("part_progress", {})
    paused = set(str(value) for value in progress.get("paused", []))
    active = set(str(value) for value in progress.get("active", []))
    buildable_parts = {
        str(part.get("id")): part
        for part in graph.get("parts", [])
        if isinstance(part, dict) and part.get("role") in BUILDABLE_ROLES and part.get("id")
    }
    missing_review_parts = sorted(set(buildable_parts) - set(review_parts))
    if missing_review_parts:
        errors.append(
            "part_review_scores.json: missing construction parts " + ",".join(missing_review_parts)
        )

    required_review_stages: list[str] = []
    if stage_index >= MODELING_STAGES.index("topology_construction"):
        required_review_stages.extend(["analysis_readiness", "blockout"])
    if stage_index >= MODELING_STAGES.index("structural_forms"):
        required_review_stages.append("formal_topology")
    if stage_index >= MODELING_STAGES.index("functional_parts"):
        required_review_stages.append("structural_transition")
    if stage_index >= MODELING_STAGES.index("surfacing"):
        required_review_stages.append("systems")
    if stage_index >= MODELING_STAGES.index("lighting"):
        required_review_stages.append("surfacing")
    if modeling_stage == "final":
        required_review_stages.append("final")

    review_targets = {
        part_id
        for part_id, record in review_parts.items()
        if record.get("critical") is True
    } | active
    for part_id in sorted(review_targets):
        if part_id in paused and review_parts.get(part_id, {}).get("critical") is not True:
            continue
        stages = review_parts.get(part_id, {}).get("stages", {})
        for review_stage in required_review_stages:
            record = stages.get(review_stage, {})
            if record.get("disposition") == "deferred":
                continue
            if record.get("gate_clear") is not True:
                errors.append(
                    f"part_review_scores.json: {part_id}:{review_stage} is not clear to advance"
                )
    needs_user_review = set(str(value) for value in progress.get("needs_user_review", []))
    if not needs_user_review.issubset(paused):
        errors.append("stage_state.json: needs_user_review parts must also be paused")
    for part_id in sorted(needs_user_review):
        stages = review_parts.get(part_id, {}).get("stages", {})
        if not any(
            isinstance(record, dict) and record.get("disposition") == "needs_user_review"
            for record in stages.values()
        ):
            errors.append(f"stage_state.json: {part_id} has no matching review stop state")
    if stage_index > MODELING_STAGES.index("topology_construction"):
        buildable_roles = {"primary_form", "structural_part", "functional_detail", "decorative_detail", "cutter"}
        remaining_proxies = [
            str(part.get("id"))
            for part in graph.get("parts", [])
            if isinstance(part, dict)
            and part.get("role") in buildable_roles
            and part.get("blockout_proxy") is True
            and part.get("topology_status") not in {"deferred", "not_applicable"}
        ]
        if remaining_proxies:
            errors.append(
                "construction_graph.json: blockout proxies remain after topology conversion "
                + ",".join(remaining_proxies)
            )
        incomplete_topology = [
            str(part.get("id"))
            for part in graph.get("parts", [])
            if isinstance(part, dict)
            and part.get("role") in buildable_roles
            and part.get("form_level") in {"primary", "structural", "transition"}
            and part.get("topology_status") not in {"passed", "deferred", "not_applicable"}
        ]
        if incomplete_topology:
            errors.append(
                "construction_graph.json: formal topology incomplete "
                + ",".join(incomplete_topology)
            )
        for part in graph.get("parts", []):
            if not isinstance(part, dict) or part.get("topology_status") != "passed":
                continue
            topology_evidence = part.get("topology_evidence", {})
            if not topology_evidence.get("construction_operations"):
                errors.append(
                    f"construction_graph.json: topology operations missing for {part.get('id')}"
                )
            component_count = topology_evidence.get("connected_component_count")
            if not isinstance(component_count, int) or component_count < 1:
                errors.append(
                    f"construction_graph.json: connected component evidence missing for {part.get('id')}"
                )
            wireframe = topology_evidence.get("wireframe")
            if not isinstance(wireframe, str) or not Path(wireframe).is_file():
                errors.append(
                    f"construction_graph.json: part wireframe evidence missing for {part.get('id')}"
                )
        evidence = stage_state.get("review_evidence", {})
        evidence_paths: list[str] = []
        for key in ("front_clay", "side_clay", "top_clay", "hero_clay", "wireframe"):
            path_value = evidence.get(key)
            if not isinstance(path_value, str) or not Path(path_value).is_file():
                errors.append(f"stage_state.json: missing topology review evidence {key}")
            else:
                evidence_paths.append(str(Path(path_value).resolve()))
        if len(evidence_paths) != len(set(evidence_paths)):
            errors.append("stage_state.json: review evidence paths must be unique")
    if stage_index >= MODELING_STAGES.index("structural_forms"):
        if stage_state.get("form_gates", {}).get("primary_masses") != "passed":
            errors.append("stage_state.json: Primary Masses gate not passed")
        if stage_state.get("topology_gate_status") != "passed":
            errors.append("stage_state.json: formal topology gate not passed")
    if stage_index >= MODELING_STAGES.index("transition_forms"):
        if stage_state.get("form_gates", {}).get("structural_forms") != "passed":
            errors.append("stage_state.json: Structural Forms gate not passed")
    if stage_index >= MODELING_STAGES.index("functional_parts"):
        if stage_state.get("form_gates", {}).get("transition_forms") != "passed":
            errors.append("stage_state.json: Transition Forms gate not passed")
        if stage_state.get("topology_gate_status") != "passed":
            errors.append("stage_state.json: topology gate not passed before Functional Parts")
        missing_interfaces = [
            str(part.get("id"))
            for part in graph.get("parts", [])
            if isinstance(part, dict)
            and part.get("form_level") in {"functional", "detail"}
            and part.get("separation_policy") not in {"instance_source", "temporary_construction"}
            and not part.get("assembly_interfaces")
        ]
        if missing_interfaces:
            errors.append(
                "construction_graph.json: functional/detail interfaces missing "
                + ",".join(missing_interfaces)
            )
    if stage_index >= MODELING_STAGES.index("surface_details"):
        if stage_state.get("form_gates", {}).get("functional_parts") != "passed":
            errors.append("stage_state.json: Functional Parts gate not passed")
    if stage_index >= MODELING_STAGES.index("surfacing"):
        if stage_state.get("form_gates", {}).get("surface_details") != "passed":
            errors.append("stage_state.json: Surface Details gate not passed")
    if stage_index >= MODELING_STAGES.index("lighting"):
        if lighting_plan.get("analysis_status") != "passed":
            errors.append("lighting_plan.json: lighting analysis not passed")
        if lighting_plan.get("first_pass", {}).get("status") != "passed":
            errors.append("lighting_plan.json: gray-light gate not passed")
    strikes = [str(value) for value in stage_state.get("topology_rollback_strikes", [])]
    rollback = stage_state.get("rollback", {})
    if len(set(strikes)) >= 2:
        if rollback.get("required") is not True:
            errors.append("stage_state.json: two topology strikes require rollback")
        target = rollback.get("target")
        if target not in {"topology_construction", "structural_forms"}:
            errors.append("stage_state.json: invalid topology rollback target")
        elif stage_index > MODELING_STAGES.index(target):
            errors.append("stage_state.json: later-stage work cannot continue during topology rollback")
    reference_locked = "reference_locked_reconstruction" in task_route.get("classes", [])
    if reference_locked:
        reference_payloads: dict[str, dict[str, Any]] = {}
        for name, keys in REFERENCE_REQUIRED.items():
            path = root / name
            if not path.is_file():
                errors.append(f"missing reference artifact: {name}")
                continue
            checked.append(name)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{name}: invalid JSON: {exc}")
                continue
            reference_payloads[name] = payload
            if payload.get("schema_version") != SCHEMA_VERSION:
                errors.append(f"{name}: unsupported schema_version")
            for key in keys:
                if key not in payload:
                    errors.append(f"{name}: missing {key}")
        gate = reference_payloads.get("reference_gate.json", {})
        expected_stage_mapping = {
            "R0": "analysis",
            "R1": "blockout",
            "R2": "primary_surface",
            "R3": "surfacing_lighting",
            "R4": "final",
        }
        if gate.get("state_authority") != "stage_state.json":
            errors.append("reference_gate.json: stage_state.json must own state")
        if gate.get("stage_mapping") != expected_stage_mapping:
            errors.append("reference_gate.json: invalid production stage mapping")
        scoring = gate.get("blockout_scoring", {})
        expected_maxima = {
            "primary_form_proportion": 30,
            "spatial_layout_connectivity": 25,
            "directional_structures": 25,
            "structural_contact_support_clearance": 20,
        }
        if scoring.get("component_maxima") != expected_maxima:
            errors.append("reference_gate.json: invalid model-body component maxima")
        if scoring.get("emergency_rebuild_threshold") != 40:
            errors.append("reference_gate.json: invalid emergency rebuild threshold")
        if scoring.get("stop_after_consecutive_under_threshold") != 2:
            errors.append("reference_gate.json: invalid consecutive failure stop count")
        if scoring.get("disposition") == "awaiting_deletion_decision":
            if gate.get("gate_status") != "waiting_for_user":
                errors.append("reference_gate.json: deletion decision state must wait for user")
            if stage_state.get("mutations_blocked") is not True:
                errors.append("stage_state.json: mutations must stop after the second low score")
        gate_project = gate.get("project_disposition", {})
        if gate_project.get("status") != stage_state.get("project_disposition", {}).get("status"):
            errors.append("reference_gate.json: project disposition does not match stage_state.json")
        current_stage = stage_state.get("current_stage")
        if stage_index >= MODELING_STAGES.index("topology_construction"):
            score = scoring.get("current_score")
            if not isinstance(score, (int, float)) or score < 40:
                errors.append("reference_gate.json: model-body score must be at least 40 to advance")
            if scoring.get("disposition") != "continue":
                errors.append("reference_gate.json: model-body state is not clear to continue")
        if stage_state.get("current_stage") == "final":
            gate_path = root / "reference_gate.json"
            if gate_path.is_file():
                gate = json.loads(gate_path.read_text(encoding="utf-8"))
                if gate.get("current_gate") != "R4" or gate.get("gate_status") != "passed":
                    errors.append("reference_gate.json: final stage requires passed R4")
                if gate.get("unresolved_blockers"):
                    errors.append("reference_gate.json: unresolved blockers at final stage")
                failed_gate_checks = [
                    item.get("id") for item in gate.get("checks", [])
                    if not isinstance(item, dict) or item.get("status") != "passed" or not item.get("evidence")
                ]
                if failed_gate_checks:
                    errors.append(
                        "reference_gate.json: final stage has incomplete checks "
                        + ",".join(str(value) for value in failed_gate_checks)
                    )
                for evidence in gate.get("evidence_paths", []):
                    if not Path(str(evidence)).is_file():
                        errors.append(f"reference_gate.json: missing evidence {evidence}")
            validation = payloads.get("validation_report.json", {})
            if validation.get("generator") != "blender-geometry-validation/scripts/validate_scene.py":
                errors.append("validation_report.json: final reference task requires raw validator generator identity")
            if validation.get("not_evaluated"):
                errors.append("validation_report.json: final reference task has not_evaluated checks")
            observation_path = root / "reference_observation.json"
            graph = payloads.get("construction_graph.json", {})
            if observation_path.is_file():
                observation = json.loads(observation_path.read_text(encoding="utf-8"))
                p0_ids = {
                    item.get("id") for item in observation.get("observations", [])
                    if isinstance(item, dict)
                    and item.get("priority") == "P0"
                    and item.get("production_domain") == "geometry"
                }
                graph_parts = {
                    item.get("id"): item for item in graph.get("parts", [])
                    if isinstance(item, dict) and item.get("id")
                }
                for part_id in sorted(p0_ids):
                    if part_id not in graph_parts:
                        errors.append(f"construction_graph.json: missing P0 part {part_id}")
                    elif not graph_parts[part_id].get("requirements"):
                        errors.append(f"construction_graph.json: P0 part {part_id} has no requirements")
    result = {"status": "PASS" if not errors else "FAIL", "checked": checked, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
