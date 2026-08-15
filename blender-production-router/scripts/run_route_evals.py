#!/usr/bin/env python3
"""Run deterministic request-routing evaluations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from route_blender_task import classify_request  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evals", default=str(SCRIPT_DIR.parent / "evals" / "route_evals.json"))
    parser.add_argument("--capabilities")
    parser.add_argument("--output")
    args = parser.parse_args()
    capabilities = None
    if args.capabilities:
        capabilities = json.loads(Path(args.capabilities).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.evals).read_text(encoding="utf-8"))
    results = []
    for case in cases:
        route = classify_request(case["request"], capabilities)
        candidate_methods = [candidate["method"] for candidate in route["candidates"]]
        archetypes = {
            item["id"]: item for item in route.get("construction_archetypes", [])
        }
        parameter_owner_text = " ".join(
            owner
            for owners in route.get("construction_method_decision", {})
            .get("parameter_owners", {})
            .values()
            for owner in owners
        ).lower()
        errors = []
        native_decision = route.get("native_component_decision", {})
        if not native_decision.get("primary_system"):
            errors.append("missing native component primary system")
        system_choice = native_decision.get("system_choice", {})
        required_choice_fields = {
            "comparison_required",
            "direct_candidate",
            "node_candidate",
            "selected_system",
            "selection_reason",
            "rejected_alternative",
            "node_justification",
            "boolean_policy",
        }
        missing_choice_fields = required_choice_fields - set(system_choice)
        if missing_choice_fields:
            errors.append(
                "missing system choice fields: " + ", ".join(sorted(missing_choice_fields))
            )
        if route.get("code_role") not in {"orchestration", "direct_topology_exception", "none"}:
            errors.append(f"invalid code role {route.get('code_role')}")
        if route.get("application_policy") not in {
            "keep_non_destructive",
            "apply_for_downstream_topology",
            "realize_for_export",
            "bake_simulation",
            "not_applicable",
        }:
            errors.append(f"invalid application policy {route.get('application_policy')}")
        expected_selected = case.get("expected_selected")
        if expected_selected and route["selected_method"] != expected_selected:
            errors.append(f"selected {route['selected_method']} != {expected_selected}")
        expected_skill = case.get("expected_skill")
        if expected_skill and route["selected_skill"] != expected_skill:
            errors.append(f"skill {route['selected_skill']} != {expected_skill}")
        expected_deliverable = case.get("expected_deliverable")
        if expected_deliverable and route["deliverable"] != expected_deliverable:
            errors.append(
                f"deliverable {route['deliverable']} != {expected_deliverable}"
            )
        expected_design_owner = case.get("expected_design_owner")
        if expected_design_owner and route.get("design_owner") != expected_design_owner:
            errors.append(
                f"design owner {route.get('design_owner')} != {expected_design_owner}"
            )
        expected_native_system = case.get("expected_native_system")
        if expected_native_system and native_decision.get("primary_system") != expected_native_system:
            errors.append(
                f"native system {native_decision.get('primary_system')} != {expected_native_system}"
            )
        if "expected_node_candidate" in case and system_choice.get("node_candidate") != case["expected_node_candidate"]:
            errors.append(
                f"node candidate {system_choice.get('node_candidate')} != {case['expected_node_candidate']}"
            )
        expected_library_status = case.get("expected_local_asset_library_status")
        if expected_library_status and route.get("local_asset_library", {}).get("status") != expected_library_status:
            errors.append(
                "local asset library status "
                f"{route.get('local_asset_library', {}).get('status')} != {expected_library_status}"
            )
        expected_library_origin = case.get("expected_local_asset_library_origin")
        if expected_library_origin and route.get("local_asset_library", {}).get("request_origin") != expected_library_origin:
            errors.append(
                "local asset library origin "
                f"{route.get('local_asset_library', {}).get('request_origin')} != {expected_library_origin}"
            )
        for expected in case.get("expected_specialists", []):
            if expected not in route.get("required_specialists", []):
                errors.append(f"missing specialist {expected}")
        for unexpected in case.get("unexpected_specialists", []):
            if unexpected in route.get("required_specialists", []):
                errors.append(f"unexpected specialist {unexpected}")
        for expected in case.get("expected_classes", []):
            if expected not in route.get("classes", []):
                errors.append(f"missing class {expected}")
        for expected in case.get("expected_candidates", []):
            if expected not in candidate_methods:
                errors.append(f"missing candidate {expected}")
        for unexpected in case.get("unexpected_candidates", []):
            if unexpected in candidate_methods:
                errors.append(f"unexpected candidate {unexpected}")
        for expected in case.get("expected_archetypes", []):
            if expected not in archetypes:
                errors.append(f"missing construction archetype {expected}")
        for archetype_id, expected_method in case.get(
            "expected_archetype_methods", {}
        ).items():
            actual = archetypes.get(archetype_id, {}).get("primary_method")
            if actual != expected_method:
                errors.append(
                    f"archetype {archetype_id} primary method {actual} != {expected_method}"
                )
        for expected in case.get("expected_parameter_owner_terms", []):
            if expected.lower() not in parameter_owner_text:
                errors.append(f"missing parameter owner term {expected}")
        for forbidden in case.get("must_forbid", []):
            if forbidden not in route["forbidden_substitutions"]:
                errors.append(f"missing forbidden substitution {forbidden}")
        results.append(
            {
                "id": case["id"],
                "request": case["request"],
                "selected": route["selected_method"],
                "candidates": candidate_methods,
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
            }
        )
    failed = [result for result in results if result["status"] == "FAIL"]
    report = {
        "schema_version": "1.0",
        "status": "PASS" if not failed else "FAIL",
        "case_count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
