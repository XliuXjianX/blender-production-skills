"""Native-component forced-perspective portal generator for Blender 5.2+.

Python orchestrates a Boolean frame, an Array-owned stair flight, optional
Collection Instances, and separate preview helpers. The script never clears
unowned data and is safe to rerun when its owned data remains intact.
"""

from __future__ import annotations

import json
import math
from typing import Any

import bmesh
import bpy
from mathutils import Vector


GENERATOR_ID = "codex.blender.forced-perspective-portal"
GENERATOR_SCHEMA = "2.0"
OWNER_KEY = "codex_generator_id"
SCHEMA_KEY = "codex_generator_schema"


SETTINGS: dict[str, Any] = {
    "collection_name": "PORTAL_GENERATED",
    "preview_collection_name": "PORTAL_PREVIEW",
    "instance_collection_name": "PORTAL_INSTANCES",

    # Main frame.
    "outer_width": 3.20,
    "outer_height": 5.00,
    "opening_width": 1.82,
    "opening_height": 3.86,
    "frame_depth": 0.72,
    "frame_bevel": 0.035,

    # Straight stair flight. Array constant offset owns run and rise.
    "step_count": 18,
    "step_run": 0.235,
    "step_rise": 0.158,
    "stair_width_front": 1.54,
    "stair_width_back": 0.72,
    "stair_offset_x": 0.16,
    "step_overlap": 0.006,
    "step_bevel": 0.008,
    "use_object_offset_taper": True,

    # Tunnel.
    "tunnel_wall_thickness": 0.13,
    "tunnel_extra_depth": 0.65,
    "tunnel_back_width": 0.82,
    "add_back_blocker": True,

    # Preview lookdev is opt-in and separate from production instances.
    "add_preview_materials": False,
    "add_preview_light": False,
    "preview_light_energy": 850.0,

    # Optional collection instances. Example:
    # {"name": "PORTAL_FAR_A", "location": (8, 20, 0), "scale": 0.45}
    "distant_instances": [],
}


def _tag(id_block: Any) -> Any:
    id_block[OWNER_KEY] = GENERATOR_ID
    id_block[SCHEMA_KEY] = GENERATOR_SCHEMA
    return id_block


def _is_owned(id_block: Any) -> bool:
    return id_block is not None and id_block.get(OWNER_KEY) == GENERATOR_ID


def _require_owned(id_block: Any, label: str) -> None:
    if not _is_owned(id_block):
        name = getattr(id_block, "name", "<unnamed>")
        raise RuntimeError(f"Refusing to modify unowned {label}: {name}")


def _assert_name_available(collection: Any, name: str, label: str) -> None:
    existing = collection.get(name)
    if existing is not None and not _is_owned(existing):
        raise RuntimeError(f"Name conflict with unowned {label}: {name}")


def _capture_context() -> dict[str, Any]:
    active = bpy.context.view_layer.objects.active
    return {
        "active_name": active.name if active else None,
        "active_mode": active.mode if active else None,
        "selected_names": [obj.name for obj in bpy.context.selected_objects],
    }


def _restore_context(context: dict[str, Any]) -> None:
    active_name = context.get("active_name")
    active = bpy.data.objects.get(active_name) if active_name else None
    if active is not None:
        bpy.context.view_layer.objects.active = active
    if context.get("active_mode") == "OBJECT":
        selected_names = set(context.get("selected_names", []))
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj.name in selected_names)


def _preflight_owned_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    _require_owned(collection, "collection")
    for obj in collection.objects:
        _require_owned(obj, "collection object")
        outside = [item.name for item in obj.users_collection if item != collection]
        if outside:
            raise RuntimeError(
                f"Owned object {obj.name} is linked outside {collection.name}: {outside}"
            )
    for child in collection.children:
        _require_owned(child, "child collection")


def _ensure_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = _tag(bpy.data.collections.new(name))
        bpy.context.scene.collection.children.link(collection)
    else:
        _require_owned(collection, "collection")
        if collection.name not in {item.name for item in bpy.context.scene.collection.children}:
            bpy.context.scene.collection.children.link(collection)
    return collection


