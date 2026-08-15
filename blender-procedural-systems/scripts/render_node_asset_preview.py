#!/usr/bin/env python3
"""Render a temporary review image for a node asset without saving the source file."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Expected output image path after --")
    output_path = Path(args[0]).expanduser().resolve()
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("No mesh object found")

    points = [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        for corner in obj.bound_box
    ]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    extent = max(maximum - minimum)

    camera_data = bpy.data.cameras.new("NODE_ASSET_REVIEW_CAMERA")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + Vector((1.8, -2.6, 1.35)).normalized() * extent * 3.2
    camera_data.lens = 58
    _look_at(camera, center)
    bpy.context.scene.camera = camera

    key_data = bpy.data.lights.new("NODE_ASSET_REVIEW_KEY", "AREA")
    key = bpy.data.objects.new(key_data.name, key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = center + Vector((-2.2, -2.4, 3.5)) * extent
    key_data.energy = 900.0 * max(extent, 0.5)
    key_data.shape = "DISK"
    key_data.size = extent * 2.0
    _look_at(key, center)

    rim_data = bpy.data.lights.new("NODE_ASSET_REVIEW_RIM", "AREA")
    rim = bpy.data.objects.new(rim_data.name, rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim.location = center + Vector((2.0, 1.5, 2.5)) * extent
    rim_data.energy = 500.0 * max(extent, 0.5)
    rim_data.size = extent * 1.4
    _look_at(rim, center)

    world = bpy.context.scene.world or bpy.data.worlds.new("NODE_ASSET_REVIEW_WORLD")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.04, 0.055, 1.0)
    background.inputs["Strength"].default_value = 0.28

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = str(output_path)
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
