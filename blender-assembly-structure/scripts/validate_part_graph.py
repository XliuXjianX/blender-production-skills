#!/usr/bin/env python3
"""Validate the topology-first Part Graph without changing Blender."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORM_LEVELS = {"primary", "structural", "transition", "functional", "detail", "helper"}
COMBINATION_LEVELS = {
    "A_VISUAL_GROUPING",
    "B_OBJECT_JOIN",
    "C_PHYSICAL_ASSEMBLY",
    "D_TOPOLOGY_FUSION",
    "NOT_APPLICABLE",
}
SEPARATION_POLICIES = {
    "continuous_shell",
    "separate_manufactured_part",
    "moving_part",
    "transparent_part",
    "instance_source",
    "temporary_construction",
    "non_geometric",
}
BUILDABLE_ROLES = {
    "primary_form",
    "structural_part",
    "functional_detail",
    "decorative_detail",
    "cutter",
}
RELATIONSHIP_TYPES = {
    "continuous_surface",
    "boolean_fused",
    "mechanical_seam",
    "embedded_component",
    "constraint_connection",
    "physical_contact",
    "instanced_element",
    "intentionally_independent",
}
STAGES = [
    "analysis",
    "blockout",
    "topology_construction",
    "structural_forms",
    "transition_forms",
    "functional_parts",
    "surface_details",
    "systems",
    "surfacing",
    "lighting",
    "final",
]


def validate(
    graph: dict[str, Any],
    require_approved: bool = False,
    stage: str = "analysis",
) -> dict[str, Any]:
    errors: list[str] = []
    parts = [part for part in graph.get("parts", []) if isinstance(part, dict)]
    ids = [part.get("id") for part in parts]
    if not parts:
        errors.append("parts_empty")
    if len(ids) != len(set(ids)):
        errors.append("duplicate_part_ids")
    if any(value in {None, ""} for value in ids):
        errors.append("part_id_missing")
    if require_approved and graph.get("part_graph_status") != "approved":
        errors.append("part_graph_not_approved")
    if stage not in STAGES:
        errors.append("stage_invalid")
        stage = "analysis"
    stage_index = STAGES.index(stage)
    for part in parts:
        part_id = str(part.get("id", "unknown"))
        if part.get("form_level") not in FORM_LEVELS:
            errors.append(f"form_level:{part_id}")
        if part.get("role") in BUILDABLE_ROLES:
            for key in (
                "physical_function",
                "separation_policy",
                "separation_reason",
                "construction_method",
                "connection_method",
                "combination_level",
                "final_object_name",
                "topology_status",
            ):
                if part.get(key) in {None, "", "unresolved"}:
                    errors.append(f"{key}:{part_id}")
            if part.get("separation_policy") not in SEPARATION_POLICIES:
                errors.append(f"separation_policy_value:{part_id}")
            if part.get("combination_level") not in COMBINATION_LEVELS:
                errors.append(f"combination_level_value:{part_id}")
            if not isinstance(part.get("blockout_object_names"), list):
                errors.append(f"blockout_object_names:{part_id}")
            if not isinstance(part.get("assembly_interfaces"), list):
                errors.append(f"assembly_interfaces:{part_id}")
            topology_evidence = part.get("topology_evidence")
            if not isinstance(topology_evidence, dict):
                errors.append(f"topology_evidence:{part_id}")
                topology_evidence = {}
            if part.get("separation_policy") == "continuous_shell":
                if part.get("combination_level") != "D_TOPOLOGY_FUSION":
                    errors.append(f"continuous_shell_not_level_d:{part_id}")
                if part.get("requirements", {}).get("single_component") is not True:
                    errors.append(f"continuous_shell_not_single_component:{part_id}")
            if stage_index > STAGES.index("topology_construction") and part.get("blockout_proxy") is True:
                errors.append(f"blockout_proxy_remains:{part_id}")
            if (
                stage_index > STAGES.index("topology_construction")
                and part.get("form_level") in {"primary", "structural", "transition"}
                and part.get("topology_status") not in {"passed", "deferred", "not_applicable"}
            ):
                errors.append(f"formal_topology_incomplete:{part_id}")
            if part.get("topology_status") == "passed":
                if not topology_evidence.get("construction_operations"):
                    errors.append(f"construction_operations_empty:{part_id}")
                component_count = topology_evidence.get("connected_component_count")
                if not isinstance(component_count, int) or component_count < 1:
                    errors.append(f"component_evidence:{part_id}")
                wireframe = topology_evidence.get("wireframe")
                if not isinstance(wireframe, str) or not Path(wireframe).is_file():
                    errors.append(f"wireframe_evidence:{part_id}")
            if (
                stage_index >= STAGES.index("functional_parts")
                and part.get("form_level") in {"functional", "detail"}
                and part.get("separation_policy") not in {"instance_source", "temporary_construction"}
                and not part.get("assembly_interfaces")
            ):
                errors.append(f"assembly_interfaces_empty:{part_id}")
            reason = str(part.get("separation_reason", "")).lower()
            if "difficult" in reason or "hard to model" in reason or "难" in reason:
                errors.append(f"difficulty_used_as_separation_reason:{part_id}")
    id_set = set(ids)
    for index, relation in enumerate(graph.get("relationships", [])):
        if not isinstance(relation, dict):
            errors.append(f"relationship_not_object:{index}")
            continue
        if relation.get("a") not in id_set or relation.get("b") not in id_set:
            errors.append(f"relationship_endpoint:{index}")
        if relation.get("type") not in RELATIONSHIP_TYPES:
            errors.append(f"relationship_type:{index}")
        if not relation.get("validation"):
            errors.append(f"relationship_validation_empty:{index}")
        relation_type = relation.get("type")
        endpoints = [part for part in parts if part.get("id") in {relation.get("a"), relation.get("b")}]
        if relation_type in {"continuous_surface", "boolean_fused"} and any(
            part.get("combination_level") != "D_TOPOLOGY_FUSION" for part in endpoints
        ):
            errors.append(f"fusion_relation_not_level_d:{index}")
    return {
        "schema_version": "1.0",
        "status": "FAIL" if errors else "PASS",
        "part_count": len(parts),
        "errors": sorted(set(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction-graph", required=True)
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--stage", choices=STAGES, default="analysis")
    parser.add_argument("--output")
    args = parser.parse_args()
    graph = json.loads(Path(args.construction_graph).expanduser().resolve().read_text(encoding="utf-8"))
    report = validate(graph, args.require_approved, args.stage)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
