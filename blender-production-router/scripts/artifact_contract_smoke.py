#!/usr/bin/env python3
"""Exercise progressive analysis, topology conversion, and rollback artifact gates."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_router():
    path = SCRIPT_DIR / "route_blender_task.py"
    spec = importlib.util.spec_from_file_location("artifact_contract_router", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_part_scorer():
    path = SCRIPT_DIR / "score_part_review.py"
    spec = importlib.util.spec_from_file_location("artifact_contract_part_scorer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _validate(root: Path) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "validate_public_artifacts.py"),
            "--artifact-dir",
            str(root),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return completed.returncode, json.loads(completed.stdout)


def _approve_minimum_analysis(root: Path) -> None:
    analysis_path = root / "production_analysis.json"
    analysis = _read(analysis_path)
    analysis.update(
        {
            "status": "provisional",
            "execution_allowed": True,
            "execution_scope": "reversible_blockout",
            "completion_scope": "reusable_asset",
            "critical_blockers": [],
            "part_graph_status": "provisional",
        }
    )
    analysis["protected_scope"] = {
        "status": "passed",
        "objects": [],
        "task_owned_collection": "TASK_Blockout",
    }
    analysis["real_scale"] = {
        "status": "estimated",
        "units": "METRIC",
        "anchors": ["overall bounding box hypothesis"],
    }
    analysis["design_intent"].update(
        {
            "status": "provisional",
            "visual_thesis": "test subject with one primary focus",
            "evidence": ["brief"],
        }
    )
    analysis["focal_hierarchy"] = [{"id": "subject", "rank": "primary"}]
    minimum = analysis["minimum_viable_analysis"]
    minimum.update({"status": "passed", "attempts": 1, "evidence": ["brief and scene preflight"]})
    minimum["required_decisions"] = {
        "deliverable_scope": True,
        "protected_scope": True,
        "major_parts_or_regions": True,
        "scale_strategy": True,
        "provisional_route": True,
    }
    _write(analysis_path, analysis)

    graph_path = root / "construction_graph.json"
    graph = _read(graph_path)
    graph["part_graph_status"] = "provisional"
    _write(graph_path, graph)

    stage_path = root / "stage_state.json"
    stage = _read(stage_path)
    stage.update(
        {
            "current_stage": "blockout",
            "modeling_stage": "blockout",
            "analysis_gate_status": "provisional",
            "visual_gate": "blockout",
            "mutations_blocked": False,
            "allowed_operations": ["task-owned reversible Blockout"],
        }
    )
    stage["part_progress"]["active"] = ["subject"]
    _write(stage_path, stage)


def _approve_analysis(root: Path) -> None:
    analysis_path = root / "production_analysis.json"
    analysis = _read(analysis_path)
    analysis.update(
        {
            "status": "passed",
            "execution_allowed": True,
            "execution_scope": "formal_production",
            "completion_scope": "reusable_asset",
            "part_graph_status": "approved",
            "blocking_unknowns": [],
            "critical_blockers": [],
            "object_partition_basis": ["one manufactured exterior shell"],
            "geometry_vs_shading": ["silhouette, transitions, and bevels remain geometry"],
        }
    )
    analysis["real_scale"] = {"status": "confirmed", "units": "METRIC", "anchors": ["overall dimensions"]}
    analysis["protected_scope"] = {
        "status": "passed",
        "objects": [],
        "task_owned_collection": "TASK_Blockout",
    }
    for section in (
        "design_intent",
        "camera_and_perspective",
        "primary_silhouette_and_proportion",
        "spatial_and_support_structure",
        "lighting_analysis",
        "material_analysis",
    ):
        analysis[section]["status"] = "resolved"
    analysis["focal_hierarchy"] = [{"id": "subject", "rank": "primary"}]
    analysis["depth_layers"] = [{"id": "asset_depth", "role": "primary"}]
    analysis["representation_budget"].update(
        {"status": "resolved", "real_geometry": ["subject"]}
    )
    analysis["performance_budget"].update(
        {"status": "resolved", "object_limit": 20, "instance_limit": 0}
    )
    analysis["form_hierarchy"].update(
        {
            "primary_masses": [{"id": "main_shell", "status": "planned"}],
            "structural_forms": [{"id": "major_sections", "status": "planned"}],
            "transition_forms": [{"id": "manufactured_radii", "status": "planned"}],
        }
    )
    _write(analysis_path, analysis)
    graph_path = root / "construction_graph.json"
    graph = _read(graph_path)
    graph["part_graph_status"] = "approved"
    for part in graph.get("parts", []):
        if part.get("role") not in {
            "primary_form",
            "structural_part",
            "functional_detail",
            "decorative_detail",
            "cutter",
        }:
            continue
        part.update(
            {
                "physical_function": "formal exterior shell",
                "separation_policy": "continuous_shell",
                "separation_reason": "one manufactured shell",
                "construction_method": "SUBDIVISION_SURFACE",
                "connection_method": "shared_topology",
                "combination_level": "D_TOPOLOGY_FUSION",
                "final_object_name": "FORMAL_Subject",
                "topology_status": "planned",
                "bevel_policy": {"classes": ["SECONDARY_BEVEL"], "method": "BEVEL_MODIFIER"},
            }
        )
    _write(graph_path, graph)


def _set_stage(root: Path, modeling_stage: str) -> None:
    stage_path = root / "stage_state.json"
    stage = _read(stage_path)
    stage.update(
        {
            "current_stage": "primary_surface",
            "modeling_stage": modeling_stage,
            "analysis_gate_status": "passed",
            "mutations_blocked": False,
            "allowed_operations": ["formal topology work"],
        }
    )
    _write(stage_path, stage)


def _score_stage(scorer, root: Path, stage_name: str, attempt_id: str) -> None:
    scores = {key: float(value) for key, value in scorer.CRITERIA[stage_name].items()}
    scorer.apply_review(
        root / "part_review_scores.json",
        "subject",
        stage_name,
        scores,
        [f"{stage_name} smoke evidence"],
        [],
        attempt_id,
        False,
        None,
        root / "stage_state.json",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capabilities", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    capabilities = _read(Path(args.capabilities).expanduser().resolve())
    router = _load_router()
    scorer = _load_part_scorer()
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="artifact_contract_smoke_") as temp:
        root = Path(temp)
        router.write_artifacts(
            "正式制作连续产品外壳并在灰模后转换为真实拓扑",
            root,
            capabilities,
            [],
        )
        initial_code, initial = _validate(root)
        checks["initial_analysis_state_passes"] = initial_code == 0 and initial["status"] == "PASS"

        _approve_minimum_analysis(root)
        provisional_code, provisional = _validate(root)
        checks["provisional_analysis_allows_blockout"] = (
            provisional_code == 0 and provisional["status"] == "PASS"
        )

        derivatives_path = root / "reference_derivatives.json"
        derivatives = _read(derivatives_path)
        derivatives["source_references"] = ["synthetic-reference.png"]
        derivatives["generation_capability"] = "unavailable"
        for key in ("depth_map", "white_model_guide"):
            derivatives[key].update(
                {
                    "status": "skipped_capability_unavailable",
                    "attempts": 0,
                    "path": None,
                    "method": None,
                }
            )
        _write(derivatives_path, derivatives)
        unavailable_code, unavailable = _validate(root)
        checks["unavailable_derivatives_are_non_blocking"] = (
            unavailable_code == 0 and unavailable["status"] == "PASS"
        )

        derivatives["generation_capability"] = "available"
        for key in ("depth_map", "white_model_guide"):
            derivatives[key].update(
                {
                    "status": "failed_non_blocking",
                    "attempts": 1,
                    "path": None,
                    "method": "image_generation_attempt",
                }
            )
        _write(derivatives_path, derivatives)
        failed_code, failed = _validate(root)
        checks["failed_derivatives_are_non_blocking"] = (
            failed_code == 0 and failed["status"] == "PASS"
        )

        _set_stage(root, "topology_construction")
        blocked_code, blocked = _validate(root)
        checks["provisional_analysis_blocks_formal_topology"] = (
            blocked_code != 0
            and any("formal production scope" in value for value in blocked["errors"])
        )

        _approve_analysis(root)
        _set_stage(root, "topology_construction")
        _score_stage(scorer, root, "analysis_readiness", "analysis-ready-1")
        _score_stage(scorer, root, "blockout", "blockout-pass-1")
        conversion_code, conversion = _validate(root)
        checks["topology_conversion_allows_active_proxies"] = conversion_code == 0 and conversion["status"] == "PASS"

        _set_stage(root, "structural_forms")
        _score_stage(scorer, root, "formal_topology", "formal-topology-1")
        stage = _read(root / "stage_state.json")
        stage["topology_gate_status"] = "passed"
        stage["form_gates"]["primary_masses"] = "passed"
        _write(root / "stage_state.json", stage)
        structural_code, structural = _validate(root)
        checks["structural_stage_rejects_unconverted_proxy"] = (
            structural_code != 0
            and any("blockout proxies remain" in value for value in structural["errors"])
        )

        _set_stage(root, "functional_parts")
        stage = _read(root / "stage_state.json")
        stage["topology_rollback_strikes"] = [
            "blockout_proxy_as_final_topology",
            "wireframe_acceptance_missing",
        ]
        stage["rollback"] = {"required": False, "target": None, "reasons": []}
        _write(root / "stage_state.json", stage)
        rollback_code, rollback = _validate(root)
        checks["two_strikes_block_later_stage"] = (
            rollback_code != 0
            and "stage_state.json: two topology strikes require rollback" in rollback["errors"]
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