def _remove_owned_object(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    _require_owned(obj, "object")
    if any(item != collection for item in obj.users_collection):
        raise RuntimeError(f"Refusing to remove multiply-linked object: {obj.name}")
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is None or data.users != 0 or not _is_owned(data):
        return
    if isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)
    elif isinstance(data, bpy.types.Light):
        bpy.data.lights.remove(data)
    elif isinstance(data, bpy.types.Curve):
        bpy.data.curves.remove(data)


def _clear_collection(collection: bpy.types.Collection) -> None:
    _require_owned(collection, "collection")
    if collection.children:
        raise RuntimeError(f"Owned collection has unexpected child collections: {collection.name}")
    for obj in list(collection.objects):
        _remove_owned_object(obj, collection)


def _link_object(obj: bpy.types.Object, collection: bpy.types.Collection) -> bpy.types.Object:
    collection.objects.link(obj)
    return obj


def _recalc_normals(mesh: bpy.types.Mesh) -> None:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def _mesh_object(
    name: str,
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    collection: bpy.types.Collection,
    material: bpy.types.Material | None = None,
) -> bpy.types.Object:
    mesh_name = f"{name}_Mesh"
    _assert_name_available(bpy.data.objects, name, "object")
    _assert_name_available(bpy.data.meshes, mesh_name, "mesh")
    mesh = _tag(bpy.data.meshes.new(mesh_name))
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    _recalc_normals(mesh)
    obj = _tag(bpy.data.objects.new(name, mesh))
    _link_object(obj, collection)
    if material is not None:
        obj.data.materials.append(material)
    return obj


def _empty_object(
    name: str,
    collection: bpy.types.Collection,
    display_type: str = "PLAIN_AXES",
) -> bpy.types.Object:
    _assert_name_available(bpy.data.objects, name, "object")
    obj = _tag(bpy.data.objects.new(name, None))
    obj.empty_display_type = display_type
    _link_object(obj, collection)
    return obj


