#!/usr/bin/env python3
"""Apply a validator recommendation through the Router-owned production state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from router_state import assert_router_owned, write_json_atomic


REPAIR_REQUEST_KEYS = {
    "symptom",
    "evidence",
    "likely_owner",
    "affected_part",
    "recommended_rollback_target",
    "geometry_revision",
}


def register_local_repair_request(
    stage_state: dict[str, Any],
    request: dict[str, Any],
) -> bool:
    """Record one local repair request; reject unchanged-geometry duplicates."""
    assert_router_owned(stage_state)
    missing = REPAIR_REQUEST_KEYS - set(request)
    if missing:
        raise ValueError(f"repair request missing fields: {sorted(missing)}")
    requests = stage_state.setdefault("local_repair_requests", [])
    signature = (
        str(request["affected_part"]),
        str(request["symptom"]),
        str(request["geometry_revision"]),
    )
    for existing in requests:
        if not isinstance(existing, dict):
            continue
        existing_signature = (
            str(existing.get("affected_part")),
            str(existing.get("symptom")),
            str(existing.get("geometry_revision")),
        )
        if existing_signature == signature:
            return False
    requests.append(dict(request))
    return True


def record_route_replacement(stage_state: dict[str, Any], reason: str) -> None:
    """Consume the single Router-owned route replacement budget."""
    assert_router_owned(stage_state)
    conflict = stage_state.setdefault(
        "route_conflict", {"replacement_count": 0, "replacement_limit": 1}
    )
    count = int(conflict.get("replacement_count", 0))
    limit = int(conflict.get("replacement_limit", 1))
    if count >= limit:
        raise RuntimeError("route replacement budget exhausted")
    conflict["replacement_count"] = count + 1
    conflict["last_reason"] = reason


def apply_topology_rollback(
    stage_state: dict[str, Any],
    topology_strikes: list[str],
    rollback_target: str | None,
) -> dict[str, Any]:
    assert_router_owned(stage_state)
    if rollback_target not in {None, "topology_construction", "structural_forms"}:
        raise ValueError(f"invalid rollback target: {rollback_target}")

    distinct_strikes = list(dict.fromkeys(str(value) for value in topology_strikes))
    stage_state["topology_rollback_strikes"] = distinct_strikes
    rollback = stage_state.setdefault("rollback", {})
    rollback.update(
        {
            "required": rollback_target is not None,
            "target": rollback_target,
            "reasons": distinct_strikes,
            "decision_owner": "blender-production-router",
        }
    )
    if rollback_target is None:
        return stage_state

    stage_state["current_stage"] = "primary_surface"
    stage_state["modeling_stage"] = rollback_target
    stage_state["gate_status"] = "failed"
    stage_state["mutations_blocked"] = False
    stage_state["allowed_operations"] = [
        "restore the last accepted task-owned checkpoint",
        "repair formal topology and construction relationships",
        "regenerate unique multiview and wireframe evidence",
        "rerun blender-geometry-validation",
    ]
    form_gates = stage_state.setdefault("form_gates", {})
    if rollback_target == "topology_construction":
        stage_state["topology_gate_status"] = "failed"
        reopen = (
            "primary_masses",
            "structural_forms",
            "transition_forms",
            "functional_parts",
            "surface_details",
        )
    else:
        reopen = (
            "structural_forms",
            "transition_forms",
            "functional_parts",
            "surface_details",
        )
    for key in reopen:
        form_gates[key] = "open"
    return stage_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-state", required=True)
    parser.add_argument("--validation-report", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    stage_path = Path(args.stage_state).expanduser().resolve()
    report_path = Path(args.validation_report).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else stage_path
    stage_state = json.loads(stage_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rollback = report.get("rollback", {})
    apply_topology_rollback(
        stage_state,
        list(report.get("topology_rollback_strikes", [])),
        rollback.get("target") if rollback.get("required") else None,
    )
    write_json_atomic(output_path, stage_state)
    print(json.dumps({"status": "ok", "output": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
