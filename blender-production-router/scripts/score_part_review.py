#!/usr/bin/env python3
"""Apply one bounded, evidence-backed review to one Blender construction part."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from router_state import assert_router_owned, read_json, update_part_progress, write_json_atomic


SCHEMA_VERSION = "1.0"
MAX_ATTEMPTS = 2
VISUAL_GATES = {"blockout", "primary_surface", "systems", "final"}
CRITERIA: dict[str, dict[str, int]] = {
    "analysis_readiness": {
        "intent_and_role": 20,
        "scale_and_reference": 20,
        "construction_route": 25,
        "relationships": 20,
        "risk_and_downstream_use": 15,
    },
    "blockout": {
        "silhouette": 30,
        "proportion": 25,
        "position_support_clearance": 25,
        "directionality": 20,
    },
    "formal_topology": {
        "continuity": 20,
        "structural_form": 20,
        "transition_quality": 20,
        "bevel_edge_language": 15,
        "cleanup": 15,
        "editability": 10,
    },
    "structural_transition": {
        "structural_completeness": 25,
        "transition_continuity": 25,
        "connection_correctness": 20,
        "edge_language": 15,
        "multiview_evidence": 15,
    },
    "systems": {
        "causal_fit": 25,
        "setup": 20,
        "stability": 25,
        "interfaces": 15,
        "cache_and_performance": 15,
    },
    "surfacing": {
        "material_identity": 25,
        "scale_and_mapping": 20,
        "physical_response": 25,
        "causal_layering": 15,
        "geometry_compatibility": 15,
    },
    "final": {
        "multiview_or_reference": 25,
        "construction": 20,
        "technical_integrity": 20,
        "surfacing_and_lighting": 20,
        "downstream_fitness": 15,
    },
}


_read = read_json
_write = write_json_atomic


def _parse_scores(values: list[str], stage: str) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"score must use key=value: {value}")
        key, raw = value.split("=", 1)
        key = key.strip()
        if key in parsed:
            raise ValueError(f"duplicate score component: {key}")
        try:
            parsed[key] = float(raw)
        except ValueError as exc:
            raise ValueError(f"score is not numeric: {value}") from exc
    expected = CRITERIA[stage]
    if set(parsed) != set(expected):
        missing = sorted(set(expected) - set(parsed))
        extra = sorted(set(parsed) - set(expected))
        raise ValueError(f"score components mismatch; missing={missing}, extra={extra}")
    for key, score in parsed.items():
        maximum = float(expected[key])
        if score < 0.0 or score > maximum:
            raise ValueError(f"{key} must be between 0 and {maximum:g}")
    return parsed


def _empty_stage(disposition: str = "not_scored") -> dict[str, Any]:
    return {
        "attempts": 0,
        "current_score": None,
        "disposition": disposition,
        "gate_clear": disposition == "deferred",
        "consecutive_below_60": 0,
        "history": [],
    }


def _find_part(
    artifact: dict[str, Any],
    part_id: str,
    create: bool,
    critical: bool | None,
) -> dict[str, Any]:
    parts = artifact.setdefault("parts", [])
    for part in parts:
        if isinstance(part, dict) and part.get("part_id") == part_id:
            if critical is not None:
                part["critical"] = critical
            return part
    if not create:
        raise ValueError(f"unknown part_id: {part_id}; use --create-part after Part Graph expansion")
    if critical is None:
        raise ValueError("--critical is required with --create-part")
    part = {
        "part_id": part_id,
        "critical": critical,
        "stages": {stage: _empty_stage() for stage in CRITERIA},
    }
    parts.append(part)
    return part


def apply_review(
    artifact_path: Path,
    part_id: str,
    stage: str,
    scores: dict[str, float],
    evidence: list[str],
    notes: list[str],
    attempt_id: str | None,
    create_part: bool,
    critical: bool | None,
    stage_state_path: Path | None,
) -> dict[str, Any]:
    stage_state: dict[str, Any] | None = None
    if stage_state_path is not None:
        stage_state = _read(stage_state_path)
        assert_router_owned(stage_state)

    artifact = _read(artifact_path)
    if artifact.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported part_review_scores schema")
    if artifact.get("max_automatic_reviews_per_part_stage") != MAX_ATTEMPTS:
        raise ValueError("max automatic reviews must be 2")
    if artifact.get("project_policy", {}).get("project_delete_from_part_failure") is not False:
        raise ValueError("part failure must not authorize project deletion")
    if not evidence or any(not str(value).strip() for value in evidence):
        raise ValueError("at least one non-empty evidence item is required")

    part = _find_part(artifact, part_id, create_part, critical)
    part_critical = bool(part.get("critical"))
    stages = part.setdefault("stages", {})
    record = stages.setdefault(stage, _empty_stage())
    history = record.setdefault("history", [])
    attempts = int(record.get("attempts", len(history)))
    if attempts >= MAX_ATTEMPTS or len(history) >= MAX_ATTEMPTS:
        raise RuntimeError(
            f"automatic review limit reached for {part_id}:{stage}; user review is required"
        )

    resolved_attempt_id = attempt_id or f"{part_id}:{stage}:{attempts + 1}"
    if any(item.get("attempt_id") == resolved_attempt_id for item in history if isinstance(item, dict)):
        raise ValueError(f"duplicate attempt_id: {resolved_attempt_id}")

    total = round(sum(scores.values()), 4)
    consecutive = int(record.get("consecutive_below_60", 0)) + 1 if total < 60 else 0
    if consecutive >= MAX_ATTEMPTS:
        disposition = "needs_user_review"
        gate_clear = False
    elif total >= 80:
        disposition = "pass"
        gate_clear = True
    elif total >= 60:
        disposition = "repair_local"
        gate_clear = True
    elif total >= 40:
        disposition = "repair_local"
        gate_clear = False
    else:
        disposition = "rebuild_part"
        gate_clear = False

    history.append(
        {
            "attempt_id": resolved_attempt_id,
            "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "components": scores,
            "total": total,
            "evidence": [str(value) for value in evidence],
            "notes": [str(value) for value in notes],
            "disposition": disposition,
            "gate_clear": gate_clear,
        }
    )
    record.update(
        {
            "attempts": attempts + 1,
            "current_score": total,
            "disposition": disposition,
            "gate_clear": gate_clear,
            "consecutive_below_60": consecutive,
        }
    )
    artifact["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _write(artifact_path, artifact)

    if stage_state is not None and stage_state_path is not None:
        update_part_progress(
            stage_state,
            part_id,
            part_critical,
            disposition,
            gate_clear,
        )
        _write(stage_state_path, stage_state)

    return {
        "status": "ok",
        "part_id": part_id,
        "stage": stage,
        "attempts": attempts + 1,
        "score": total,
        "disposition": disposition,
        "gate_clear": gate_clear,
        "critical": part_critical,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--part-id", required=True)
    parser.add_argument("--stage", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--score", action="append", default=[])
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--attempt-id")
    parser.add_argument("--create-part", action="store_true")
    parser.add_argument("--critical", choices=["true", "false"])
    parser.add_argument("--stage-state")
    args = parser.parse_args()

    critical = None if args.critical is None else args.critical == "true"
    try:
        result = apply_review(
            Path(args.artifact).expanduser().resolve(),
            args.part_id,
            args.stage,
            _parse_scores(args.score, args.stage),
            args.evidence,
            args.note,
            args.attempt_id,
            args.create_part,
            critical,
            Path(args.stage_state).expanduser().resolve() if args.stage_state else None,
        )
    except RuntimeError as exc:
        print(json.dumps({"status": "limit_reached", "error": str(exc)}, ensure_ascii=False))
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
