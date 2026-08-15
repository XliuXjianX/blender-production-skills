#!/usr/bin/env python3
"""Validate an accountable Blender lighting plan without changing the scene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate(plan: dict[str, Any], require_passed: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    if plan.get("schema_version") != "1.0":
        errors.append("schema_version_invalid")
    if plan.get("analysis_status") not in {"open", "passed", "failed"}:
        errors.append("analysis_status_invalid")
    first = plan.get("first_pass", {})
    allowed = first.get("allowed_sources")
    if allowed != ["SUN", "WORLD"]:
        errors.append("first_pass_sources_must_be_sun_world")
    if first.get("gray_model_required") is not True:
        errors.append("gray_model_not_required")
    if first.get("topology_gate_required") is not True:
        errors.append("topology_gate_not_required")
    if first.get("status") == "passed" and not first.get("evidence"):
        errors.append("gray_light_evidence_missing")
    lights = [item for item in plan.get("lights", []) if isinstance(item, dict)]
    ids = [item.get("id") for item in lights]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_light_ids")
    for index, light in enumerate(lights):
        light_id = str(light.get("id", index))
        for key in ("source", "role", "evidence", "loss_if_removed"):
            value = light.get(key)
            if value is None or value == "" or value == "unresolved" or value == []:
                errors.append(f"light_{key}:{light_id}")
    first_status = first.get("status")
    if first_status not in {"open", "passed", "failed"}:
        errors.append("first_pass_status_invalid")
    if first_status != "passed" and len(lights) > 1:
        errors.append("extra_lights_before_gray_light_pass")
    if require_passed:
        if plan.get("analysis_status") != "passed":
            errors.append("lighting_analysis_not_passed")
        if first_status != "passed":
            errors.append("gray_light_gate_not_passed")
        if not lights:
            errors.append("lights_empty")
        if plan.get("unresolved_blockers"):
            errors.append("lighting_blockers_remain")
    return {
        "schema_version": "1.0",
        "status": "FAIL" if errors else "PASS",
        "light_count": len(lights),
        "errors": sorted(set(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lighting-plan", required=True)
    parser.add_argument("--require-passed", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    plan = json.loads(Path(args.lighting_plan).expanduser().resolve().read_text(encoding="utf-8"))
    report = validate(plan, args.require_passed)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
