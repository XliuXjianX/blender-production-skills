#!/usr/bin/env python3
"""Create backward-compatible reference reconstruction artifact templates."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from PIL import Image


SCHEMA_VERSION = "1.0"


def _source(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        width, height = image.size
    return {
        "path": str(path.resolve()),
        "width": width,
        "height": height,
        "aspect_ratio": width / max(height, 1),
    }


def build(
    reference_paths: list[Path],
    deliverable: str = "unresolved",
) -> dict[str, dict[str, object]]:
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    sources = [_source(path) for path in reference_paths]
    primary = sources[0]
    return {
        "reference_derivatives.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "source_references": [str(path.resolve()) for path in reference_paths],
            "generation_capability": "unknown",
            "attempt_limit": 1,
            "blocking": False,
            "authority": "auxiliary_hypothesis_only",
            "depth_map": {
                "status": "pending",
                "attempts": 0,
                "path": None,
                "method": None,
            },
            "white_model_guide": {
                "status": "pending",
                "attempts": 0,
                "path": None,
                "method": None,
            },
        },
        "reference_observation.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "reference_files": sources,
            "purpose": "reference_guided_spatial_reconstruction",
            "observations": [],
            "uncertainty_register": [],
            "visual_priorities": [],
        },
        "spatial_hypothesis.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "deliverable_scope": deliverable,
            "scene_kind": "unresolved",
            "coordinate_frame": {
                "up_axis": "Z",
                "forward_axis": None,
                "lateral_axis": None,
                "ground_elevation": None,
                "origin_policy": "unresolved",
                "evidence": [],
            },
            "camera_context": {
                "region_id": None,
                "inside_outside": "unresolved",
                "height_range": [],
                "lateral_bias": "unresolved",
                "view_direction": "unresolved",
                "lock_state": "provisional",
                "revision": 0,
                "confidence": 0.0,
                "evidence": [],
            },
            "axes": [],
            "regions": [],
            "connections": [],
            "occlusion_order": [],
            "scale_anchors": [],
            "alternative_hypotheses": [],
            "spatial_invariants": [],
            "hypothesis_revision": 0,
            "directional_structures": [],
            "blockout_views": [],
        },
        "camera_match.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "reference_size": [primary["width"], primary["height"]],
            "projection_hypotheses": [],
            "line_families": [],
            "lens_distortion_hypotheses": [],
            "horizon_y_normalized": None,
            "vanishing_evidence": [],
            "anchors": [],
            "negative_space": {},
            "lock_state": "provisional",
            "revision": 0,
            "tolerances": {
                "aspect_ratio_error": 0.01,
                "anchor_center_warn": 0.02,
                "anchor_center_fail": 0.04,
                "size_warn": 0.05,
                "size_fail": 0.10,
            },
        },
        "material_hypotheses.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "materials": [],
            "global_aging_causes": [],
            "wetness_policy": "unresolved",
        },
        "visual_targets.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "attention_order": [],
            "luminance_zones": [],
            "palette": [],
            "light_sources": [],
            "depth_layers": [],
            "photographic_treatment": {},
            "simplification_limits": [],
        },
        "reference_gate.json": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "state_authority": "stage_state.json",
            "stage_mapping": {
                "R0": "analysis",
                "R1": "blockout",
                "R2": "primary_surface",
                "R3": "surfacing_lighting",
                "R4": "final",
            },
            "current_gate": "R0",
            "gate_status": "open",
            "checks": [
                {"id": "p0_observation_completeness", "status": "open", "evidence": []},
                {"id": "spatial_hypothesis_completeness", "status": "open", "evidence": []},
                {"id": "camera_evidence", "status": "open", "evidence": []},
                {"id": "blocking_uncertainty", "status": "open", "evidence": []},
                {"id": "camera_overlay", "status": "open", "evidence": []},
                {"id": "negative_space_and_occlusion", "status": "open", "evidence": []},
                {"id": "portal_and_region_connectivity", "status": "open", "evidence": []},
                {"id": "camera_spatial_consistency", "status": "open", "evidence": []},
                {"id": "cross_view_blockout", "status": "open", "evidence": []},
                {"id": "directional_structure_skeleton", "status": "open", "evidence": []},
                {"id": "blockout_similarity_score", "status": "open", "evidence": []},
                {"id": "p0_primary_geometry", "status": "open", "evidence": []},
                {"id": "part_graph_complete", "status": "open", "evidence": []},
                {"id": "blockout_replaced_by_formal_topology", "status": "open", "evidence": []},
                {"id": "structural_forms", "status": "open", "evidence": []},
                {"id": "transition_forms", "status": "open", "evidence": []},
                {"id": "assembly_interfaces", "status": "open", "evidence": []},
                {"id": "real_bevel_geometry", "status": "open", "evidence": []},
                {"id": "wireframe_acceptance", "status": "open", "evidence": []},
                {"id": "continuous_connections_and_smoothing", "status": "open", "evidence": []},
                {"id": "semantic_material_identity", "status": "open", "evidence": []},
                {"id": "causal_aging_and_wetness", "status": "open", "evidence": []},
                {"id": "lighting_and_depth", "status": "open", "evidence": []},
                {"id": "final_overlay", "status": "open", "evidence": []},
                {"id": "final_semantic_review", "status": "open", "evidence": []},
            ],
            "evidence_paths": [],
            "camera_revision": 0,
            "approvals": [],
            "blockout_scoring": {
                "schema_version": SCHEMA_VERSION,
                "scale": 100,
                "emergency_rebuild_threshold": 40,
                "stop_after_consecutive_under_threshold": 2,
                "attempt_index": 0,
                "current_score": None,
                "raw_score": None,
                "consecutive_under_40": 0,
                "disposition": "not_scored",
                "component_maxima": {
                    "primary_form_proportion": 30,
                    "spatial_layout_connectivity": 25,
                    "directional_structures": 25,
                    "structural_contact_support_clearance": 20,
                },
                "component_scores": {},
                "history": [],
            },
            "router_decision": {
                "required": False,
                "owner": "blender-production-router",
                "action": None,
                "attempt_id": None,
                "applied": False,
            },
            "project_disposition": {
                "status": "active",
                "explicit_user_confirmation_required": True,
                "deletion_candidate_paths": [],
                "task_owned_paths": [],
                "confirmation": None,
            },
            "unresolved_blockers": [
                "Complete minimum reference analysis before reversible Blockout"
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", action="append", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--deliverable",
        choices=["asset", "animated_asset", "environment", "shot", "unresolved"],
        default="unresolved",
    )
    args = parser.parse_args()
    references = [Path(value).expanduser().resolve() for value in args.reference]
    missing = [str(path) for path in references if not path.is_file()]
    if missing:
        raise SystemExit("Missing reference files: " + ", ".join(missing))
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, payload in build(references, deliverable=args.deliverable).items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        paths[name] = str(path)
    print(json.dumps({"status": "ok", "artifacts": paths}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
