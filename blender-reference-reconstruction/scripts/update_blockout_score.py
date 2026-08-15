#!/usr/bin/env python3
"""Record R1 evidence and request a Router-owned state transition."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
THRESHOLD = 40
STOP_AFTER = 2
COMPONENT_MAXIMA = {
    "primary_form_proportion": 30,
    "spatial_layout_connectivity": 25,
    "directional_structures": 25,
    "structural_contact_support_clearance": 20,
}
LOW_SCORE_BLOCKER_PREFIX = "R1_BLOCKOUT_SCORE_UNDER_40:"


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _unique_paths(values: list[str] | None, require_files: bool = False) -> list[str]:
    result: list[str] = []
    for value in values or []:
        path = Path(value).expanduser().resolve()
        if require_files and not path.is_file():
            raise FileNotFoundError(path)
        normalized = str(path)
        if normalized not in result:
            result.append(normalized)
    return result


def _set_check(gate: dict[str, Any], check_id: str, status: str, evidence: list[str]) -> None:
    checks = gate.setdefault("checks", [])
    for item in checks:
        if isinstance(item, dict) and item.get("id") == check_id:
            item["status"] = status
            item["evidence"] = list(evidence)
            return
    checks.append({"id": check_id, "status": status, "evidence": list(evidence)})


def _remove_low_score_blockers(gate: dict[str, Any]) -> None:
    gate["unresolved_blockers"] = [
        value
        for value in gate.get("unresolved_blockers", [])
        if not str(value).startswith(LOW_SCORE_BLOCKER_PREFIX)
    ]


def _invalidate_spatial_blockout(root: Path) -> None:
    spatial_path = root / "spatial_hypothesis.json"
    spatial = _read(spatial_path)
    spatial["hypothesis_revision"] = int(spatial.get("hypothesis_revision", 0)) + 1
    for view in spatial.get("blockout_views", []):
        if isinstance(view, dict) and view.get("status") == "passed":
            view["status"] = "stale"
    _write_atomic(spatial_path, spatial)


def record_score(
    artifact_dir: Path,
    attempt_id: str,
    component_scores: dict[str, int],
    evidence: list[str],
    root_causes: list[str] | None = None,
    critical_directional_failure: bool = False,
    rebuild_from_attempt: str | None = None,
    task_owned_paths: list[str] | None = None,
    deletion_candidate_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = artifact_dir.expanduser().resolve()
    gate_path = root / "reference_gate.json"
    gate = _read(gate_path)
    scoring = gate.setdefault("blockout_scoring", {})
    existing_disposition = gate.get("project_disposition", {})
    pending_decision = gate.get("router_decision", {})

    if existing_disposition.get("status") == "awaiting_deletion_decision":
        raise RuntimeError("Work is stopped pending the user's project-deletion decision")
    if pending_decision.get("required") and not pending_decision.get("applied"):
        raise RuntimeError("Apply the previous score through the Router before recording another score")
    history = scoring.setdefault("history", [])
    if any(isinstance(item, dict) and item.get("attempt_id") == attempt_id for item in history):
        raise ValueError(f"Duplicate blockout attempt_id: {attempt_id}")
    previous_low = next(
        (item for item in reversed(history) if isinstance(item, dict) and int(item.get("score", 100)) < THRESHOLD),
        None,
    )
    if scoring.get("disposition") == "rebuild_required":
        expected = previous_low.get("attempt_id") if previous_low else None
        if rebuild_from_attempt != expected:
            raise ValueError(
                "A new full rebuild must identify the failed attempt with --rebuild-from-attempt; "
                "re-rendering the same blockout does not count as a second attempt"
            )

    normalized_scores: dict[str, int] = {}
    for name, maximum in COMPONENT_MAXIMA.items():
        value = component_scores.get(name)
        if not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"{name} must be an integer from 0 to {maximum}")
        normalized_scores[name] = value
    evidence_paths = _unique_paths(evidence, require_files=True)
    if not evidence_paths:
        raise ValueError("At least one existing comparison-evidence file is required")
    owned_paths = _unique_paths(task_owned_paths)
    candidate_paths = _unique_paths(deletion_candidate_paths)
    disposition = dict(existing_disposition)
    disposition["explicit_user_confirmation_required"] = True
    disposition["task_owned_paths"] = list(
        dict.fromkeys(disposition.get("task_owned_paths", []) + owned_paths)
    )
    disposition["deletion_candidate_paths"] = list(
        dict.fromkeys(disposition.get("deletion_candidate_paths", []) + candidate_paths)
    )
    disposition["confirmation"] = None

    raw_score = sum(normalized_scores.values())
    score = min(raw_score, THRESHOLD - 1) if critical_directional_failure else raw_score
    attempt = {
        "attempt_index": int(scoring.get("attempt_index", 0)) + 1,
        "attempt_id": attempt_id,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": score,
        "raw_score": raw_score,
        "component_scores": normalized_scores,
        "critical_directional_failure": bool(critical_directional_failure),
        "rebuild_from_attempt": rebuild_from_attempt,
        "evidence": evidence_paths,
        "root_causes": list(root_causes or []),
    }
    history.append(attempt)
    scoring.update(
        {
            "schema_version": SCHEMA_VERSION,
            "scale": 100,
            "emergency_rebuild_threshold": THRESHOLD,
            "stop_after_consecutive_under_threshold": STOP_AFTER,
            "attempt_index": attempt["attempt_index"],
            "current_score": score,
            "raw_score": raw_score,
            "component_maxima": dict(COMPONENT_MAXIMA),
            "component_scores": normalized_scores,
        }
    )
    gate["current_gate"] = "R1"
    gate["evidence_paths"] = list(dict.fromkeys(gate.get("evidence_paths", []) + evidence_paths))
    if score < THRESHOLD:
        consecutive = int(scoring.get("consecutive_under_40", 0)) + 1
        scoring["consecutive_under_40"] = consecutive
        _set_check(gate, "blockout_similarity_score", "failed", evidence_paths)
        _set_check(
            gate,
            "directional_structure_skeleton",
            "failed" if critical_directional_failure else "open",
            evidence_paths if critical_directional_failure else [],
        )
        _remove_low_score_blockers(gate)
        blocker = f"{LOW_SCORE_BLOCKER_PREFIX}{score}:attempt={attempt_id}"
        gate.setdefault("unresolved_blockers", []).append(blocker)
        gate["current_gate"] = "R1"
        if consecutive >= STOP_AFTER:
            action = "stop_and_request_deletion_decision"
            scoring["disposition"] = "awaiting_deletion_decision"
            disposition["status"] = "awaiting_deletion_decision"
            gate["gate_status"] = "waiting_for_user"
        else:
            action = "rebuild_required"
            scoring["disposition"] = "rebuild_required"
            disposition["status"] = "rebuild_required"
            gate["gate_status"] = "failed"
            _invalidate_spatial_blockout(root)
    else:
        action = "continue_r1_checks"
        scoring["consecutive_under_40"] = 0
        scoring["disposition"] = "continue"
        disposition["status"] = "active"
        gate["gate_status"] = "open"
        _remove_low_score_blockers(gate)
        _set_check(gate, "blockout_similarity_score", "passed", evidence_paths)

    gate["router_decision"] = {
        "required": True,
        "owner": "blender-production-router",
        "action": action,
        "attempt_id": attempt_id,
        "applied": False,
        "project_disposition_patch": disposition,
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "action": action,
        "score": score,
        "raw_score": raw_score,
        "consecutive_under_40": scoring["consecutive_under_40"],
        "attempt_id": attempt_id,
        "project_disposition": disposition,
        "automatic_deletion_performed": False,
        "router_state_apply_required": True,
    }
    if action == "stop_and_request_deletion_decision":
        result["user_decision_required"] = {
            "question": "白模连续两次低于 40 分。是否删除本任务的整个项目？",
            "answer_required": "explicit_yes_or_no",
            "deletion_candidate_paths": disposition.get("deletion_candidate_paths", []),
            "protected_objects": [],
        }
        result["user_decision_required"]["question"] = (
            "连续两次白模评分低于 40 分。是否删除本任务的整个项目？"
        )
    _write_atomic(gate_path, gate)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--primary-form-proportion", required=True, type=int)
    parser.add_argument("--spatial-layout-connectivity", required=True, type=int)
    parser.add_argument("--directional-structures", required=True, type=int)
    parser.add_argument("--structural-contact-support-clearance", required=True, type=int)
    parser.add_argument("--evidence", action="append", required=True)
    parser.add_argument("--root-cause", action="append")
    parser.add_argument("--critical-directional-failure", action="store_true")
    parser.add_argument("--rebuild-from-attempt")
    parser.add_argument("--task-owned-path", action="append")
    parser.add_argument("--deletion-candidate", action="append")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = record_score(
        Path(args.artifact_dir),
        args.attempt_id,
        {
            "primary_form_proportion": args.primary_form_proportion,
            "spatial_layout_connectivity": args.spatial_layout_connectivity,
            "directional_structures": args.directional_structures,
            "structural_contact_support_clearance": args.structural_contact_support_clearance,
        },
        args.evidence,
        args.root_cause,
        args.critical_directional_failure,
        args.rebuild_from_attempt,
        args.task_owned_path,
        args.deletion_candidate,
    )
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
