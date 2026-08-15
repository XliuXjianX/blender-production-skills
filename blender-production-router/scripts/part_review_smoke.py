#!/usr/bin/env python3
"""Exercise bounded per-part scoring and local/global pause behavior."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _scaled(criteria: dict[str, int], fraction: float) -> dict[str, float]:
    return {key: float(value) * fraction for key, value in criteria.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    router = _load("part_review_router", SCRIPT_DIR / "route_blender_task.py")
    scorer = _load("part_review_scorer", SCRIPT_DIR / "score_part_review.py")
    checks: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="part_review_smoke_") as temp:
        root = Path(temp)
        router.write_artifacts("Build a production hard-surface asset", root, None, [])
        stage_path = root / "stage_state.json"
        stage = _read(stage_path)
        stage.update(
            {
                "current_stage": "blockout",
                "modeling_stage": "blockout",
                "visual_gate": "blockout",
                "mutations_blocked": False,
            }
        )
        _write(stage_path, stage)
        artifact_path = root / "part_review_scores.json"

        first = scorer.apply_review(
            artifact_path,
            "rail_detail",
            "blockout",
            _scaled(scorer.CRITERIA["blockout"], 0.35),
            ["rail detail first review"],
            [],
            "rail-attempt-1",
            True,
            False,
            stage_path,
        )
        first_stage = _read(stage_path)
        checks["first_sub40_rebuilds_only_part"] = (
            first["disposition"] == "rebuild_part"
            and "rail_detail" in first_stage["part_progress"]["paused"]
            and first_stage["mutations_blocked"] is False
        )

        second = scorer.apply_review(
            artifact_path,
            "rail_detail",
            "blockout",
            _scaled(scorer.CRITERIA["blockout"], 0.50),
            ["rail detail second review"],
            [],
            "rail-attempt-2",
            False,
            None,
            stage_path,
        )
        second_stage = _read(stage_path)
        checks["noncritical_second_failure_stays_local"] = (
            second["disposition"] == "needs_user_review"
            and "rail_detail" in second_stage["part_progress"]["needs_user_review"]
            and second_stage["mutations_blocked"] is False
            and second_stage["project_disposition"]["status"] == "active"
        )

        limit_raised = False
        try:
            scorer.apply_review(
                artifact_path,
                "rail_detail",
                "blockout",
                _scaled(scorer.CRITERIA["blockout"], 0.90),
                ["illegal third review"],
                [],
                "rail-attempt-3",
                False,
                None,
                stage_path,
            )
        except RuntimeError:
            limit_raised = True
        rail_part = next(
            item
            for item in _read(artifact_path)["parts"]
            if item["part_id"] == "rail_detail"
        )
        checks["third_automatic_attempt_is_rejected"] = (
            limit_raised
            and rail_part["stages"]["blockout"]["attempts"] == 2
            and len(rail_part["stages"]["blockout"]["history"]) == 2
        )

        repair = scorer.apply_review(
            artifact_path,
            "independent_panel",
            "blockout",
            _scaled(scorer.CRITERIA["blockout"], 0.65),
            ["panel review"],
            ["tighten one local proportion"],
            "panel-attempt-1",
            True,
            False,
            stage_path,
        )
        repair_stage = _read(stage_path)
        checks["score_60_to_79_clears_with_repairs"] = (
            repair["disposition"] == "repair_local"
            and repair["gate_clear"] is True
            and "independent_panel" in repair_stage["part_progress"]["continuable"]
        )

        for attempt_id, fraction in (("subject-attempt-1", 0.30), ("subject-attempt-2", 0.50)):
            critical = scorer.apply_review(
                artifact_path,
                "subject",
                "blockout",
                _scaled(scorer.CRITERIA["blockout"], fraction),
                [attempt_id],
                [],
                attempt_id,
                False,
                None,
                stage_path,
            )
        critical_stage = _read(stage_path)
        checks["critical_second_failure_closes_visual_gate_only"] = (
            critical["disposition"] == "needs_user_review"
            and critical_stage["gate_status"] == "waiting_for_user"
            and critical_stage["mutations_blocked"] is True
            and critical_stage["project_disposition"]["status"] == "active"
            and critical_stage["project_disposition"]["confirmation"] is None
        )

    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
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
