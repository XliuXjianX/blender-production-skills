#!/usr/bin/env python3
"""Verify declared simulation and procedural systems against real Blender data."""

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
    spec = importlib.util.spec_from_file_location("system_validation_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cube(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _evidence(path: Path) -> str:
    image = bpy.data.images.new(path.stem, width=8, height=8)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return str(path)


def _part(
    part_id: str,
    obj: bpy.types.Object,
    wireframe: str,
    components: int,
) -> dict[str, object]:
    return {
        "id": part_id,
        "object": obj.name,
        "final_object_name": obj.name,
        "role": "structural_part",
        "form_level": "structural",
        "physical_function": part_id,
        "separation_policy": "instance_source" if part_id == "array_output" else "separate_manufactured_part",
        "separation_reason": "system validation fixture",
        "construction_method": "BOX_MODELING",
        "connection_method": "intentionally_independent",
        "combination_level": "C_PHYSICAL_ASSEMBLY",
        "bevel_policy": {"classes": [], "method": "not_applicable", "widths": {}},
        "modifier_stack_intent": [],
        "blockout_proxy": False,
        "topology_status": "passed",
        "blockout_object_names": [],
        "assembly_interfaces": [],
        "topology_evidence": {
            "construction_operations": ["box_modeling"],
            "connected_component_count": components,
            "evaluated_bevel_geometry": None,
            "boolean_cleanup_passed": None,
            "primitive_retained_reason": "the fixture is intentionally a manufactured rectangular solid",
            "wireframe": wireframe,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    array_obj = _cube("TEST-ARRAY-OUTPUT", (0.0, 0.0, 0.0))
    array = array_obj.modifiers.new("TEST-ARRAY", "ARRAY")
    array.count = 3
    array.relative_offset_displace = (2.0, 0.0, 0.0)
    cloth_obj = _cube("TEST-CLOTH-SUBJECT", (0.0, 3.0, 0.0))
    cloth_obj.modifiers.new("TEST-CLOTH", "CLOTH")
    bpy.context.view_layer.update()

    views = {
        key: _evidence(output.with_name(f"systems-{key}.png"))
        for key in ("front_clay", "side_clay", "top_clay", "hero_clay", "wireframe")
    }
    graph = {
        "schema_version": "1.0",
        "part_graph_status": "approved",
        "parts": [
            _part("array_output", array_obj, views["wireframe"], 3),
            _part("cloth_subject", cloth_obj, views["wireframe"], 1),
        ],
        "relationships": [],
        "unclassified_visible_intersections_allowed": False,
    }
    stage_state = {
        "schema_version": "1.0",
        "current_stage": "systems",
        "modeling_stage": "systems",
        "analysis_gate_status": "passed",
        "topology_gate_status": "passed",
        "form_gates": {
            "primary_masses": "passed",
            "structural_forms": "passed",
            "transition_forms": "passed",
            "functional_parts": "passed",
            "surface_details": "passed",
        },
        "review_evidence": views,
        "topology_rollback_strikes": [],
        "rollback": {"required": False, "target": None, "reasons": []},
        "mutations_blocked": False,
        "project_disposition": {"status": "active"},
    }
    validator = _load_validator()
    undeclared = validator.validate_scene(
        graph=graph,
        snapshot=None,
        object_names=[array_obj.name, cloth_obj.name],
        allow_open_objects=set(),
        max_unclassified_pairs=10,
        stage_state=stage_state,
    )
    undeclared_statuses = {item["id"]: item["status"] for item in undeclared["checks"]}

    graph["parts"][0]["procedural"] = {
        "status": "passed",
        "source_objects": [array_obj.name],
        "instance_count": 3,
        "realized_count": 0,
        "realize_reason": "",
        "animated_random": False,
        "stable_ids": True,
        "viewport_vertex_budget": 1000,
    }
    graph["parts"][1]["simulation"] = {
        "system": "cloth",
        "role": "subject",
        "cache_required": False,
        "low_resolution_test": {
            "status": "passed",
            "frame_range": [1, 20],
            "max_penetration": 0.0,
            "penetration_threshold": 0.001,
            "evidence": ["isolated low-resolution cloth test"],
        },
    }
    declared = validator.validate_scene(
        graph=graph,
        snapshot=None,
        object_names=[array_obj.name, cloth_obj.name],
        allow_open_objects=set(),
        max_unclassified_pairs=10,
        stage_state=stage_state,
    )
    declared_statuses = {item["id"]: item["status"] for item in declared["checks"]}
    checks = {
        "undeclared_array_fails": undeclared_statuses.get("procedural_part_array_output") == "FAIL",
        "undeclared_cloth_fails": undeclared_statuses.get("simulation_part_cloth_subject") == "FAIL",
        "declared_array_passes": declared_statuses.get("procedural_part_array_output") == "PASS",
        "declared_cloth_passes": declared_statuses.get("simulation_part_cloth_subject") == "PASS",
    }
    result = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("SYSTEM_VALIDATION_SMOKE " + json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
