#!/usr/bin/env python3
"""Exercise the Sun/World first-pass and accountable-light contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_validator():
    path = SCRIPT_DIR / "validate_lighting_plan.py"
    spec = importlib.util.spec_from_file_location("lighting_plan_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    validator = _load_validator()
    sun = {
        "id": "Light_Sun_Key",
        "source": "sun",
        "role": "primary direction and cast shadow",
        "evidence": ["observed ground-contact shadow"],
        "loss_if_removed": "primary shadow direction disappears",
    }
    valid_plan = {
        "schema_version": "1.0",
        "analysis_status": "passed",
        "first_pass": {
            "status": "passed",
            "allowed_sources": ["SUN", "WORLD"],
            "gray_model_required": True,
            "topology_gate_required": True,
            "evidence": ["gray-light-review.png"],
        },
        "lights": [sun],
        "unresolved_blockers": [],
    }
    valid = validator.validate(valid_plan, require_passed=True)
    invalid_plan = json.loads(json.dumps(valid_plan))
    invalid_plan["first_pass"]["status"] = "open"
    invalid_plan["lights"].append(
        {
            "id": "Light_Unjustified_Rim",
            "source": "none",
            "role": "hide weak silhouette",
            "evidence": ["none"],
            "loss_if_removed": "primitive seam becomes visible",
        }
    )
    invalid = validator.validate(invalid_plan)
    checks = {
        "valid_gray_light_plan_passes": valid["status"] == "PASS",
        "extra_light_before_gate_fails": "extra_lights_before_gray_light_pass" in invalid["errors"],
    }
    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
