#!/usr/bin/env python3
"""Probe Blender's runtime capabilities without mutating the current scene."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

import bpy


SCHEMA_VERSION = "1.0"


def _enum_identifiers(rna_type: Any, property_name: str) -> list[str]:
    try:
        prop = rna_type.bl_rna.properties[property_name]
        return sorted(item.identifier for item in prop.enum_items)
    except Exception:
        return []


def _rna_type_names() -> list[str]:
    result: list[str] = []
    for name in dir(bpy.types):
        if name.startswith("_"):
            continue
        value = getattr(bpy.types, name, None)
        if value is not None and hasattr(value, "bl_rna"):
            result.append(name)
    return sorted(result)


def _node_type_names(prefix: str) -> list[str]:
    return sorted(
        name
        for name in dir(bpy.types)
        if name.startswith(prefix) and hasattr(getattr(bpy.types, name, None), "bl_rna")
    )


def _render_engine_names() -> list[str]:
    """Collect dynamic render engines without changing the user's active scene."""

    result = set(_enum_identifiers(bpy.types.RenderSettings, "engine"))
    for engine_class in bpy.types.RenderEngine.__subclasses__():
        identifier = getattr(engine_class, "bl_idname", "")
        if identifier:
            result.add(str(identifier))

    probe_scene = bpy.data.scenes.new("__BPS_CAPABILITY_PROBE__")
    try:
        candidates = {
            "BLENDER_EEVEE",
            "BLENDER_EEVEE_NEXT",
            "BLENDER_WORKBENCH",
            "CYCLES",
        }
        candidates.update(result)
        for identifier in candidates:
            try:
                probe_scene.render.engine = identifier
                result.add(identifier)
            except (TypeError, ValueError):
                pass
    finally:
        bpy.data.scenes.remove(probe_scene)
    return sorted(result)


def _operator_index() -> dict[str, list[str]]:
    operators: dict[str, list[str]] = {}
    for module_name in sorted(name for name in dir(bpy.ops) if not name.startswith("_")):
        try:
            module = getattr(bpy.ops, module_name)
            names = sorted(name for name in dir(module) if not name.startswith("_"))
        except Exception:
            continue
        if names:
            operators[module_name] = names
    return operators


def _enabled_addons() -> list[str]:
    try:
        return sorted(str(name) for name in bpy.context.preferences.addons.keys())
    except Exception:
        return []


def _extension_repositories() -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    try:
        for repo in bpy.context.preferences.extensions.repos:
            repos.append(
                {
                    "name": str(getattr(repo, "name", "")),
                    "module": str(getattr(repo, "module", "")),
                    "directory": str(getattr(repo, "directory", "")),
                    "enabled": bool(getattr(repo, "enabled", True)),
                    "remote_url": str(getattr(repo, "remote_url", "")),
                }
            )
    except Exception:
        pass
    return repos


def _cycles_devices() -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    try:
        addon = bpy.context.preferences.addons.get("cycles")
        if addon is None:
            return devices
        prefs = addon.preferences
        prefs.get_devices()
        for device in prefs.devices:
            devices.append(
                {
                    "name": str(device.name),
                    "type": str(device.type),
                    "id": str(device.id),
                }
            )
    except Exception:
        pass
    return devices


def _runtime_blender_executable() -> tuple[str, str]:
    """Resolve Blender's launcher even when Blender 5.2 reports embedded Python as binary_path."""

    raw_candidates = [
        (str(getattr(bpy.app, "binary_path", "") or ""), "bpy.app.binary_path"),
        (str(sys.argv[0] or ""), "sys.argv[0]"),
        (str(sys.executable or ""), "sys.executable"),
    ]
    seen: set[Path] = set()
    paths: list[tuple[Path, str]] = []
    for raw, source in raw_candidates:
        if not raw:
            continue
        try:
            path = Path(raw).expanduser().resolve()
        except OSError:
            continue
        if path in seen:
            continue
        seen.add(path)
        paths.append((path, source))
        if path.is_file() and path.stem.lower().startswith("blender"):
            return str(path), source

    # Blender 5.2 may report .../Blender/5.2/python/bin/python.exe.  Search a bounded
    # set of ancestors instead of assuming a single platform-specific installation layout.
    launcher_names = ("blender.exe", "blender")
    for path, source in paths:
        for ancestor in list(path.parents)[:7]:
            for launcher_name in launcher_names:
                launcher = ancestor / launcher_name
                if launcher.is_file():
                    return str(launcher.resolve()), f"{source} ancestor search"

    fallback = paths[0][0] if paths else Path(sys.executable).resolve()
    return str(fallback), "unresolved embedded runtime fallback"


def collect_capabilities() -> dict[str, Any]:
    rna_types = _rna_type_names()
    executable, executable_source = _runtime_blender_executable()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "blender_runtime_rna",
        "blender": {
            "version": bpy.app.version_string,
            "version_tuple": list(bpy.app.version),
            "build_hash": str(getattr(bpy.app, "build_hash", b"").decode("utf-8", "ignore")
                              if isinstance(getattr(bpy.app, "build_hash", ""), bytes)
                              else getattr(bpy.app, "build_hash", "")),
            "executable": executable,
            "executable_source": executable_source,
            "python_executable": os.path.abspath(sys.executable),
            "background": bool(bpy.app.background),
        },
        "capabilities": {
            "modifier_types": _enum_identifiers(bpy.types.Modifier, "type"),
            "constraint_types": _enum_identifiers(bpy.types.Constraint, "type"),
            "object_types": _enum_identifiers(bpy.types.Object, "type"),
            "render_engines": _render_engine_names(),
            "rna_types": rna_types,
            "operators": _operator_index(),
            "geometry_nodes": _node_type_names("GeometryNode"),
            "shader_nodes": _node_type_names("ShaderNode"),
            "compositor_nodes": _node_type_names("CompositorNode"),
            "enabled_addons": _enabled_addons(),
            "extension_repositories": _extension_repositories(),
            "cycles_devices": _cycles_devices(),
        },
    }


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = collect_capabilities()
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "CAPABILITY_PROBE "
        + json.dumps(
            {
                "output": str(output),
                "version": payload["blender"]["version"],
                "modifier_count": len(payload["capabilities"]["modifier_types"]),
                "operator_modules": len(payload["capabilities"]["operators"]),
                "rna_type_count": len(payload["capabilities"]["rna_types"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
