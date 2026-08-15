#!/usr/bin/env python3
"""Blender-background smoke test for directional structure scene mapping."""

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
    spec = importlib.util.spec_from_file_location("directional_scene_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _empty(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def _cube(name: str, location: tuple[float, float, float], dimensions: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.context.view_layer.update()
    return obj


def _directional_check(validator, spatial: dict) -> dict:
    checks, _failures, _not_evaluated = validator._spatial_scene_checks(spatial)
    return next(item for item in checks if item.get("id") == "directional_structure_scene_rail_a")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args(_script_args())
    validator = _load_validator()

    start = _empty("ANCHOR_START", (0.0, 0.0, 0.0))
    end = _empty("ANCHOR_END", (0.0, 4.0, 1.0))
    _empty("CTRL_RAIL_PATH", (0.0, 2.0, 0.5))
    _cube("RAIL_GENERATED", (0.0, 2.0, 0.5), (0.4, 4.0, 1.0))
    spatial = {
        "camera_context": {"lock_state": "locked"},
        "regions": [],
        "connections": [],
        "directional_structures": [
            {
                "id": "rail_a",
                "type": "railing",
                "direction_vector": [0.0, 1.0, 0.25],
                "anchor_object_names": {"start": start.name, "end": end.name},
                "control_object_names": ["CTRL_RAIL_PATH"],
                "generated_object_names": ["RAIL_GENERATED"],
            }
        ],
    }
    accepted = _directional_check(validator, spatial)
    end.location = (0.0, -4.0, 1.0)
    bpy.context.view_layer.update()
    reversed_check = _directional_check(validator, spatial)
    checks = {
        "valid_directional_scene_mapping_passes": accepted.get("status") == "PASS",
        "reversed_anchor_direction_fails": reversed_check.get("status") == "FAIL"
        and "directional_anchor_order_mismatch"
        in reversed_check.get("evidence", {}).get("failed_requirements", []),
    }
    report = {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "check_count": len(checks),
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
