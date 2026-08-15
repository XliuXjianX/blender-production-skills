#!/usr/bin/env python3
"""Apply a reference score through the Router-owned stage state."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from router_state import apply_blockout_score_decision, read_json, write_json_atomic


def apply(artifact_dir: Path, protected_objects: list[str] | None = None) -> dict[str, object]:
    root = artifact_dir.expanduser().resolve()
    gate_path = root / "reference_gate.json"
    stage_path = root / "stage_state.json"
    gate = read_json(gate_path)
    stage = read_json(stage_path)
    decision = gate.get("router_decision", {})
    if decision.get("owner") != "blender-production-router":
        raise ValueError("reference_gate has no Router-owned score decision")
    attempt_id = decision.get("attempt_id")
    existing = [
        item
        for item in stage.get("router_decisions", [])
        if isinstance(item, dict) and item.get("type") == "blockout_score"
    ]
    if any(item.get("attempt_id") == attempt_id for item in existing):
        return {
            "status": "already_applied",
            "attempt_id": attempt_id,
            "stage_state": str(stage_path),
        }

    result = apply_blockout_score_decision(stage, gate, protected_objects)
    decision["applied"] = True
    decision["applied_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    decision["stage_state"] = str(stage_path)
    write_json_atomic(stage_path, stage)
    write_json_atomic(gate_path, gate)
    result["status"] = "applied"
    result["stage_state"] = str(stage_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--protected-object", action="append", default=None)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = apply(Path(args.artifact_dir), args.protected_object)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
