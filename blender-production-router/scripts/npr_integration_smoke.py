#!/usr/bin/env python3
"""Build and render both NPR systems in an isolated background Blender.

This script refuses to run in a visible Blender process. It validates actual
node graphs and writes uniquely named preview renders plus a JSON report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import bpy
from mathutils import Vector


def _script_args() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clear_test_objects() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


def _point_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _setup_camera_and_lights() -> bpy.types.Object:
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BPS NPR Test World")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.50, 0.52, 0.55, 1.0)
    background.inputs["Strength"].default_value = 0.45

    bpy.ops.object.camera_add(location=(0.0, -6.2, 0.55))
    camera = bpy.context.active_object
    camera.name = "BPS NPR Test Camera"
    camera.data.lens = 58.0
    _point_at(camera, Vector((0.0, 0.0, 0.45)))
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(-3.0, -4.0, 5.0))
    key = bpy.context.active_object
    key.name = "BPS NPR Key"
    key.data.energy = 850.0
    key.data.shape = "DISK"
    key.data.size = 4.0
    _point_at(key, Vector((0.0, 0.0, 0.3)))

    bpy.ops.object.light_add(type="AREA", location=(3.5, -1.0, 1.5))
    fill = bpy.context.active_object
    fill.name = "BPS NPR Fill"
    fill.data.energy = 300.0
    fill.data.size = 3.0
    _point_at(fill, Vector((0.0, 0.0, 0.3)))
    return camera


def _create_subject(name: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_monkey_add(location=(0.0, 0.0, 0.35))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (1.28, 1.28, 1.28)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    subdivision = obj.modifiers.new("BPS Test Subdivision", "SUBSURF")
    subdivision.levels = 2
    subdivision.render_levels = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=subdivision.name)
    obj.select_set(True)
    return obj


def _configure_render(path: Path, *, samples: int | None = None) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = 384
    scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(path)
    scene.render.image_settings.color_mode = "RGBA"
    if samples is not None and hasattr(scene, "cycles"):
        scene.cycles.samples = samples
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.device = "CPU"


def _render_and_measure(path: Path, *, samples: int | None = None) -> dict[str, Any]:
    _configure_render(path, samples=samples)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.get("Render Result")
    loaded_from_disk = False
    if image is None or not image.has_data:
        if not path.exists():
            raise RuntimeError("Render Result and written preview are both missing")
        image = bpy.data.images.load(str(path), check_existing=False)
        loaded_from_disk = True
    pixels = list(image.pixels)
    luminance: list[float] = []
    dark = 0
    for index in range(0, len(pixels), 4):
        red, green, blue, alpha = pixels[index : index + 4]
        if alpha <= 0.001:
            continue
        value = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        luminance.append(value)
        if value < 0.08:
            dark += 1
    if not luminance:
        raise RuntimeError("Rendered image has no visible pixels")
    mean = sum(luminance) / len(luminance)
    variance = sum((value - mean) ** 2 for value in luminance) / len(luminance)
    result = {
        "path": str(path),
        "width": image.size[0],
        "height": image.size[1],
        "luminance_min": min(luminance),
        "luminance_max": max(luminance),
        "luminance_mean": mean,
        "luminance_stddev": math.sqrt(variance),
        "dark_pixel_ratio": dark / len(luminance),
    }
    result["nonblank"] = (
        result["luminance_max"] - result["luminance_min"] > 0.08
        and result["luminance_stddev"] > 0.02
    )
    if loaded_from_disk:
        bpy.data.images.remove(image)
    return result


def _input_source(node: bpy.types.Node, socket_name: str) -> tuple[str, str] | None:
    socket = node.inputs.get(socket_name)
    if socket is None or not socket.is_linked:
        return None
    link = socket.links[0]
    return (link.from_node.bl_idname, link.from_socket.name)


def _validate_eevee(module: ModuleType, result: dict[str, Any]) -> dict[str, Any]:
    group = bpy.data.node_groups[result["outline_group"]]
    toon = bpy.data.materials[result["toon_material"]]
    outline = bpy.data.materials[result["outline_material"]]
    node_types = [node.bl_idname for node in group.nodes]
    required = {
        "GeometryNodeExtrudeMesh",
        "GeometryNodeSeparateGeometry",
        "GeometryNodeSetPosition",
        "GeometryNodeFlipFaces",
        "GeometryNodeSetMaterial",
        "GeometryNodeJoinGeometry",
        "GeometryNodeSwitch",
        "GeometryNodeInputPosition",
        "GeometryNodeInputNormal",
    }
    noise = next(node for node in group.nodes if node.name == "BPS Position-Driven Wobble")
    normal_scale = next(
        node for node in group.nodes if node.name == "BPS Project Wobble Along Normal"
    )
    palette = next(
        node for node in toon.node_tree.nodes if node.name == "BPS Constant Toon Palette"
    )
    checks = {
        "engine_is_eevee": bpy.context.scene.render.engine in {
            "BLENDER_EEVEE",
            "BLENDER_EEVEE_NEXT",
        },
        "required_geometry_nodes": required.issubset(set(node_types)),
        "position_drives_noise": _input_source(noise, "Vector")
        == ("GeometryNodeInputPosition", "Position"),
        "normal_drives_wobble": _input_source(normal_scale, "Vector")
        == ("GeometryNodeInputNormal", "Normal"),
        "shader_to_rgb_exists": any(
            node.bl_idname == "ShaderNodeShaderToRGB" for node in toon.node_tree.nodes
        ),
        "palette_is_constant": palette.color_ramp.interpolation == "CONSTANT",
        "outline_backface_culling": bool(
            getattr(outline, "use_backface_culling", False)
        ),
        "owned_modifier_exists": any(
            modifier.type == "NODES"
            and modifier.node_group is group
            for obj in bpy.context.scene.objects
            for modifier in obj.modifiers
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "node_type_count": len(node_types),
        "builder_result": result,
    }


def _validate_cycles(result: dict[str, Any]) -> dict[str, Any]:
    sample_group = bpy.data.node_groups[result["sample_group"]]
    look_group = bpy.data.node_groups[result["look_group"]]
    material = bpy.data.materials[result["material"]]
    raycasts = [
        node for node in sample_group.nodes if node.bl_idname == "ShaderNodeRaycast"
    ]
    transforms = [
        node
        for node in sample_group.nodes
        if node.bl_idname == "ShaderNodeVectorTransform"
    ]
    sample_instances = [
        node
        for node in look_group.nodes
        if node.bl_idname == "ShaderNodeGroup" and node.node_tree is sample_group
    ]
    offsets = sorted(
        tuple(round(value, 4) for value in node.inputs["Offset"].default_value)
        for node in sample_instances
    )
    expected_offsets = sorted(
        [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)]
    )
    multiply_nodes = [
        node
        for node in look_group.nodes
        if node.bl_idname == "ShaderNodeMath" and node.operation == "MULTIPLY"
    ]
    checks = {
        "engine_is_cycles": bpy.context.scene.render.engine == "CYCLES",
        "one_sample_raycast": len(raycasts) == 1,
        "raycast_only_local": len(raycasts) == 1 and bool(raycasts[0].only_local),
        "camera_to_world_transform": len(transforms) == 1
        and transforms[0].vector_type == "VECTOR"
        and transforms[0].convert_from == "CAMERA"
        and transforms[0].convert_to == "WORLD",
        "four_sample_instances": len(sample_instances) == 4,
        "offsets_are_cardinal": offsets == expected_offsets,
        "three_mask_multiplies": len(multiply_nodes) == 3,
        "toon_bsdf_exists": any(
            node.bl_idname == "ShaderNodeBsdfToon" for node in look_group.nodes
        ),
        "no_shader_to_rgb": not any(
            node.bl_idname == "ShaderNodeShaderToRGB"
            for tree in (sample_group, look_group, material.node_tree)
            for node in tree.nodes
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "sample_node_count": len(sample_group.nodes),
        "look_node_count": len(look_group.nodes),
        "builder_result": result,
    }


def main() -> int:
    if not bpy.app.background:
        raise RuntimeError("This integration smoke test may only run in background Blender")

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(_script_args())
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    suite_root = Path(__file__).resolve().parents[2]
    eevee_module = _load_module(
        "bps_npr_eevee",
        suite_root / "blender-npr-eevee" / "scripts" / "build_eevee_npr.py",
    )
    cycles_module = _load_module(
        "bps_npr_cycles",
        suite_root / "blender-npr-cycles" / "scripts" / "build_cycles_npr.py",
    )

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    eevee_preview = output.parent / f"npr_eevee_preview_{stamp}.png"
    cycles_preview = output.parent / f"npr_cycles_preview_{stamp}.png"

    _clear_test_objects()
    _setup_camera_and_lights()
    eevee_subject = _create_subject("BPS Eevee NPR Subject")
    eevee_result = eevee_module.apply_to_objects(
        [eevee_subject],
        width=0.055,
        noise_scale=4.5,
        wobble_amount=0.003,
        replace_material=True,
    )
    eevee_validation = _validate_eevee(eevee_module, eevee_result)
    eevee_render = _render_and_measure(eevee_preview)

    _clear_test_objects()
    _setup_camera_and_lights()
    cycles_subject = _create_subject("BPS Cycles NPR Subject")
    cycles_result = cycles_module.apply_to_objects(
        [cycles_subject],
        width=0.035,
        ray_length=100.0,
        only_local=True,
        replace_material=True,
    )
    cycles_validation = _validate_cycles(cycles_result)
    cycles_render = _render_and_measure(cycles_preview, samples=12)

    statuses = [
        eevee_validation["status"] == "PASS",
        cycles_validation["status"] == "PASS",
        bool(eevee_render["nonblank"]),
        bool(cycles_render["nonblank"]),
    ]
    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "status": "PASS" if all(statuses) else "FAIL",
        "eevee": {
            "validation": eevee_validation,
            "render": eevee_render,
        },
        "cycles": {
            "validation": cycles_validation,
            "render": cycles_render,
        },
    }
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "NPR_INTEGRATION_SMOKE "
        + json.dumps(
            {
                "output": str(output),
                "status": report["status"],
                "eevee_preview": str(eevee_preview),
                "cycles_preview": str(cycles_preview),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
