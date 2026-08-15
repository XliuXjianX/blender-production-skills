#!/usr/bin/env python3
"""Shared mutation API for Router-owned production state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTER_OWNER = "blender-production-router"
REFERENCE_OWNER = "blender-reference-reconstruction"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def assert_router_owned(stage_state: dict[str, Any]) -> None:
    authority = stage_state.get("authority", {})
    if authority.get("state_owner") != ROUTER_OWNER:
        raise ValueError("stage_state is not owned by blender-production-router")


def _set_membership(values: list[str], part_id: str, include: bool) -> list[str]:
    unique = [value for value in dict.fromkeys(str(item) for item in values) if value != part_id]
    if include:
        unique.append(part_id)
    return unique


def update_part_progress(
    stage_state: dict[str, Any],
    part_id: str,
    critical: bool,
    disposition: str,
    gate_clear: bool,
) -> None:
    """Apply a local part review without changing the route or deletion policy."""

    assert_router_owned(stage_state)
    progress = stage_state.setdefault(
        "part_progress",
        {"active": [], "continuable": [], "paused": [], "needs_user_review": []},
    )
    for key in ("active", "continuable", "paused", "needs_user_review"):
        if not isinstance(progress.get(key), list):
            progress[key] = []

    if gate_clear:
        progress["continuable"] = _set_membership(progress["continuable"], part_id, True)
        progress["paused"] = _set_membership(progress["paused"], part_id, False)
        progress["needs_user_review"] = _set_membership(
            progress["needs_user_review"], part_id, False
        )
    else:
        progress["active"] = _set_membership(progress["active"], part_id, False)
        progress["continuable"] = _set_membership(progress["continuable"], part_id, False)
        progress["paused"] = _set_membership(progress["paused"], part_id, True)
        progress["needs_user_review"] = _set_membership(
            progress["needs_user_review"],
            part_id,
            disposition == "needs_user_review",
        )

    if (
        disposition == "needs_user_review"
        and critical
        and stage_state.get("visual_gate") in {"blockout", "primary_surface", "systems", "final"}
    ):
        stage_state["gate_status"] = "waiting_for_user"
        stage_state["mutations_blocked"] = True
        stage_state["allowed_operations"] = [
            "inspect evidence",
            "review the failed critical part",
            "record the user decision",
        ]


def apply_blockout_score_decision(
    stage_state: dict[str, Any],
    gate: dict[str, Any],
    protected_objects: list[str] | None = None,
) -> dict[str, Any]:
    """Apply the latest reference score to Router state and return the decision."""

    assert_router_owned(stage_state)
    if gate.get("state_authority") != "stage_state.json":
        raise ValueError("reference_gate does not declare stage_state.json as authority")

    scoring = gate.get("blockout_scoring", {})
    history = scoring.get("history", [])
    if not history or not isinstance(history[-1], dict):
        raise ValueError("reference_gate has no recorded blockout score")
    attempt = history[-1]
    score = float(scoring.get("current_score", attempt.get("score", 0)))
    consecutive = int(scoring.get("consecutive_under_40", 0))
    decision = gate.get("router_decision", {})
    disposition = decision.get("project_disposition_patch", gate.get("project_disposition", {}))
    if not isinstance(disposition, dict):
        raise ValueError("reference_gate Router decision has an invalid project disposition patch")
    status = str(disposition.get("status", "active"))

    stage_state["current_stage"] = "blockout"
    stage_state["modeling_stage"] = "blockout"
    stage_state["visual_gate"] = "blockout"
    stage_state["iteration"] = int(stage_state.get("iteration", 0)) + 1
    stage_state["project_disposition"] = {
        **stage_state.get("project_disposition", {}),
        **disposition,
    }
    if protected_objects is not None:
        stage_state["protected_objects"] = list(dict.fromkeys(str(item) for item in protected_objects))

    if score < 40 and consecutive >= 2:
        action = "stop_and_request_deletion_decision"
        stage_state["gate_status"] = "waiting_for_user"
        stage_state["mutations_blocked"] = True
        stage_state["allowed_operations"] = [
            "inventory exact task-owned project paths",
            "preserve failed evidence",
            "ask the user whether to delete the task project",
        ]
    elif score < 40:
        action = "rebuild_required"
        stage_state["gate_status"] = "failed"
        stage_state["mutations_blocked"] = False
        stage_state["allowed_operations"] = [
            "re-audit model proportions and spatial hypothesis",
            "replace task-owned blockout geometry",
            "rebuild directional semantic skeletons",
            "render unique R1 evidence",
        ]
    else:
        action = "continue_r1_checks"
        stage_state["gate_status"] = "open"
        stage_state["mutations_blocked"] = False
        stage_state["allowed_operations"] = [
            "complete remaining R1 semantic and cross-view checks",
        ]

    stage_state.setdefault("router_decisions", []).append(
        {
            "type": "blockout_score",
            "attempt_id": attempt.get("attempt_id"),
            "score": score,
            "consecutive_under_40": consecutive,
            "action": action,
        }
    )
    gate["project_disposition"] = dict(stage_state["project_disposition"])
    result: dict[str, Any] = {
        "action": action,
        "attempt_id": attempt.get("attempt_id"),
        "score": score,
        "consecutive_under_40": consecutive,
        "project_disposition": stage_state["project_disposition"],
        "automatic_deletion_performed": False,
    }
    if action == "stop_and_request_deletion_decision":
        result["user_decision_required"] = {
            "question": "连续两次白模评分低于 40 分。是否删除本任务的整个项目？",
            "answer_required": "explicit_yes_or_no",
            "deletion_candidate_paths": stage_state["project_disposition"].get(
                "deletion_candidate_paths", []
            ),
            "protected_objects": stage_state.get("protected_objects", []),
        }
    return result