def _box_geometry(
    size: tuple[float, float, float],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    sx, sy, sz = (value * 0.5 for value in size)
    verts = [
        (-sx, -sy, -sz),
        (sx, -sy, -sz),
        (sx, sy, -sz),
        (-sx, sy, -sz),
        (-sx, -sy, sz),
        (sx, -sy, sz),
        (sx, sy, sz),
        (-sx, sy, sz),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return verts, faces


def _add_box(
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    collection: bpy.types.Collection,
    material: bpy.types.Material | None = None,
) -> bpy.types.Object:
    verts, faces = _box_geometry(size)
    obj = _mesh_object(name, verts, faces, collection, material)
    obj.location = location
    return obj


def _add_bevel(
    obj: bpy.types.Object,
    name: str,
    width: float,
    segments: int = 3,
    angle_degrees: float = 25.0,
) -> bpy.types.Modifier | None:
    if width <= 0:
        return None
    modifier = obj.modifiers.new(name=name, type="BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    modifier.angle_limit = math.radians(angle_degrees)
    if hasattr(modifier, "harden_normals"):
        modifier.harden_normals = True
    return modifier


def _owned_material(name: str) -> bpy.types.Material:
    material = bpy.data.materials.get(name)
    if material is None:
        material = _tag(bpy.data.materials.new(name))
    else:
        _require_owned(material, "material")
    material.use_nodes = True
    material.node_tree.nodes.clear()
    return material


def _stone_material(
    name: str,
    light_color: tuple[float, float, float, float],
    dark_color: tuple[float, float, float, float],
    roughness: float,
    bump_strength: float,
) -> bpy.types.Material:
    material = _owned_material(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = dark_color
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = light_color
    bsdf.inputs["Roughness"].default_value = roughness
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.075
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def _simple_material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
) -> bpy.types.Material:
    material = _owned_material(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def _preview_materials() -> dict[str, bpy.types.Material | None]:
    if not SETTINGS["add_preview_materials"]:
        return {"frame": None, "stairs": None, "tunnel": None}
    for name in ("MAT_Portal_Stone", "MAT_Stair_Stone", "MAT_Tunnel_Dark"):
        existing = bpy.data.materials.get(name)
        if existing is not None:
            _require_owned(existing, "material")
    return {
        "frame": _stone_material(
            "MAT_Portal_Stone",
            (0.82, 0.72, 0.57, 1.0),
            (0.40, 0.31, 0.22, 1.0),
            0.66,
            0.13,
        ),
        "stairs": _stone_material(
            "MAT_Stair_Stone",
            (0.42, 0.39, 0.34, 1.0),
            (0.16, 0.15, 0.14, 1.0),
            0.78,
            0.10,
        ),
        "tunnel": _simple_material(
            "MAT_Tunnel_Dark", (0.008, 0.009, 0.012, 1.0), 0.96
        ),
    }


def _create_boolean_frame(
    collection: bpy.types.Collection,
    material: bpy.types.Material | None,
) -> tuple[bpy.types.Object, bpy.types.Object]:
    outer_width = float(SETTINGS["outer_width"])
    outer_height = float(SETTINGS["outer_height"])
    opening_width = float(SETTINGS["opening_width"])
    opening_height = float(SETTINGS["opening_height"])
    depth = float(SETTINGS["frame_depth"])

    host = _add_box(
        "PORTAL_FRAME_HOST",
        (outer_width, depth, outer_height),
        (0.0, 0.0, outer_height * 0.5),
        collection,
        material,
    )
    cutter_bottom = -0.20
    cutter_top = opening_height
    cutter_height = cutter_top - cutter_bottom
    cutter = _add_box(
        "PORTAL_FRAME_CUTTER",
        (opening_width, depth + 0.40, cutter_height),
        (0.0, 0.0, (cutter_top + cutter_bottom) * 0.5),
        collection,
        None,
    )
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    cutter["component_role"] = "boolean_cutter"

    boolean = host.modifiers.new("PORTAL_OPENING_BOOLEAN", "BOOLEAN")
    boolean.operation = "DIFFERENCE"
    boolean.solver = "EXACT"
    boolean.object = cutter
    _add_bevel(
        host,
        "PORTAL_FRAME_BEVEL",
        float(SETTINGS["frame_bevel"]),
        segments=4,
        angle_degrees=18.0,
    )
    host["native_system"] = "BOOLEAN"
    host["source_objects"] = json.dumps([host.name, cutter.name])
    host["application_policy"] = "keep_non_destructive"
    return host, cutter


def _create_array_stairs(
    collection: bpy.types.Collection,
    material: bpy.types.Material | None,
) -> tuple[bpy.types.Object, bpy.types.Object | None, float, float, float]:
    count = max(2, int(SETTINGS["step_count"]))
    run = float(SETTINGS["step_run"])
    rise = float(SETTINGS["step_rise"])
    overlap = max(0.0, float(SETTINGS["step_overlap"]))
    width_front = float(SETTINGS["stair_width_front"])
    width_back = float(SETTINGS["stair_width_back"])
    y_start = float(SETTINGS["frame_depth"]) * 0.5 + 0.055

    source = _add_box(
        "PORTAL_STAIR_SOURCE",
        (width_front, run + overlap, rise + overlap),
        (
            float(SETTINGS["stair_offset_x"]),
            y_start + run * 0.5,
            rise * 0.5,
        ),
        collection,
        material,
    )
    array = source.modifiers.new("PORTAL_STAIR_ARRAY", "ARRAY")
    array.count = count
    array.use_relative_offset = False
    array.use_constant_offset = True
    array.constant_offset_displace = (0.0, run, rise)
    array.use_merge_vertices = False

    taper = None
    if bool(SETTINGS["use_object_offset_taper"]) and width_back > 0 and width_back != width_front:
        taper = _empty_object("PORTAL_STAIR_TAPER", collection, "CUBE")
        taper.location = source.location
        taper.empty_display_size = 0.18
        per_step_scale = (width_back / width_front) ** (1.0 / (count - 1))
        taper.scale = (per_step_scale, 1.0, 1.0)
        taper.hide_render = True
        taper["component_role"] = "array_object_offset"
        array.use_object_offset = True
        array.offset_object = taper

    _add_bevel(
        source,
        "PORTAL_STAIR_BEVEL",
        float(SETTINGS["step_bevel"]),
        segments=2,
        angle_degrees=28.0,
    )
    source["native_system"] = "ARRAY"
    source["source_objects"] = json.dumps([source.name])
    source["semantic_inputs"] = json.dumps(
        {
            "count": count,
            "constant_offset": [0.0, run, rise],
            "front_width": width_front,
            "back_width": width_back,
            "object_offset_taper": taper.name if taper else None,
        }
    )
    source["application_policy"] = "keep_non_destructive"
    total_run = run * count
    total_rise = rise * count
    return source, taper, y_start, total_run, total_rise


def _create_tunnel(
    collection: bpy.types.Collection,
    material: bpy.types.Material | None,
    total_run: float,
    total_rise: float,
) -> tuple[list[bpy.types.Object], float]:
    front_y = float(SETTINGS["frame_depth"]) * 0.5 - 0.02
    depth = total_run + float(SETTINGS["tunnel_extra_depth"])
    back_y = front_y + depth
    front_width = float(SETTINGS["opening_width"]) * 0.985
    front_height = float(SETTINGS["opening_height"]) * 0.985
    back_width = min(float(SETTINGS["tunnel_back_width"]), front_width * 0.72)
    back_height = min(front_height * 0.985, max(total_rise + 0.48, front_height * 0.76))
    thickness = float(SETTINGS["tunnel_wall_thickness"])

    prism_faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    left_verts = [
        (-front_width * 0.5 - thickness, front_y, 0.0),
        (-front_width * 0.5, front_y, 0.0),
        (-front_width * 0.5, front_y, front_height),
        (-front_width * 0.5 - thickness, front_y, front_height),
        (-back_width * 0.5 - thickness, back_y, 0.0),
        (-back_width * 0.5, back_y, 0.0),
        (-back_width * 0.5, back_y, back_height),
        (-back_width * 0.5 - thickness, back_y, back_height),
    ]
    right_verts = [
        (front_width * 0.5, front_y, 0.0),
        (front_width * 0.5 + thickness, front_y, 0.0),
        (front_width * 0.5 + thickness, front_y, front_height),
        (front_width * 0.5, front_y, front_height),
        (back_width * 0.5, back_y, 0.0),
        (back_width * 0.5 + thickness, back_y, 0.0),
        (back_width * 0.5 + thickness, back_y, back_height),
        (back_width * 0.5, back_y, back_height),
    ]
    ceiling_verts = [
        (-front_width * 0.5, front_y, front_height),
        (front_width * 0.5, front_y, front_height),
        (front_width * 0.5, front_y, front_height + thickness),
        (-front_width * 0.5, front_y, front_height + thickness),
        (-back_width * 0.5, back_y, back_height),
        (back_width * 0.5, back_y, back_height),
        (back_width * 0.5, back_y, back_height + thickness),
        (-back_width * 0.5, back_y, back_height + thickness),
    ]

    parts = [
        _mesh_object("PORTAL_TUNNEL_LEFT", left_verts, prism_faces, collection, material),
        _mesh_object("PORTAL_TUNNEL_RIGHT", right_verts, prism_faces, collection, material),
        _mesh_object("PORTAL_TUNNEL_CEILING", ceiling_verts, prism_faces, collection, material),
        _add_box(
            "PORTAL_TUNNEL_FLOOR",
            (front_width + 2 * thickness, depth, 0.08),
            (0.0, front_y + depth * 0.5, -0.04),
            collection,
            material,
        ),
    ]
    if bool(SETTINGS["add_back_blocker"]):
        parts.append(
            _add_box(
                "PORTAL_TUNNEL_BACK",
                (back_width + 2 * thickness, 0.10, back_height + thickness),
                (0.0, back_y + 0.05, (back_height + thickness) * 0.5),
                collection,
                material,
            )
        )
    for part in parts:
        part["native_system"] = "MESH_DATA"
        part["code_role"] = "direct_topology_exception"
        part["fallback_reason"] = "unique tapered tunnel boundary surfaces"
    return parts, back_y


def _aim_object(
    obj: bpy.types.Object,
    target: tuple[float, float, float],
    track_axis: str = "-Z",
    up_axis: str = "Y",
) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat(track_axis, up_axis).to_euler()


def _add_preview_light(collection: bpy.types.Collection) -> bpy.types.Object:
    name = "PORTAL_PREVIEW_AREA"
    _assert_name_available(bpy.data.objects, name, "object")
    _assert_name_available(bpy.data.lights, name, "light")
    light_data = _tag(bpy.data.lights.new(name, type="AREA"))
    light_data.energy = float(SETTINGS["preview_light_energy"])
    light_data.shape = "RECTANGLE"
    light_data.size = float(SETTINGS["opening_width"]) * 1.35
    if hasattr(light_data, "size_y"):
        light_data.size_y = float(SETTINGS["opening_height"]) * 0.72
    light_obj = _tag(bpy.data.objects.new(name, light_data))
    _link_object(light_obj, collection)
    light_obj.location = (0.0, -1.55, float(SETTINGS["opening_height"]) * 0.64)
    _aim_object(light_obj, (0.10, 2.0, float(SETTINGS["opening_height"]) * 0.50))
    return light_obj


def _create_distant_instances(
    source_collection: bpy.types.Collection,
    instance_collection: bpy.types.Collection,
) -> list[bpy.types.Object]:
    instances = []
    for index, spec in enumerate(SETTINGS.get("distant_instances", [])):
        name = str(spec.get("name") or f"PORTAL_INSTANCE_{index:02d}")
        instance = _empty_object(name, instance_collection, "CUBE")
        instance.instance_type = "COLLECTION"
        instance.instance_collection = source_collection
        instance.location = tuple(spec.get("location", (0.0, 0.0, 0.0)))
        scale = spec.get("scale", 1.0)
        if isinstance(scale, (int, float)):
            instance.scale = (float(scale),) * 3
        else:
            instance.scale = tuple(scale)
        instance["native_system"] = "COLLECTION_INSTANCE"
        instances.append(instance)
    return instances


def _construction_graph(
    frame: bpy.types.Object,
    cutter: bpy.types.Object,
    stairs: bpy.types.Object,
    taper: bpy.types.Object | None,
    tunnel_parts: list[bpy.types.Object],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "parts": [
            {
                "id": "portal_frame",
                "native_system": "BOOLEAN",
                "source_objects": [frame.name, cutter.name],
                "semantic_inputs": {
                    "outer_width": SETTINGS["outer_width"],
                    "outer_height": SETTINGS["outer_height"],
                    "opening_width": SETTINGS["opening_width"],
                    "opening_height": SETTINGS["opening_height"],
                },
                "generated_dependents": [frame.name],
                "code_role": "orchestration",
                "application_policy": "keep_non_destructive",
            },
            {
                "id": "stair_flight",
                "native_system": "ARRAY",
                "source_objects": [stairs.name] + ([taper.name] if taper else []),
                "semantic_inputs": {
                    "count": SETTINGS["step_count"],
                    "constant_offset": [0.0, SETTINGS["step_run"], SETTINGS["step_rise"]],
                },
                "generated_dependents": ["evaluated_stair_flight"],
                "code_role": "orchestration",
                "application_policy": "keep_non_destructive",
            },
            {
                "id": "tunnel_shell",
                "native_system": "MESH_DATA",
                "source_objects": [item.name for item in tunnel_parts],
                "semantic_inputs": {"tapered_depth": True},
                "generated_dependents": [item.name for item in tunnel_parts],
                "code_role": "direct_topology_exception",
                "application_policy": "keep_non_destructive",
                "fallback_reason": "unique tapered tunnel boundary surfaces",
            },
        ],
        "relationships": [
            {
                "a": "portal_frame",
                "b": "stair_flight",
                "type": "mechanical_seam",
                "validation": ["clearance", "entry alignment", "ground contact"],
            },
            {
                "a": "stair_flight",
                "b": "tunnel_shell",
                "type": "embedded_component",
                "validation": ["side clearance", "ceiling clearance", "support"],
            },
        ],
    }


def build_portal() -> dict[str, Any]:
    context = _capture_context()
    active = bpy.context.view_layer.objects.active
    if active is not None and _is_owned(active) and active.mode != "OBJECT":
        raise RuntimeError("Leave Edit/Sculpt mode on the generated portal before rerunning")

    collection_names = (
        SETTINGS["collection_name"],
        SETTINGS["preview_collection_name"],
        SETTINGS["instance_collection_name"],
    )
    for name in collection_names:
        _preflight_owned_collection(str(name))
    if SETTINGS["add_preview_materials"]:
        for name in ("MAT_Portal_Stone", "MAT_Stair_Stone", "MAT_Tunnel_Dark"):
            material = bpy.data.materials.get(name)
            if material is not None:
                _require_owned(material, "material")

    production = _ensure_collection(str(SETTINGS["collection_name"]))
    preview = _ensure_collection(str(SETTINGS["preview_collection_name"]))
    instances_collection = _ensure_collection(str(SETTINGS["instance_collection_name"]))
    try:
        for collection in (production, preview, instances_collection):
            _clear_collection(collection)

        materials = _preview_materials()
        rig = _empty_object("PORTAL_RIG", production, "CUBE")
        rig.empty_display_size = 0.42
        rig["instructions"] = (
            "Edit SETTINGS and rerun. Array owns the stair flight; use Collection Instances for copies."
        )

        frame, cutter = _create_boolean_frame(production, materials["frame"])
        stairs, taper, y_start, total_run, total_rise = _create_array_stairs(
            production, materials["stairs"]
        )
        tunnel_parts, back_y = _create_tunnel(
            production, materials["tunnel"], total_run, total_rise
        )
        production_objects = [frame, cutter, stairs] + tunnel_parts
        if taper is not None:
            production_objects.append(taper)
        for obj in production_objects:
            obj.parent = rig

        preview_light = None
        if SETTINGS["add_preview_light"]:
            preview_light = _add_preview_light(preview)

        distant_instances = _create_distant_instances(production, instances_collection)
        graph = _construction_graph(frame, cutter, stairs, taper, tunnel_parts)
        rig["construction_graph"] = json.dumps(graph)
        rig["outer_width"] = SETTINGS["outer_width"]
        rig["outer_height"] = SETTINGS["outer_height"]
        rig["opening_width"] = SETTINGS["opening_width"]
        rig["opening_height"] = SETTINGS["opening_height"]
        rig["stair_y_start"] = y_start
        rig["stair_total_run"] = total_run
        rig["stair_total_rise"] = total_rise
        rig["tunnel_back_y"] = back_y
        production["construction_graph"] = json.dumps(graph)
        production["instance_safe"] = True
        preview["production_instance_member"] = False

        array = stairs.modifiers.get("PORTAL_STAIR_ARRAY")
        boolean = frame.modifiers.get("PORTAL_OPENING_BOOLEAN")
        report = {
            "status": "PASS",
            "generator_id": GENERATOR_ID,
            "schema_version": GENERATOR_SCHEMA,
            "production_collection": production.name,
            "preview_collection": preview.name,
            "instance_collection": instances_collection.name,
            "frame": {
                "host": frame.name,
                "cutter": cutter.name,
                "modifier": boolean.name if boolean else None,
                "native_system": boolean.type if boolean else None,
            },
            "stairs": {
                "source": stairs.name,
                "modifier": array.name if array else None,
                "native_system": array.type if array else None,
                "count": array.count if array else None,
                "constant_offset": list(array.constant_offset_displace) if array else None,
                "object_offset": taper.name if taper else None,
                "manual_step_objects": 0,
            },
            "tunnel_parts": [item.name for item in tunnel_parts],
            "preview_light": preview_light.name if preview_light else None,
            "distant_instances": [item.name for item in distant_instances],
        }
        print("PORTAL_BUILD " + json.dumps(report, ensure_ascii=False))
        return report
    finally:
        _restore_context(context)


if __name__ == "__main__":
    build_portal()
