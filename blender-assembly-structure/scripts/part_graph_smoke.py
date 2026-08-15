#!/usr/bin/env python3
"""Exercise Part Graph approval, topology evidence, and fusion semantics."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_validator():
    path = SCRIPT_DIR / "validate_part_graph.py"
    spec = importlib.util.spec_from_file_location("part_graph_validator", path)
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
    with tempfile.TemporaryDirectory(prefix="part_graph_smoke_") as temp:
        wireframe = Path(temp) / "wireframe.png"
        wireframe.write_bytes(b"topology evidence")
        part = {
            "id": "housing",
            "role": "primary_form",
            "form_level": "primary",
            "physical_function": "load-bearing exterior housing",
            "separation_policy": "continuous_shell",
            "separation_reason": "one manufactured shell",
            "construction_method": "SUBDIVISION_SURFACE",
            "connection_method": "shared_topology",
            "combination_level": "D_TOPOLOGY_FUSION",
            "final_object_name": "Housing",
            "blockout_proxy": False,
            "topology_status": "passed",
            "blockout_object_names": ["BLOCKOUT_Housing"],
            "assembly_interfaces": [],
            "topology_evidence": {
                "construction_operations": ["profile_extrusion", "edge_loop_refinement"],
                "connected_component_count": 1,
                "wireframe": str(wireframe),
            },
            "requirements": {"single_component": True},
        }
        graph = {
            "schema_version": "1.0",
            "part_graph_status": "approved",
            "parts": [part],
            "relationships": [],
        }
        valid = validator.validate(graph, require_approved=True, stage="structural_forms")
        invalid_join = json.loads(json.dumps(graph))
        invalid_join["parts"][0]["combination_level"] = "B_OBJECT_JOIN"
        joined = validator.validate(invalid_join, require_approved=True, stage="structural_forms")
        invalid_proxy = json.loads(json.dumps(graph))
        invalid_proxy["parts"][0]["blockout_proxy"] = True
        proxy = validator.validate(invalid_proxy, require_approved=True, stage="structural_forms")
        checks = {
            "valid_graph_passes": valid["status"] == "PASS",
            "join_is_not_fusion": "continuous_shell_not_level_d:housing" in joined["errors"],
            "post_topology_proxy_fails": "blockout_proxy_remains:housing" in proxy["errors"],
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
