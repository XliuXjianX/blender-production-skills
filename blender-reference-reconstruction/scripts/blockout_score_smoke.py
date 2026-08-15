#!/usr/bin/env python3
"""Exercise the R1 model-body score rebuild and stop state machine."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
ROUTER_SCRIPT_DIR = SCRIPT_DIR.parent.parent / "blender-production-router" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepare(root: Path, init, reference: Path) -> None:
    artifacts = init.build([reference], deliverable="environment")
    artifacts["camera_match.json"].update({"lock_state": "locked", "revision": 7})
    artifacts["spatial_hypothesis.json"]["camera_context"].update(
        {"lock_state": "locked", "revision": 7}
    )
    artifacts["spatial_hypothesis.json"]["blockout_views"] = [
        {"type": "camera", "path": str(reference), "status": "passed"},
        {"type": "top", "path": str(reference), "status": "passed"},
        {"type": "side", "path": str(reference), "status": "passed"},
    ]
    artifacts["stage_state.json"] = {
        "schema_version": "1.0",
        "current_stage": "blockout",
        "modeling_stage": "blockout",
        "iteration": 0,
        "visual_gate": "blockout",
        "gate_status": "open",
        "protected_objects": ["USER_CAMERA", "USER_REFERENCE"],
        "checkpoints": [],
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
        "allowed_operations": [],
        "project_disposition": {
            "status": "active",
            "explicit_user_confirmation_required": True,
            "deletion_candidate_paths": [],
            "task_owned_paths": [],
            "confirmation": None,
        },
        "authority": {
            "state_owner": "blender-production-router",
            "design_owner": "blender-scene-design",
            "reference_owner": "blender-reference-reconstruction",
            "validator_can_reroute": False,
            "specialist_can_restart_analysis": False,
        },
    }
    for name, payload in artifacts.items():
        (root / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _apply_router_decision(root: Path, apply_module) -> dict:
    return apply_module.apply(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    init = _load("blockout_score_init", SCRIPT_DIR / "init_reference_artifacts.py")
    scorer = _load("blockout_score_update", SCRIPT_DIR / "update_blockout_score.py")
    applier = _load(
        "blockout_score_router_apply",
        ROUTER_SCRIPT_DIR / "apply_blockout_score_decision.py",
    )
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="blender_blockout_score_") as temp:
        base = Path(temp)
        reference = base / "evidence.png"
        Image.new("RGB", (128, 72), (48, 48, 48)).save(reference)

        stop_root = base / "stop-case"
        stop_root.mkdir()
        _prepare(stop_root, init, reference)
        project = stop_root / "task-project"
        project.mkdir()
        sentinel = project / "must_not_be_deleted.txt"
        sentinel.write_text("protected by explicit confirmation", encoding="utf-8")
        stage_before_reference_score = (stop_root / "stage_state.json").read_text(encoding="utf-8")
        gate_before_reference_score = json.loads(
            (stop_root / "reference_gate.json").read_text(encoding="utf-8")
        )
        first = scorer.record_score(
            stop_root,
            "attempt-1",
            {
                "primary_form_proportion": 25,
                "spatial_layout_connectivity": 20,
                "directional_structures": 21,
                "structural_contact_support_clearance": 15,
            },
            [str(reference)],
            ["railing bends away from the supported platform edge"],
            critical_directional_failure=True,
            task_owned_paths=[str(project)],
            deletion_candidate_paths=[str(project)],
        )
        stage_unchanged_by_reference = (
            (stop_root / "stage_state.json").read_text(encoding="utf-8")
            == stage_before_reference_score
        )
        gate_disposition_unchanged_by_reference = (
            json.loads((stop_root / "reference_gate.json").read_text(encoding="utf-8"))
            .get("project_disposition")
            == gate_before_reference_score.get("project_disposition")
        )
        premature_score_blocked = False
        try:
            scorer.record_score(
                stop_root,
                "premature-attempt",
                {
                    "primary_form_proportion": 30,
                    "spatial_layout_connectivity": 25,
                    "directional_structures": 25,
                    "structural_contact_support_clearance": 20,
                },
                [str(reference)],
                rebuild_from_attempt="attempt-1",
            )
        except RuntimeError:
            premature_score_blocked = True
        _apply_router_decision(stop_root, applier)
        camera_after_first = json.loads((stop_root / "camera_match.json").read_text(encoding="utf-8"))
        spatial_after_first = json.loads((stop_root / "spatial_hypothesis.json").read_text(encoding="utf-8"))
        second = scorer.record_score(
            stop_root,
            "attempt-2",
            {
                "primary_form_proportion": 10,
                "spatial_layout_connectivity": 8,
                "directional_structures": 7,
                "structural_contact_support_clearance": 6,
            },
            [str(reference)],
            ["rebuilt stair still ascends toward the wrong landing"],
            rebuild_from_attempt="attempt-1",
            task_owned_paths=[str(project)],
            deletion_candidate_paths=[str(project)],
        )
        _apply_router_decision(stop_root, applier)
        stage_after_second = json.loads((stop_root / "stage_state.json").read_text(encoding="utf-8"))
        third_blocked = False
        try:
            scorer.record_score(
                stop_root,
                "attempt-3",
                {
                    "primary_form_proportion": 30,
                    "spatial_layout_connectivity": 25,
                    "directional_structures": 25,
                    "structural_contact_support_clearance": 20,
                },
                [str(reference)],
                rebuild_from_attempt="attempt-2",
            )
        except RuntimeError:
            third_blocked = True

        reset_root = base / "reset-case"
        reset_root.mkdir()
        _prepare(reset_root, init, reference)
        low = scorer.record_score(
            reset_root,
            "reset-attempt-1",
            {
                "primary_form_proportion": 10,
                "spatial_layout_connectivity": 9,
                "directional_structures": 8,
                "structural_contact_support_clearance": 7,
            },
            [str(reference)],
        )
        _apply_router_decision(reset_root, applier)
        recovered = scorer.record_score(
            reset_root,
            "reset-attempt-2",
            {
                "primary_form_proportion": 22,
                "spatial_layout_connectivity": 18,
                "directional_structures": 18,
                "structural_contact_support_clearance": 14,
            },
            [str(reference)],
            rebuild_from_attempt="reset-attempt-1",
        )
        _apply_router_decision(reset_root, applier)
        reset_gate = json.loads((reset_root / "reference_gate.json").read_text(encoding="utf-8"))

        checks = {
            "critical_direction_caps_score_at_39": first["score"] == 39 and first["raw_score"] > 39,
            "reference_score_does_not_mutate_router_state": stage_unchanged_by_reference,
            "reference_score_does_not_mutate_production_mirror": gate_disposition_unchanged_by_reference,
            "router_must_apply_before_next_score": premature_score_blocked,
            "first_low_score_requires_rebuild": first["action"] == "rebuild_required" and first["consecutive_under_40"] == 1,
            "low_model_score_preserves_user_camera": camera_after_first.get("lock_state") == "locked" and camera_after_first.get("revision") == 7,
            "low_model_score_invalidates_spatial_views": all(item.get("status") == "stale" for item in spatial_after_first.get("blockout_views", [])),
            "second_consecutive_low_score_stops": second["action"] == "stop_and_request_deletion_decision" and second["consecutive_under_40"] == 2,
            "stopped_state_blocks_mutation": stage_after_second.get("mutations_blocked") is True and stage_after_second.get("gate_status") == "waiting_for_user",
            "deletion_requires_user_decision": second.get("user_decision_required", {}).get("answer_required") == "explicit_yes_or_no",
            "automatic_deletion_never_occurs": sentinel.is_file() and second.get("automatic_deletion_performed") is False,
            "work_cannot_continue_while_waiting": third_blocked,
            "passing_rebuild_resets_low_counter": low["consecutive_under_40"] == 1 and recovered["consecutive_under_40"] == 0,
            "score_does_not_auto_pass_r1": reset_gate.get("gate_status") == "open" and recovered["action"] == "continue_r1_checks",
        }
    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "check_count": len(checks),
        "checks": checks,
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
