#!/usr/bin/env python3
"""Capture a non-mutating Blender scene snapshot for later safety checks."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import bpy


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _matrix_values(obj: bpy.types.Object) -> list[float]:
    return [round(float(value), 9) for row in obj.matrix_world for value in row]


def _modifier_state(modifier: bpy.types.Modifier) -> dict[str, Any]:
    state: dict[str, Any] = {
        "name": modifier.name,
        "type": modifier.type,
        "show_viewport": bool(modifier.show_viewport),
        "show_render": bool(modifier.show_render),
    }
    for attribute in ("object", "target", "curve", "origin", "texture"):
        value = getattr(modifier, attribute, None)
        if value is not None and hasattr(value, "name"):
            state[attribute] = value.name
    return state


def _object_state(obj: bpy.types.Object) -> dict[str, Any]:
    return {
        "name": obj.name,
        "type": obj.type,
        "data_name": obj.data.name if obj.data else None,
        "matrix_world": _matrix_values(obj),
        "hide_viewport": bool(obj.hide_viewport),
        "hide_render": bool(obj.hide_render),
        "display_type": str(obj.display_type),
        "collections": sorted(collection.name for collection in obj.users_collection),
        "materials": [
            slot.material.name if slot.material is not None else None for slot in obj.material_slots
        ],
        "modifiers": [_modifier_state(modifier) for modifier in obj.modifiers],
    }


def capture_snapshot(protected_names: list[str] | None = None) -> dict[str, Any]:
    names = protected_names or sorted(obj.name for obj in bpy.data.objects)
    objects = {
        name: _object_state(bpy.data.objects[name])
        for name in names
        if name in bpy.data.objects
    }
    scene = bpy.context.scene
    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "blend_file": bpy.data.filepath,
        "scene": {
            "name": scene.name,
            "camera": scene.camera.name if scene.camera else None,
            "world": scene.world.name if scene.world else None,
            "render_engine": scene.render.engine,
            "render_filepath": scene.render.filepath,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
        },
        "protected_objects": sorted(objects),
        "objects": objects,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--protected-object", action="append", default=[])
    args = parser.parse_args(_script_args())
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = capture_snapshot(args.protected_object or None)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "SCENE_SNAPSHOT "
        + json.dumps(
            {
                "output": str(output),
                "protected_object_count": len(payload["protected_objects"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

