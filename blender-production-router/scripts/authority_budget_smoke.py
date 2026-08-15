#!/usr/bin/env python3
"""Exercise the single-authority and bounded-retry production state."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load(path: Path, name: str):
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
    router = _load(SCRIPT_DIR / "route_blender_task.py", "authority_router")
    decisions = _load(SCRIPT_DIR / "apply_validation_decision.py", "authority_decisions")
    state = router._stage_state([])

    request = {
        "symptom": "stair direction is reversed",
        "evidence": ["side_view_001.png"],
        "likely_owner": "blender-procedural-systems",
        "affected_part": "stair_flight",
        "recommended_rollback_target": "blockout",
        "geometry_revision": "geo-001",
    }
    first_registered = decisions.register_local_repair_request(state, request)
    duplicate_registered = decisions.register_local_repair_request(state, request)
    decisions.record_route_replacement(state, "native component prerequisite failed")
    second_replacement_refused = False
    try:
        decisions.record_route_replacement(state, "same conflict under another name")
    except RuntimeError:
        second_replacement_refused = True

    validator_source = (
        SCRIPT_DIR.parent.parent
        / "blender-geometry-validation"
        / "scripts"
        / "validate_scene.py"
    ).read_text(encoding="utf-8")
    checks = {
        "router_owns_state": state["authority"]["state_owner"] == "blender-production-router",
        "validator_cannot_reroute": state["authority"]["validator_can_reroute"] is False,
        "specialist_cannot_restart_analysis": state["authority"]["specialist_can_restart_analysis"] is False,
        "budgets_match_contract": state["review_budgets"] == {
            "minimum_analysis_reviews": 2,
            "technical_repairs_per_stage": 3,
            "part_reviews_per_part_stage": 2,
            "consecutive_white_model_under_40_stop": 2,
            "route_candidate_replacements": 1,
            "unchanged_geometry_render_counts_as_attempt": False,
        },
        "first_local_repair_registered": first_registered,
        "unchanged_geometry_duplicate_ignored": not duplicate_registered and len(state["local_repair_requests"]) == 1,
        "one_route_replacement_only": state["route_conflict"]["replacement_count"] == 1 and second_replacement_refused,
        "validator_has_no_state_mutation_cli": "--update-stage-state" not in validator_source,
    }
    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "state": state,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
