#!/usr/bin/env python3
"""Verify that two topology regressions force a deterministic stage rollback."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _load_validator():
    path = SCRIPT_DIR / "validate_scene.py"
    spec = importlib.util.spec_from_file_location("topology_rollback_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_router_decision():
    path = SCRIPT_DIR.parent.parent / "blender-production-router" / "scripts" / "apply_validation_decision.py"
    spec = importlib.util.spec_from_file_location("topology_rollback_router", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cube(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _evidence(path: Path) -> str:
    image = bpy.data.images.new(path.stem, width=8, height=8)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return str(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    shell_a = _cube("TEST-SHELL-A", (0.0, 0.0, 0.0))
    shell_b = _cube("TEST-SHELL-B", (1.0, 0.0, 0.0))
    button = _cube("TEST-EARLY-BUTTON", (0.0, 0.0, 0.8))

    views = {
        key: _evidence(output.with_name(f"topology-{key}.png"))
        for key in ("front_clay", "side_clay", "top_clay", "hero_clay", "wireframe")
    }
    wireframe = views["wireframe"]

    def part(
        part_id: str,
        obj: bpy.types.Object,
        form_level: str,
        role: str,
        status: str = "passed",
    ) -> dict[str, object]:
        return {
            "id": part_id,
            "object": obj.name,
            "final_object_name": obj.name,
            "role": role,
            "form_level": form_level,
            "physical_function": part_id,
            "separation_policy": "continuous_shell" if form_level == "primary" else "separate_manufactured_part",
            "separation_reason": "test contract",
            "construction_method": "BOX_MODELING",
            "connection_method": "bridge_and_weld" if form_level == "primary" else "mechanical_mount",
            "combination_level": "D_TOPOLOGY_FUSION" if form_level == "primary" else "C_PHYSICAL_ASSEMBLY",
            "bevel_policy": {"classes": [], "method": "not_applicable"},
            "modifier_stack_intent": [],
            "blockout_proxy": False,
            "topology_status": status,
            "blockout_object_names": [],
            "assembly_interfaces": [],
            "topology_evidence": {
                "construction_operations": ["box_modeling", "edge_loop_refinement"],
                "connected_component_count": 1,
                "evaluated_bevel_geometry": None,
                "boolean_cleanup_passed": None,
                "wireframe": wireframe,
            },
        }

    graph = {
        "schema_version": "1.0",
        "part_graph_status": "approved",
        "parts": [
            part("shell_a", shell_a, "primary", "primary_form"),
            part("shell_b", shell_b, "primary", "primary_form"),
            part("early_button", button, "functional", "functional_detail", "in_progress"),
        ],
        "relationships": [
            {
                "a": "shell_a",
                "b": "shell_b",
                "type": "continuous_surface",
                "validation": ["same final mesh", "single connected component"],
            }
        ],
        "unclassified_visible_intersections_allowed": False,
    }
    stage_state = {
        "schema_version": "1.0",
        "current_stage": "primary_surface",
        "modeling_stage": "functional_parts",
        "analysis_gate_status": "passed",
        "topology_gate_status": "passed",
        "form_gates": {
            "primary_masses": "passed",
            "structural_forms": "passed",
            "transition_forms": "open",
            "functional_parts": "open",
            "surface_details": "open",
        },
        "review_evidence": views,
        "topology_rollback_strikes": [],
        "rollback": {"required": False, "target": None, "reasons": []},
        "mutations_blocked": False,
        "allowed_operations": [],
        "project_disposition": {"status": "active"},
        "authority": {
            "state_owner": "blender-production-router",
            "validator_can_reroute": False,
            "specialist_can_restart_analysis": False,
        },
    }

    validator = _load_validator()
    report = validator.validate_scene(
        graph=graph,
        snapshot=None,
        object_names=[shell_a.name, shell_b.name, button.name],
        allow_open_objects=set(),
        max_unclassified_pairs=20,
        stage_state=stage_state,
    )
    router_decision = _load_router_decision()
    router_decision.apply_topology_rollback(
        stage_state,
        report["topology_rollback_strikes"],
        report["rollback"]["target"],
    )
    checks = {
        "validation_fails": report["overall_status"] == "FAIL",
        "two_or_more_distinct_strikes": len(report["topology_rollback_strikes"]) >= 2,
        "rollback_targets_structural_forms": report["rollback"]["target"] == "structural_forms",
        "state_is_rolled_back": stage_state.get("modeling_stage") == "structural_forms",
        "later_gates_reopened": stage_state.get("form_gates", {}).get("transition_forms") == "open",
        "scene_objects_preserved": all(bpy.data.objects.get(name) is not None for name in (shell_a.name, shell_b.name, button.name)),
    }
    result = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "topology_rollback_strikes": report["topology_rollback_strikes"],
        "rollback": report["rollback"],
    }
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("TOPOLOGY_ROLLBACK_SMOKE " + json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
