#!/usr/bin/env python3
"""Classify a Blender request and create production-routing artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"
ROOT = Path(__file__).resolve().parent.parent
CARD_FILE = ROOT / "references" / "capability-cards.yaml"
DOC_SEARCH_SCRIPT = ROOT / "scripts" / "search_official_blender_docs.py"
_DOC_RESOLUTION_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
LOCAL_ASSET_LIBRARY_DEFAULT = Path(
    r"C:\Users\Administrator\Downloads\Assets-main\Assets-main\blender\assets"
)
LOCAL_ASSET_REQUEST_TERMS = (
    "blueish",
    "asset library",
    "asset browser",
    "node asset",
    "local asset",
    "assets-main",
    "blender_local_asset_library",
    "\u8d44\u4ea7\u5e93",
    "\u8282\u70b9\u8d44\u4ea7",
    "\u672c\u5730\u8d44\u4ea7",
    "\u590d\u7528\u8282\u70b9",
)
LOCAL_ASSET_CATALOGS_BY_METHOD: dict[str, list[str]] = {
    "geometry_nodes_instances": ["Geometry Node"],
    "geometry_nodes_simulation": ["Geometry Node", "Particle System"],
    "directional_structure": ["Geometry Node/Curve"],
    "curve_profile_construction": ["Geometry Node/Curve"],
    "particles_and_boids": ["Particle System", "Geometry Node"],
    "armature_constraints": ["Rigging System"],
    "shader_nodes": ["Material", "MFs"],
    "material_surfacing": ["Material", "MFs"],
    "metal_material": ["Material", "MFs"],
    "wood_material": ["Material", "MFs"],
    "water_material": ["Material", "MFs"],
    "toon_shader_banding": ["Stylized", "Compositor"],
    "inverted_hull_outline": ["Stylized", "Geometry Node"],
    "cycles_raycast_outline": ["Stylized", "Material"],
    "fluid": ["VFX", "Particle System"],
    "fracture": ["VFX", "Geometry Node"],
}
AUTO_LOCAL_ASSET_METHODS = frozenset(
    {
        "geometry_nodes_instances",
        "geometry_nodes_simulation",
        "particles_and_boids",
        "armature_constraints",
        "shader_nodes",
        "material_surfacing",
        "metal_material",
        "wood_material",
        "water_material",
        "toon_shader_banding",
        "inverted_hull_outline",
        "cycles_raycast_outline",
        "fluid",
        "fracture",
    }
)
NODE_FIELD_SIGNALS = (
    "field",
    "attribute",
    "adaptive",
    "context-aware",
    "per-point",
    "per point",
    "mask-driven",
    "multi-source",
    "stable id",
    "exclusion",
    "lod",
    "variable profile",
    "\u5b57\u6bb5",
    "\u5c5e\u6027",
    "\u81ea\u9002\u5e94",
    "\u6309\u70b9",
    "\u906e\u7f69",
    "\u591a\u6e90",
    "\u7a33\u5b9a id",
    "\u6392\u9664\u533a\u57df",
)
NODE_INSTANCE_CONTEXT_TERMS = (
    "instance",
    "distribution",
    "scatter",
    "curve",
    "path",
    "repetition",
    "module",
    "procedural topology",
    "procedural geometry",
    "\u5b9e\u4f8b",
    "\u5206\u5e03",
    "\u6563\u5e03",
    "\u6cbf\u66f2\u7ebf",
    "\u8def\u5f84",
    "\u91cd\u590d",
    "\u6a21\u5757",
    "\u7a0b\u5e8f\u5316\u62d3\u6251",
)
NODE_STATE_SIGNALS = (
    "simulation zone",
    "stateful",
    "state over time",
    "feedback loop",
    "accumulate over time",
    "procedural growth",
    "\u6a21\u62df\u533a",
    "\u72b6\u6001\u7d2f\u79ef",
    "\u968f\u65f6\u95f4\u751f\u957f",
    "\u53cd\u9988\u5faa\u73af",
)


def _load_doc_search_module() -> Any:
    spec = importlib.util.spec_from_file_location("blender_official_docs", DOC_SEARCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load official documentation resolver: {DOC_SEARCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _capability_version(capabilities: dict[str, Any] | None) -> str | None:
    if not capabilities:
        return None
    blender = capabilities.get("blender", {})
    version_tuple = blender.get("version_tuple")
    if isinstance(version_tuple, list) and len(version_tuple) >= 2:
        try:
            return f"{int(version_tuple[0])}.{int(version_tuple[1])}"
        except (TypeError, ValueError):
            pass
    version = str(blender.get("version", ""))
    for token in version.replace("-", " ").split():
        if token.count(".") >= 1 and token[0].isdigit():
            return ".".join(token.split(".")[:2])
    return None


def _resolve_local_asset_library_root() -> Path | None:
    raw_root = os.environ.get("BLENDER_LOCAL_ASSET_LIBRARY_ROOT")
    candidates = [Path(raw_root).expanduser()] if raw_root else []
    candidates.append(LOCAL_ASSET_LIBRARY_DEFAULT)
    for candidate in candidates:
        for root in (candidate, candidate / "blender" / "assets", candidate / "assets"):
            if (root / "_asset-library-meta.json").is_file() and (
                root / "_v1" / "asset-index.json"
            ).is_file():
                return root.resolve()
    return None


def _local_asset_library_decision(request: str, selected_method: str) -> dict[str, Any]:
    explicit_request = any(term in request.lower() for term in LOCAL_ASSET_REQUEST_TERMS)
    router_candidate = selected_method in AUTO_LOCAL_ASSET_METHODS
    if not explicit_request and not router_candidate:
        return {
            "status": "not_requested",
            "requested": False,
            "request_origin": "not_requested",
            "root": None,
            "eligible_catalogs": [],
            "candidate_policy": "No local candidate discovery is needed for the selected direct system.",
        }

    origin = "user_explicit" if explicit_request else "router_node_candidate"

    root = _resolve_local_asset_library_root()
    if root is None:
        return {
            "status": "unavailable",
            "requested": True,
            "request_origin": origin,
            "root": None,
            "eligible_catalogs": [],
            "candidate_policy": "Candidate library was not found; do not install, append, or assume assets.",
        }

    try:
        index = json.loads((root / "_v1" / "asset-index.json").read_text(encoding="utf-8"))
        available_catalogs = {
            str(catalog.get("path"))
            for catalog in index.get("catalogs", [])
            if catalog.get("path")
        }
    except (OSError, json.JSONDecodeError):
        available_catalogs = set()
    preferred = LOCAL_ASSET_CATALOGS_BY_METHOD.get(
        selected_method,
        ["Geometry Node", "Material", "Particle System", "Rigging System", "Stylized", "Compositor", "VFX"],
    )
    eligible = [
        catalog
        for catalog in preferred
        if any(path == catalog or path.startswith(f"{catalog}/") for path in available_catalogs)
    ]
    return {
        "status": "available",
        "requested": True,
        "request_origin": origin,
        "root": str(root),
        "eligible_catalogs": eligible,
        "candidate_policy": (
            "read-only metadata and background source inspection only; a passing runtime probe and "
            "owning-specialist task-scene validation are required before integration; discovery cannot "
            "override the selected system without the Router's single permitted route replacement"
        ),
    }


def _node_escalation_matches(text: str) -> dict[str, list[str]]:
    field_matches = [term for term in NODE_FIELD_SIGNALS if term in text]
    context_matches = [term for term in NODE_INSTANCE_CONTEXT_TERMS if term in text]
    state_matches = [term for term in NODE_STATE_SIGNALS if term in text]
    matches: dict[str, list[str]] = {}
    if field_matches and context_matches:
        matches["geometry_nodes_instances"] = field_matches + context_matches
    if state_matches:
        matches["geometry_nodes_simulation"] = state_matches
    return matches


OFFICIAL_QUERY_TERMS = {
    "architectural_opening": "bpy.types.BooleanModifier Boolean modifier opening cutter wall",
    "boolean_construction": "bpy.types.BooleanModifier Boolean modifier mesh cleanup",
    "directional_structure": "bpy.types.ArrayModifier Array modifier stairs constant offset curve",
    "array_instances": "bpy.types.ArrayModifier Array modifier count offset",
    "curve_profile_construction": "bpy.types.Curve Bezier curve bevel profile sweep",
    "curve_deform": "bpy.types.CurveModifier Curve modifier deform path",
    "precision_snapping": "bpy.types.ToolSettings snapping vertex edge face surface",
    "displace_surface": "bpy.types.DisplaceModifier Displace modifier texture coordinates",
    "simple_deform": "bpy.types.SimpleDeformModifier Simple Deform bend twist taper",
    "lattice_deform": "bpy.types.LatticeModifier Lattice modifier deformation",
    "mesh_or_surface_deform": "bpy.types.MeshDeformModifier bpy.types.SurfaceDeformModifier deformation",
    "shrinkwrap": "bpy.types.ShrinkwrapModifier Shrinkwrap modifier surface conformity",
    "armature_constraints": "bpy.types.ArmatureModifier constraints drivers mechanical motion",
    "cloth": "bpy.types.ClothModifier Cloth simulation collision self collision pinning",
    "soft_body": "bpy.types.SoftBodyModifier Soft Body simulation goal collision",
    "rigid_body": "bpy.types.RigidBodyObject Rigid Body simulation collision friction",
    "rigid_body_constraints": "bpy.types.RigidBodyConstraint Rigid Body Constraint fracture",
    "fracture": "Cell Fracture rigid body destruction",
    "fluid": "bpy.types.FluidModifier Fluid simulation liquid smoke fire domain",
    "dynamic_paint": "bpy.types.DynamicPaintModifier Dynamic Paint surface collision",
    "ocean": "bpy.types.OceanModifier Ocean modifier waves",
    "wave": "bpy.types.WaveModifier Wave modifier Dynamic Paint",
    "particles_and_boids": "Particle system Boids flocking",
    "geometry_nodes_instances": "GeometryNodeInstanceOnPoints Geometry Nodes instances distribute points",
    "geometry_nodes_simulation": "Geometry Nodes simulation zone repeat",
    "shader_nodes": "ShaderNodeTexNoise ShaderNodeBsdfPrincipled Shader Nodes material noise",
    "metal_material": "ShaderNodeBsdfPrincipled metallic roughness anisotropic",
    "wood_material": "ShaderNodeTexCoord ShaderNodeTexNoise ShaderNodeBump wood grain",
    "water_material": "ShaderNodeVolumeAbsorption ShaderNodeBsdfPrincipled water transmission",
    "inverted_hull_outline": "Geometry Nodes extrude flip faces outline",
    "camera_line_art": "Line Art Freestyle outline occlusion",
    "cycles_raycast_outline": "Cycles Shader Raycast camera offset",
    "toon_shader_banding": "Shader to RGB toon color ramp",
}


def _resolve_official_docs(
    route: dict[str, Any],
    request: str,
    capabilities: dict[str, Any] | None,
) -> dict[str, Any]:
    version = _capability_version(capabilities)
    declared = list(route.get("native_component_decision", {}).get("official_sources", []))
    if not version:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "pending_capability_probe",
            "version": None,
            "query": None,
            "cache_path": None,
            "declared_sources": declared,
            "results": [],
            "resolved_sources": declared,
            "errors": [],
        }

    method = str(route.get("selected_method", "direct_mesh_editing"))
    query = " ".join(
        value
        for value in (
            OFFICIAL_QUERY_TERMS.get(method, method.replace("_", " ")),
            request,
        )
        if value
    )
    key = (version, query)
    if key not in _DOC_RESOLUTION_CACHE:
        try:
            docs = _load_doc_search_module()
            _DOC_RESOLUTION_CACHE[key] = docs.resolve_official_sources(
                version,
                query,
                limit=8,
                offline=os.environ.get("BLENDER_PRODUCTION_OFFLINE", "") == "1",
            )
        except Exception as exc:
            _DOC_RESOLUTION_CACHE[key] = {
                "schema_version": SCHEMA_VERSION,
                "status": "unavailable",
                "version": version,
                "query": query,
                "cache_path": None,
                "source_status": {},
                "results": [],
                "errors": [str(exc)],
            }
    resolved = dict(_DOC_RESOLUTION_CACHE[key])
    result_urls = [
        str(item.get("url"))
        for item in resolved.get("results", [])
        if isinstance(item, dict) and item.get("url")
    ]
    resolved["declared_sources"] = declared
    resolved["resolved_sources"] = list(dict.fromkeys(declared + result_urls))[:12]
    return resolved

SCENE_DESIGN_DELIVERABLES = {"asset", "animated_asset", "environment", "shot"}
SCENE_DESIGN_EXEMPT_METHODS = {
    "lighting_analysis",
    "shader_nodes",
    "material_surfacing",
    "metal_material",
    "wood_material",
    "water_material",
    "toon_shader_banding",
    "cycles_raycast_outline",
}

NATIVE_SYSTEM_BY_METHOD: dict[str, str] = {
    "architectural_opening": "BOOLEAN",
    "boolean_construction": "BOOLEAN",
    "directional_structure": "ARRAY",
    "array_instances": "ARRAY",
    "curve_profile_construction": "CURVE",
    "curve_deform": "CURVE_MODIFIER",
    "precision_snapping": "SNAP",
    "displace_surface": "DISPLACE",
    "simple_deform": "SIMPLE_DEFORM",
    "lattice_deform": "LATTICE",
    "mesh_or_surface_deform": "MESH_DEFORM_OR_SURFACE_DEFORM",
    "shrinkwrap": "SHRINKWRAP",
    "armature_constraints": "ARMATURE_CONSTRAINT_DRIVER",
    "cloth": "CLOTH",
    "soft_body": "SOFT_BODY",
    "rigid_body": "RIGID_BODY",
    "rigid_body_constraints": "RIGID_BODY_CONSTRAINT",
    "fracture": "FRACTURE_OR_RIGID_BODY",
    "fluid": "FLUID",
    "dynamic_paint": "DYNAMIC_PAINT",
    "ocean": "OCEAN",
    "wave_dynamic_paint": "WAVE_OR_DYNAMIC_PAINT",
    "particles_and_boids": "PARTICLES_OR_BOIDS",
    "geometry_nodes_instances": "GEOMETRY_NODES",
    "geometry_nodes_simulation": "GEOMETRY_NODES_SIMULATION",
    "inverted_hull_outline": "GEOMETRY_NODES",
    "camera_line_art": "LINE_ART_OR_FREESTYLE",
    "cycles_raycast_outline": "SHADER_NODES",
    "toon_shader_banding": "SHADER_NODES",
    "shader_nodes": "SHADER_NODES",
    "material_surfacing": "SHADER_NODES",
    "metal_material": "SHADER_NODES",
    "wood_material": "SHADER_NODES",
    "water_material": "SHADER_NODES",
    "voxel_remesh_sculpt": "REMESH_SCULPT",
    "subdivision_control_cage": "SUBSURF",
    "bridge_and_weld": "BMESH",
    "profile_spin_or_loft": "BMESH_OR_CURVE",
    "direct_mesh_editing": "MESH_DATA",
    "assembly_structure": "ASSEMBLY_DATA",
    "reference_reconstruction": "DEFERRED_PER_PART",
}

PRESENTATION_NATIVE_METHODS = {
    "lighting_analysis",
    "shader_nodes",
    "material_surfacing",
    "metal_material",
    "wood_material",
    "water_material",
    "inverted_hull_outline",
    "camera_line_art",
    "cycles_raycast_outline",
    "toon_shader_banding",
}

PART_REVIEW_CRITERIA: dict[str, dict[str, int]] = {
    "analysis_readiness": {
        "intent_and_role": 20,
        "scale_and_reference": 20,
        "construction_route": 25,
        "relationships": 20,
        "risk_and_downstream_use": 15,
    },
    "blockout": {
        "silhouette": 30,
        "proportion": 25,
        "position_support_clearance": 25,
        "directionality": 20,
    },
    "formal_topology": {
        "continuity": 20,
        "structural_form": 20,
        "transition_quality": 20,
        "bevel_edge_language": 15,
        "cleanup": 15,
        "editability": 10,
    },
    "structural_transition": {
        "structural_completeness": 25,
        "transition_continuity": 25,
        "connection_correctness": 20,
        "edge_language": 15,
        "multiview_evidence": 15,
    },
    "systems": {
        "causal_fit": 25,
        "setup": 20,
        "stability": 25,
        "interfaces": 15,
        "cache_and_performance": 15,
    },
    "surfacing": {
        "material_identity": 25,
        "scale_and_mapping": 20,
        "physical_response": 25,
        "causal_layering": 15,
        "geometry_compatibility": 15,
    },
    "final": {
        "multiview_or_reference": 25,
        "construction": 20,
        "technical_integrity": 20,
        "surfacing_and_lighting": 20,
        "downstream_fitness": 15,
    },
}


ROUTES: list[dict[str, Any]] = [
    {
        "id": "reference_reconstruction",
        "skill": "blender-reference-reconstruction",
        "keywords": [
            "参考图",
            "参考图片",
            "参考照片",
            "按照图片",
            "复刻",
            "还原画面",
            "视觉匹配",
            "match reference",
            "recreate from image",
            "reference-locked",
            "clone scene",
        ],
        "classes": [
            "reference_locked_reconstruction",
            "spatial_reconstruction",
            "projective_spatial_reconstruction",
        ],
        "causes": [],
        "priority": 30,
    },
    {
        "id": "simple_deform",
        "skill": "blender-deformation-rigging",
        "keywords": ["弯成环", "环形", "规则弯曲", "bend", "twist", "扭转", "taper", "锥化"],
        "classes": ["predictable_deformation"],
        "causes": [],
        "priority": 12,
    },
    {
        "id": "curve_deform",
        "skill": "blender-deformation-rigging",
        "keywords": ["沿曲线", "沿路径", "路径变形", "curve modifier", "follow path", "软管", "电缆", "管线"],
        "classes": ["predictable_deformation", "path_based_construction"],
        "causes": [],
        "priority": 11,
    },
    {
        "id": "directional_structure",
        "skill": "blender-procedural-systems",
        "keywords": [
            "楼梯",
            "踏步",
            "扶手",
            "栏杆",
            "弯曲栏杆",
            "曲线栏杆",
            "stair",
            "staircase",
            "curved railing",
            "handrail",
            "balustrade",
        ],
        "classes": [
            "path_based_construction",
            "directional_structure",
            "spatial_connection",
            "regular_repetition",
        ],
        "causes": [],
        "priority": 21,
    },
    {
        "id": "assembly_structure",
        "skill": "blender-assembly-structure",
        "keywords": [
            "装配",
            "组装",
            "铰链",
            "转轴",
            "安装结构",
            "机械接缝",
            "嵌入部件",
            "assembly",
            "hinge",
            "mounting interface",
            "mechanical seam",
        ],
        "classes": ["object_assembly", "manufactured_interfaces", "scene_hierarchy"],
        "causes": [],
        "priority": 22,
    },
    {
        "id": "lighting_analysis",
        "skill": "blender-lighting-analysis",
        "keywords": [
            "光照分析",
            "阳光方向",
            "阴影方向",
            "阴影长度",
            "布光",
            "灯光匹配",
            "lighting analysis",
            "sun direction",
            "shadow direction",
            "match lighting",
        ],
        "classes": ["lighting_analysis", "light_transport", "reference_illumination"],
        "causes": ["illumination", "shadow", "bounce"],
        "priority": 22,
    },
    {
        "id": "architectural_opening",
        "skill": "blender-direct-surface-modeling",
        "keywords": [
            "门洞",
            "窗洞",
            "门窗开口",
            "墙体开口",
            "拱门洞",
            "壁龛",
            "墙龛",
            "洞口",
            "doorway",
            "door opening",
            "window opening",
            "wall opening",
            "archway",
            "wall niche",
        ],
        "classes": [
            "static_geometry",
            "architectural_opening",
            "subtractive_volume_construction",
        ],
        "causes": [],
        "priority": 24,
    },
    {
        "id": "curve_profile_construction",
        "skill": "blender-procedural-systems",
        "keywords": [
            "贝塞尔曲线",
            "曲线放样",
            "曲线截面",
            "沿曲线生成",
            "线脚",
            "踢脚线",
            "檐口",
            "连续电缆",
            "连续管线",
            "连续软管",
            "生成电缆",
            "生成管线",
            "bezier curve",
            "curve profile",
            "sweep profile",
            "molding",
            "moulding",
            "baseboard",
            "trim along path",
            "continuous cable",
            "continuous hose",
            "generate cable",
        ],
        "classes": ["path_based_construction", "swept_profile", "static_geometry"],
        "causes": [],
        "priority": 19,
    },
    {
        "id": "precision_snapping",
        "skill": "blender-assembly-structure",
        "keywords": [
            "吸附",
            "顶点吸附",
            "边吸附",
            "面吸附",
            "网格吸附",
            "精确对齐",
            "贴到表面并对齐",
            "snapping",
            "snap to face",
            "vertex snap",
            "edge snap",
            "grid snap",
            "align to surface",
        ],
        "classes": ["precision_placement", "object_assembly", "surface_contact"],
        "causes": [],
        "priority": 18,
    },
    {
        "id": "displace_surface",
        "skill": "blender-direct-surface-modeling",
        "keywords": [
            "置换修改器",
            "几何置换",
            "表面浮雕",
            "真实几何凹凸",
            "地形起伏",
            "凹凸地形",
            "displace modifier",
            "geometric displacement",
            "surface relief",
            "terrain relief",
        ],
        "classes": ["static_geometry", "sampled_surface_relief", "surface_deformation"],
        "causes": [],
        "priority": 17,
    },
    {
        "id": "profile_spin_or_loft",
        "skill": "blender-direct-surface-modeling",
        "keywords": [
            "旋绕",
            "旋转挤出",
            "管道弯头",
            "硬质弯管",
            "桥接循环边",
            "增加切割次数",
            "spin",
            "screw profile",
            "pipe elbow",
            "loft",
        ],
        "classes": ["static_geometry", "profile_driven_form", "continuous_surface"],
        "causes": [],
        "priority": 18,
    },
    {
        "id": "lattice_deform",
        "skill": "blender-deformation-rigging",
        "keywords": ["晶格", "lattice", "整体变形", "柔和变形", "局部平滑变形"],
        "classes": ["predictable_deformation"],
        "causes": [],
        "priority": 10,
    },
    {
        "id": "mesh_or_surface_deform",
        "skill": "blender-deformation-rigging",
        "keywords": ["mesh deform", "surface deform", "网格变形", "表面变形", "笼子变形"],
        "classes": ["predictable_deformation"],
        "causes": [],
        "priority": 10,
    },
    {
        "id": "shrinkwrap",
        "skill": "blender-deformation-rigging",
        "keywords": ["贴合表面", "贴在表面", "shrinkwrap", "投射到表面", "重拓扑贴合"],
        "classes": ["surface_conformity"],
        "causes": [],
        "priority": 12,
    },
    {
        "id": "armature_constraints",
        "skill": "blender-deformation-rigging",
        "keywords": ["骨骼", "绑定", "armature", "机械约束", "驱动器", "driver", "铰链", "关节", "机械运动"],
        "classes": ["mechanical_motion", "rigging"],
        "causes": [],
        "priority": 10,
    },
    {
        "id": "cloth",
        "skill": "blender-simulation-effects",
        "keywords": ["布料", "衣服", "衣物", "披风", "旗帜", "窗帘", "盖在", "drape", "cloth"],
        "classes": ["physics_simulation", "thin_flexible_material"],
        "causes": ["gravity", "flexibility", "collision"],
        "priority": 14,
    },
    {
        "id": "soft_body",
        "skill": "blender-simulation-effects",
        "keywords": ["软体", "果冻", "软垫", "橡胶变形", "弹性体", "soft body", "挤压变形"],
        "classes": ["physics_simulation", "elastic_deformation"],
        "causes": ["elasticity", "collision", "inertia"],
        "priority": 14,
    },
    {
        "id": "rigid_body",
        "skill": "blender-simulation-effects",
        "keywords": ["坠落", "掉落", "滚动", "堆叠", "撞击", "刚体", "rigid body", "真实碰撞"],
        "classes": ["physics_simulation", "rigid_dynamics"],
        "causes": ["gravity", "inertia", "collision", "friction"],
        "priority": 13,
    },
    {
        "id": "rigid_body_constraints",
        "skill": "blender-simulation-effects",
        "keywords": ["刚体约束", "可断裂关节", "物理铰链", "breakable joint", "rigid body constraint"],
        "classes": ["physics_simulation", "mechanical_motion"],
        "causes": ["constraint", "inertia", "collision"],
        "priority": 19,
    },
    {
        "id": "fracture",
        "skill": "blender-simulation-effects",
        "keywords": ["破碎", "碎裂", "坍塌", "爆破", "断裂", "fracture", "destruction"],
        "classes": ["physics_simulation", "fracture"],
        "causes": ["breaking", "impact", "collision", "inertia"],
        "priority": 18,
    },
    {
        "id": "fluid",
        "skill": "blender-simulation-effects",
        "keywords": ["流体", "液体流动", "水流", "倒水", "液体模拟", "烟雾", "火焰", "fluid", "fluid simulation", "smoke", "fire", "飞溅"],
        "classes": ["physics_simulation", "fluid_or_volume"],
        "causes": ["flow", "pressure", "buoyancy", "collision"],
        "priority": 17,
    },
    {
        "id": "water_material",
        "skill": "blender-material-surfacing",
        "keywords": ["静态水体", "水体", "液体体积", "池水", "水面材质", "水材质", "积水", "水洼", "盛水", "湿润水膜", "contained water", "water volume", "puddle material", "water material"],
        "classes": ["surface_appearance", "static_liquid_volume", "wetness"],
        "causes": ["reflection", "refraction", "absorption", "wetness"],
        "priority": 17,
    },
    {
        "id": "dynamic_paint",
        "skill": "blender-simulation-effects",
        "keywords": ["动态绘制", "脚印", "湿润痕迹", "接触涟漪", "dynamic paint", "雨滴痕迹"],
        "classes": ["surface_interaction"],
        "causes": ["contact", "proximity"],
        "priority": 15,
    },
    {
        "id": "ocean",
        "skill": "blender-simulation-effects",
        "keywords": ["大海", "海洋", "海面", "深海波浪", "ocean"],
        "classes": ["environment_simulation", "macro_surface"],
        "causes": ["wave_spectrum", "wind"],
        "priority": 17,
    },
    {
        "id": "wave",
        "skill": "blender-simulation-effects",
        "keywords": ["水波", "涟漪", "局部波浪", "wave modifier", "波纹传播"],
        "classes": ["surface_deformation", "local_wave"],
        "causes": ["wave_propagation"],
        "priority": 13,
    },
    {
        "id": "particles_and_boids",
        "skill": "blender-simulation-effects",
        "keywords": ["鱼群", "鸟群", "虫群", "boids", "群集", "粒子发射", "生命周期", "particle"],
        "classes": ["many_instances", "collective_motion", "emission"],
        "causes": ["steering", "lifecycle", "forces"],
        "priority": 14,
    },
    {
        "id": "geometry_nodes_simulation",
        "skill": "blender-procedural-systems",
        "keywords": ["模拟区", "simulation zone", "自定义群体行为", "状态累积", "随时间生长"],
        "classes": ["procedural_simulation", "stateful_system"],
        "causes": ["state_over_time"],
        "priority": 13,
    },
    {
        "id": "geometry_nodes_instances",
        "skill": "blender-procedural-systems",
        "keywords": ["散布", "大量实例", "植被", "石头分布", "几何节点实例", "geometry nodes", "萤火虫", "雨", "雪", "火花"],
        "classes": ["many_instances", "field_distribution"],
        "causes": [],
        "priority": 13,
    },
    {
        "id": "array_instances",
        "skill": "blender-procedural-systems",
        "keywords": [
            "阵列",
            "规则重复",
            "栅栏",
            "栏杆",
            "重复排列",
            "重复窗",
            "连续窗",
            "栏杆立柱",
            "百叶",
            "等距排列",
            "array",
            "环形重复",
            "repeated windows",
            "fence posts",
            "louvers",
            "regular modules",
        ],
        "classes": ["regular_repetition"],
        "causes": [],
        "priority": 12,
    },
    {
        "id": "camera_line_art",
        "skill": "blender-procedural-systems",
        "keywords": [
            "line art",
            "freestyle",
            "遮挡线",
            "交线",
            "相交线",
            "折角线",
            "褶皱线",
            "材质边界线",
            "隐藏线",
            "技术插画线稿",
        ],
        "classes": ["npr_stylization", "camera_aware_line_extraction"],
        "causes": ["occlusion", "intersection", "crease", "material_boundary"],
        "priority": 20,
    },
    {
        "id": "cycles_raycast_outline",
        "skill": "blender-npr-cycles",
        "keywords": [
            "cycles 描边",
            "cycles 三渲二",
            "cycles 二渲三",
            "光线投射描边",
            "射线检测描边",
            "着色器射线描边",
            "shader raycast",
            "raycast outline",
            "ray cast outline",
        ],
        "classes": ["npr_stylization", "surface_appearance", "camera_plane_outline"],
        "causes": ["camera_plane_offset", "ray_visibility", "silhouette_coverage"],
        "priority": 24,
    },
    {
        "id": "inverted_hull_outline",
        "skill": "blender-npr-eevee",
        "keywords": [
            "反向外壳",
            "外壳描边",
            "几何节点描边",
            "模型描边",
            "角色描边",
            "动漫描边",
            "轮廓描边",
            "inverted hull",
            "toon outline",
            "anime outline",
        ],
        "classes": ["npr_stylization", "procedural_geometry", "silhouette_outline"],
        "causes": ["surface_expansion", "face_orientation", "culling"],
        "priority": 18,
    },
    {
        "id": "toon_shader_banding",
        "skill": "blender-npr-eevee",
        "keywords": [
            "二渲三",
            "卡通明暗",
            "色阶阴影",
            "动漫材质",
            "shader to rgb",
            "着色器转 rgb",
            "toon shader",
            "cel shading",
        ],
        "classes": ["npr_stylization", "surface_appearance"],
        "causes": ["quantized_lighting", "palette_mapping"],
        "priority": 16,
    },
    {
        "id": "bridge_and_weld",
        "skill": "blender-direct-surface-modeling",
        "keywords": ["顶点连接", "边环连接", "桥接边环", "连续曲面", "无缝连接", "bridge edge loops", "焊接顶点"],
        "classes": ["topology_connection", "continuous_surface"],
        "causes": [],
        "priority": 16,
    },
    {
        "id": "boolean_construction",
        "skill": "blender-direct-surface-modeling",
        "keywords": ["布尔", "boolean", "开孔", "硬切割", "合并体积", "boolean union", "挖孔"],
        "classes": ["static_geometry", "volume_operation"],
        "causes": [],
        "priority": 12,
    },
    {
        "id": "voxel_remesh_sculpt",
        "skill": "blender-direct-surface-modeling",
        "keywords": ["有机融合", "雕刻", "重网格", "voxel remesh", "生物", "岩石", "泥塑"],
        "classes": ["static_geometry", "organic_volume"],
        "causes": [],
        "priority": 11,
    },
    {
        "id": "subdivision_control_cage",
        "skill": "blender-direct-surface-modeling",
        "keywords": ["细分曲面", "控制笼", "圆润外壳", "产品外壳", "汽车曲面", "鼠标外壳", "subdivision", "曲面高光"],
        "classes": ["static_geometry", "smooth_surface"],
        "causes": [],
        "priority": 12,
    },
    {
        "id": "shader_nodes",
        "skill": "blender-material-surfacing",
        "keywords": ["材质杂色", "粗糙度变化", "颜色变化", "微小划痕", "shader", "着色器", "bump", "normal map"],
        "classes": ["surface_appearance"],
        "causes": [],
        "priority": 13,
    },
    {
        "id": "metal_material",
        "skill": "blender-material-surfacing",
        "keywords": ["金属材质", "金属质感", "钢材", "不锈钢", "拉丝金属", "锈蚀金属", "铁锈", "metal material", "brushed metal", "metallic surface"],
        "classes": ["surface_appearance", "material_surfacing", "conductive_surface"],
        "causes": ["microfacet_reflection", "manufacturing_direction", "oxidation"],
        "priority": 18,
    },
    {
        "id": "wood_material",
        "skill": "blender-material-surfacing",
        "keywords": ["木材材质", "木板材质", "木头质感", "木纹", "潮湿木板", "腐烂木板", "旧木板", "wood material", "wood grain", "plank material"],
        "classes": ["surface_appearance", "material_surfacing", "directional_organic_surface"],
        "causes": ["fiber_direction", "moisture", "weathering"],
        "priority": 18,
    },
    {
        "id": "material_surfacing",
        "skill": "blender-material-surfacing",
        "keywords": ["真实材质", "材质质感", "pbr材质", "材质制作", "表面质感", "玻璃材质", "塑料材质", "橡胶材质", "石材材质", "混凝土材质", "瓷砖材质", "布料材质", "泥土材质", "苔藓材质", "material surfacing", "physically based material", "glass material", "concrete material", "fabric material"],
        "classes": ["surface_appearance", "material_surfacing"],
        "causes": ["surface_microstructure", "layering"],
        "priority": 19,
    },
    {
        "id": "direct_mesh_editing",
        "skill": "blender-direct-surface-modeling",
        "keywords": ["建模", "模型", "顶点", "边线", "点线面", "挤出", "内插", "拓扑", "mesh", "extrude", "inset", "椅子", "剑", "建筑"],
        "classes": ["static_geometry"],
        "causes": [],
        "priority": 3,
    },
]


CONSTRUCTION_ARCHETYPES: list[dict[str, Any]] = [
    {
        "id": "subtractive_architectural_opening",
        "keywords": [
            "门洞",
            "窗洞",
            "门窗开口",
            "墙体开口",
            "拱门洞",
            "壁龛",
            "墙龛",
            "doorway",
            "door opening",
            "window opening",
            "wall opening",
            "archway",
            "wall niche",
        ],
        "primary_method": "architectural_opening",
        "comparison_methods": ["boolean_construction", "direct_mesh_editing"],
        "parameter_owners": [
            "host wall thickness and extent",
            "opening cutter width height sill head reveal and radius",
            "frame clearance after the opening passes",
        ],
        "prerequisites": [
            "classify monolithic host versus separate lintel and jamb construction",
            "closed host and through-thickness closed cutter",
        ],
        "forbidden_substitutions": [
            "three_piece_opening_frame_as_solid_wall",
            "flat_dark_plane_as_architectural_opening",
            "coplanar_boolean_cutter",
        ],
        "validation": [
            "host and cutter ownership",
            "evaluated reveal and wall thickness",
            "Boolean sliver normal and shading audit",
        ],
    },
    {
        "id": "regular_stair_flight",
        "keywords": ["楼梯", "踏步", "梯级", "staircase", "stairs", "treads", "risers"],
        "primary_method": "directional_structure",
        "comparison_methods": ["array_instances", "direct_mesh_editing"],
        "parameter_owners": [
            "lower and upper landing anchors",
            "flight forward width and up axes",
            "total rise run count and exact per-step offset",
        ],
        "prerequisites": [
            "accepted flight and landing graph",
            "step count resolves the endpoint without hand-patching",
        ],
        "forbidden_substitutions": [
            "manual_duplicate_regular_steps",
            "independent_step_transform_patch",
            "camera_change_as_stair_direction_repair",
        ],
        "validation": [
            "rise run count and Array constant offset",
            "landing endpoint ascent direction and support",
        ],
    },
    {
        "id": "directional_rail_system",
        "keywords": [
            "弯曲栏杆",
            "曲线栏杆",
            "连续栏杆",
            "扶手",
            "栏杆",
            "curved railing",
            "continuous railing",
            "handrail",
            "balustrade",
        ],
        "primary_method": "directional_structure",
        "comparison_methods": ["curve_profile_construction", "array_instances"],
        "parameter_owners": [
            "supported edge and ordered rail path",
            "rail profile and local frame",
            "post spacing by arc length and endpoint policy",
        ],
        "prerequisites": ["accepted support edge bend side and world up policy"],
        "forbidden_substitutions": [
            "manual_patch_of_generated_directional_structure",
            "overlapping_segments_as_continuous_sweep",
            "independent_post_placement_on_curve",
        ],
        "validation": ["supported contact path continuity post spacing twist and endpoint fit"],
    },
    {
        "id": "fixed_vector_repeated_modules",
        "keywords": [
            "重复窗",
            "连续窗",
            "栏杆立柱",
            "栅栏柱",
            "百叶",
            "等距排列",
            "repeated windows",
            "fence posts",
            "louvers",
            "regular modules",
        ],
        "primary_method": "array_instances",
        "comparison_methods": ["geometry_nodes_instances"],
        "parameter_owners": ["one formal source module", "count fit policy and offset vector"],
        "prerequisites": ["stable source origin and interface", "declared end condition"],
        "forbidden_substitutions": [
            "manual_duplicate_regular_modules",
            "independent_transform_per_repeated_module",
        ],
        "validation": ["source dependency count spacing endpoint and object budget"],
    },
    {
        "id": "continuous_path_profile",
        "keywords": [
            "贝塞尔曲线",
            "曲线放样",
            "沿曲线生成",
            "线脚",
            "踢脚线",
            "檐口",
            "连续电缆",
            "连续管线",
            "连续软管",
            "生成电缆",
            "生成管线",
            "bezier curve",
            "curve profile",
            "sweep profile",
            "molding",
            "moulding",
            "baseboard",
            "trim along path",
            "continuous cable",
            "continuous hose",
            "generate cable",
        ],
        "primary_method": "curve_profile_construction",
        "comparison_methods": ["curve_deform", "profile_spin_or_loft"],
        "parameter_owners": [
            "ordered path and local frame",
            "bevel depth or profile object",
            "path and profile resolution",
        ],
        "prerequisites": ["declared path direction profile orientation and endpoint policy"],
        "forbidden_substitutions": [
            "overlapping_segments_as_continuous_sweep",
            "manual_path_segment_placement",
        ],
        "validation": ["path continuity profile twist endpoint fit and final faceting"],
    },
    {
        "id": "one_time_precision_placement",
        "keywords": [
            "吸附",
            "顶点吸附",
            "边吸附",
            "面吸附",
            "网格吸附",
            "精确对齐",
            "snapping",
            "snap to face",
            "vertex snap",
            "edge snap",
            "grid snap",
        ],
        "primary_method": "precision_snapping",
        "comparison_methods": ["shrinkwrap"],
        "parameter_owners": [
            "source active element and pivot",
            "target element transform orientation axes and offset",
        ],
        "prerequisites": ["choose one-time placement versus persistent conformity"],
        "forbidden_substitutions": [
            "eyeballed_alignment_when_semantic_snap_exists",
            "unmeasured_snapped_contact",
        ],
        "validation": ["measured contact gap orientation and restored protected tool settings"],
    },
    {
        "id": "sampled_geometric_relief",
        "keywords": [
            "置换修改器",
            "几何置换",
            "表面浮雕",
            "真实几何凹凸",
            "地形起伏",
            "凹凸地形",
            "displace modifier",
            "geometric displacement",
            "surface relief",
            "terrain relief",
        ],
        "primary_method": "displace_surface",
        "comparison_methods": ["shader_nodes", "voxel_remesh_sculpt"],
        "parameter_owners": [
            "source topology density",
            "texture and coordinate space",
            "direction midlevel strength and vertex group",
        ],
        "prerequisites": ["classify micro response versus silhouette-affecting relief"],
        "forbidden_substitutions": [
            "displacement_without_sufficient_topology",
            "undeclared_displacement_coordinates",
            "shader_bump_as_silhouette_geometry",
        ],
        "validation": ["evaluated movement silhouette self-intersection and wall thickness"],
    },
]


METHOD_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    "architectural_opening": {"modifier_types": ["BOOLEAN"]},
    "curve_profile_construction": {"rna_types": ["Curve"]},
    "precision_snapping": {"rna_types": ["ToolSettings"]},
    "displace_surface": {"modifier_types": ["DISPLACE"]},
    "simple_deform": {"modifier_types": ["SIMPLE_DEFORM"]},
    "curve_deform": {"modifier_types": ["CURVE"]},
    "lattice_deform": {"modifier_types": ["LATTICE"]},
    "mesh_or_surface_deform": {"modifier_types": ["MESH_DEFORM", "SURFACE_DEFORM"]},
    "shrinkwrap": {"modifier_types": ["SHRINKWRAP"]},
    "armature_constraints": {"modifier_types": ["ARMATURE"]},
    "cloth": {"modifier_types": ["CLOTH"], "rna_types": ["ClothSettings"]},
    "soft_body": {"modifier_types": ["SOFT_BODY"], "rna_types": ["SoftBodySettings"]},
    "rigid_body": {"rna_types": ["RigidBodyObject"]},
    "rigid_body_constraints": {"rna_types": ["RigidBodyConstraint"]},
    "fluid": {"modifier_types": ["FLUID"], "rna_types": ["FluidDomainSettings"]},
    "water_material": {"rna_types": ["ShaderNodeBsdfPrincipled", "ShaderNodeVolumeAbsorption"]},
    "dynamic_paint": {"modifier_types": ["DYNAMIC_PAINT"], "rna_types": ["DynamicPaintSurface"]},
    "ocean": {"modifier_types": ["OCEAN"]},
    "wave": {"modifier_types": ["WAVE"]},
    "particles_and_boids": {"modifier_types": ["PARTICLE_SYSTEM"], "rna_types": ["ParticleSettings"]},
    "geometry_nodes_instances": {"modifier_types": ["NODES"]},
    "geometry_nodes_simulation": {
        "modifier_types": ["NODES"],
        "rna_types": ["GeometryNodeSimulationInput", "GeometryNodeSimulationOutput"],
    },
    "array_instances": {"modifier_types": ["ARRAY"]},
    "inverted_hull_outline": {
        "modifier_types": ["NODES"],
        "rna_types": ["GeometryNodeExtrudeMesh", "GeometryNodeFlipFaces", "GeometryNodeSetMaterial"],
    },
    "camera_line_art": {"rna_types": ["GreasePencilLineartModifier"]},
    "cycles_raycast_outline": {
        "render_engines": ["CYCLES"],
        "rna_types": ["ShaderNodeRaycast", "ShaderNodeVectorTransform", "ShaderNodeBsdfToon"],
    },
    "toon_shader_banding": {"rna_types": ["ShaderNodeShaderToRGB", "ShaderNodeValToRGB"]},
    "boolean_construction": {"modifier_types": ["BOOLEAN"]},
    "voxel_remesh_sculpt": {"modifier_types": ["REMESH"]},
    "subdivision_control_cage": {"modifier_types": ["SUBSURF"]},
    "metal_material": {"rna_types": ["ShaderNodeBsdfPrincipled", "ShaderNodeTangent"]},
    "wood_material": {"rna_types": ["ShaderNodeBsdfPrincipled", "ShaderNodeTexCoord", "ShaderNodeBump"]},
    "material_surfacing": {"rna_types": ["ShaderNodeBsdfPrincipled"]},
    "shader_nodes": {"rna_types": ["ShaderNodeBsdfPrincipled"]},
}


FORBIDDEN: dict[str, list[str]] = {
    "architectural_opening": [
        "three_piece_opening_frame_as_solid_wall",
        "flat_dark_plane_as_architectural_opening",
        "coplanar_boolean_cutter",
    ],
    "curve_profile_construction": [
        "overlapping_segments_as_continuous_sweep",
        "manual_path_segment_placement",
    ],
    "precision_snapping": [
        "eyeballed_alignment_when_semantic_snap_exists",
        "unmeasured_snapped_contact",
    ],
    "displace_surface": [
        "displacement_without_sufficient_topology",
        "undeclared_displacement_coordinates",
        "shader_bump_as_silhouette_geometry",
    ],
    "reference_reconstruction": [
        "low_confidence_hypothesis_as_fact",
        "color_match_as_material_identity",
        "uniform_noise_as_causal_aging",
        "shot_only_simplification_on_visible_hero_geometry",
        "manual_override_of_failed_reference_evidence",
        "reference_image_implies_shot_only_scope",
        "screen_space_match_as_spatial_proof",
        "camera_motion_as_layout_compensation",
        "flat_dark_plane_as_unseen_space",
        "unclassified_portal_or_hidden_space",
        "early_camera_lock_before_spatial_hypothesis",
        "manual_patch_of_generated_directional_structure",
        "camera_change_as_model_score_repair",
    ],
    "simple_deform": ["manual_per-segment_rotation", "geometry_nodes_native_modifier_imitation"],
    "curve_deform": ["manual_path_segment_placement"],
    "directional_structure": [
        "independent_stair_and_handrail_guessing",
        "manual_patch_of_generated_directional_structure",
        "camera_change_as_model_score_repair",
        "manual_duplicate_regular_steps",
        "independent_step_transform_patch",
    ],
    "assembly_structure": [
        "join_objects_as_topology_fusion",
        "difficulty_as_part_boundary",
        "penetrating_part_without_interface",
        "decorative_fastener_without_mount",
    ],
    "lighting_analysis": [
        "extra_lights_before_gray_light_pass",
        "unjustified_rim_or_fill_light",
        "lighting_as_geometry_concealment",
        "unexplained_hdri_as_source_solution",
    ],
    "profile_spin_or_loft": ["rotated_segment_overlap_as_elbow", "unwelded_loop_bridge", "flat_shaded_visible_curve"],
    "cloth": ["hand-modeled_gravity_folds"],
    "soft_body": ["arbitrary_static_vertex_deformation"],
    "rigid_body": ["manual_static_impact_pose", "welded_physical_contact"],
    "fracture": ["few_hand-modeled_chunks_as_realistic_destruction"],
    "fluid": ["static_mesh_as_dynamic_flow"],
    "water_material": ["reflective_plane_as_water_volume", "fluid_simulation_for_unchanging_static_water", "ior_only_as_water_proof"],
    "particles_and_boids": ["one_object_and_keyframes_per_actor"],
    "geometry_nodes_instances": ["hundreds_of_independent_mesh_objects"],
    "array_instances": [
        "manual_duplicate_regular_modules",
        "independent_transform_per_repeated_module",
    ],
    "inverted_hull_outline": [
        "shader_only_as_true_silhouette_outline",
        "unbounded_outline_shell_expansion",
        "noise_without_position_or_normal_field",
    ],
    "camera_line_art": ["inverted_hull_as_scene_intersection_line_extractor"],
    "cycles_raycast_outline": [
        "shader_to_rgb_in_cycles",
        "geometry_nodes_as_shader_raycast",
        "unbounded_raycast_distance",
        "scene_aware_raycast_without_intent",
    ],
    "toon_shader_banding": ["shader_to_rgb_in_cycles", "toon_shading_as_true_outline"],
    "bridge_and_weld": ["deep_overlap_as_seamless_connection"],
    "boolean_construction": ["boolean_for_physical_contact"],
    "shader_nodes": ["geometry_nodes_for_material_noise"],
    "metal_material": ["gray_color_plus_metallic_as_finished_metal", "isotropic_noise_as_brushed_metal", "rust_color_without_layer_logic"],
    "wood_material": ["shared_box_projection_for_hero_boards", "texture_as_replacement_for_board_damage", "uniform_black_gloss_as_wet_wood"],
    "material_surfacing": ["base_color_only_material", "one_noise_for_every_channel", "unscaled_texture_coordinates"],
}


VALIDATION: dict[str, list[str]] = {
    "architectural_opening": [
        "monolithic host versus separate lintel and jamb classification",
        "closed host and through-thickness cutter",
        "evaluated reveal wall thickness slivers normals and shading",
    ],
    "curve_profile_construction": [
        "path point order direction and frame",
        "profile ownership orientation and scale",
        "path and bevel resolution endpoint fit twist and continuity",
    ],
    "precision_snapping": [
        "source and target ownership",
        "snap element base orientation axes and offset",
        "measured contact gap orientation and protected tool settings",
    ],
    "displace_surface": [
        "source topology density",
        "texture coordinate direction midlevel strength and stack order",
        "evaluated movement silhouette self-intersection and wall thickness",
    ],
    "reference_reconstruction": [
        "Gate R0 artifact validation",
        "camera region and inside-outside hypothesis",
        "spatial axes regions and connectivity",
        "scale anchors and hidden support space",
        "camera and negative-space anchors",
        "camera top front and side blockout views for environments",
        "P0 silhouette overlay",
        "semantic material identity",
        "blocking uncertainty disposition",
        "unique final overlay and difference evidence",
        "model-body R1 score and low-score state",
        "directional skeleton endpoints ascent support edge and local frame",
    ],
    "simple_deform": ["full-angle test", "cross-section twist", "end alignment"],
    "curve_deform": ["path adherence", "cross-section twist", "origin and axis"],
    "directional_structure": [
        "ordered start and end anchors",
        "stair ascent and landing ownership",
        "railing supported edge and bend side",
        "path tangent up-axis frame stability",
        "contact support clearance and penetration",
        "camera top and side evidence",
        "straight-flight Array constant rise and run offset when regular",
    ],
    "assembly_structure": [
        "approved Part Graph",
        "combination level",
        "mating surfaces and clearances",
        "mesh-island intent",
        "pivot hierarchy constraints and collision",
        "unclassified overlap audit",
    ],
    "lighting_analysis": [
        "shadow direction length and softness evidence",
        "single Sun and low World gray-light pass",
        "light source role evidence and loss-if-removed",
        "dark-side luminance and exposure",
        "production-light responsibility audit",
    ],
    "profile_spin_or_loft": ["shared boundary vertices", "radial segment count", "bend segment count", "cross-section preservation", "smooth-by-angle evidence"],
    "cloth": ["penetration", "stretch", "self-collision", "cache state"],
    "soft_body": ["volume collapse", "oscillation", "collision"],
    "rigid_body": ["tunneling", "jitter", "energy growth", "stable bounds"],
    "fracture": ["piece distribution", "interior material", "rigid stability"],
    "fluid": ["domain bounds", "cache state", "collider leakage"],
    "water_material": ["closed non-zero liquid volume", "waterline and contact", "IOR transmission roughness", "volume absorption scale", "macro and micro wave ownership"],
    "particles_and_boids": ["instance count", "lifecycle", "avoidance", "motion variation"],
    "geometry_nodes_instances": ["instance count", "realized count", "stable IDs", "node layout"],
    "array_instances": ["source ownership", "count or fit policy", "offset vector", "endpoint and object budget"],
    "inverted_hull_outline": [
        "front and profile silhouettes",
        "near and far camera widths",
        "deformation stability",
        "face culling",
        "shell intersections",
    ],
    "camera_line_art": [
        "occlusion",
        "intersection and crease categories",
        "temporal stability",
        "output resolution",
    ],
    "cycles_raycast_outline": [
        "Blender 5.2 and Cycles availability",
        "four camera-plane ray offsets",
        "local-only interaction policy",
        "front profile and three-quarter silhouettes",
        "near and far camera widths",
        "thin geometry and concavity",
        "ray-query render cost",
    ],
    "toon_shader_banding": [
        "render engine",
        "light rotation",
        "palette steps",
        "noise stability",
    ],
    "bridge_and_weld": ["boundary gap", "adjacent normals", "manifold state"],
    "boolean_construction": ["internal faces", "sliver faces", "evaluated shading"],
    "subdivision_control_cage": ["multiview silhouette", "highlight continuity", "cage density"],
    "shader_nodes": ["coordinates", "scale", "color spaces", "roughness range"],
    "metal_material": ["conductor and coating separation", "roughness response", "anisotropy tangent", "causal corrosion masks", "grazing reflection review"],
    "wood_material": ["board UV and grain direction", "end grain", "real texture scale", "roughness and relief hierarchy", "board variation", "wetness pooling"],
    "material_surfacing": ["material identity", "mapping scale", "channel color spaces", "layer causes", "neutral and grazing-light reviews"],
}


def _load_cards() -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(CARD_FILE.read_text(encoding="utf-8"))
    return {card["id"]: card for card in payload.get("cards", [])}


def _capability_available(method: str, capabilities: dict[str, Any] | None) -> bool | None:
    if not capabilities:
        return None
    caps = capabilities.get("capabilities", capabilities)
    requirements = METHOD_REQUIREMENTS.get(method, {})
    for key, required in requirements.items():
        available = set(caps.get(key, []))
        if not all(value in available for value in required):
            return False
    return True


def _needs_scene_design(route_method: str, deliverable: str) -> bool:
    return deliverable in SCENE_DESIGN_DELIVERABLES and route_method not in SCENE_DESIGN_EXEMPT_METHODS


def _native_system(method: str, construction: str | None = None) -> str:
    if construction:
        lowered = construction.lower()
        if "boolean" in lowered:
            return "BOOLEAN"
        if "array" in lowered:
            return "ARRAY"
        if "curve" in lowered or "bezier" in lowered or "profile" in lowered:
            return "CURVE"
        if "snap" in lowered:
            return "SNAP"
        if "displace" in lowered:
            return "DISPLACE"
        if "collision" in lowered:
            return "COLLISION"
        if "instance" in lowered:
            return "INSTANCES"
    return NATIVE_SYSTEM_BY_METHOD.get(method, "MESH_DATA")


def _component_metadata(
    part: dict[str, Any],
    selected_method: str,
    archetypes: list[dict[str, Any]],
) -> dict[str, Any]:
    role = str(part.get("role", "helper"))
    non_geometric = role in {"helper", "presentation", "lighting_region", "camera_effect"}
    construction = str(part.get("construction", selected_method))
    native = _native_system(selected_method, construction)
    if non_geometric:
        native = "NOT_APPLICABLE"
    owners = {
        item["id"]: list(item.get("parameter_owners", []))
        for item in archetypes
    }
    if non_geometric:
        return {
            "native_system": native,
            "source_objects": [],
            "semantic_inputs": {},
            "generated_dependents": [],
            "code_role": "none",
            "application_policy": "not_applicable",
            "native_component_evidence": {"status": "not_applicable"},
        }
    direct = native in {"MESH_DATA", "BMESH", "BMESH_OR_CURVE", "REMESH_SCULPT"}
    return {
        "native_system": native,
        "source_objects": [f"{part.get('id', 'part')}_SOURCE"],
        "semantic_inputs": {
            "route_method": selected_method,
            "parameter_owners": owners,
        },
        "generated_dependents": [],
        "code_role": "direct_topology_exception" if direct else "orchestration",
        "application_policy": "keep_non_destructive",
        "native_component_evidence": {
            "status": "planned",
            "expected_system": native,
            "expected_source_count": 1,
        },
    }


def _system_choice(
    selected_method: str,
    native: str,
    archetypes: list[dict[str, Any]],
) -> dict[str, Any]:
    boolean_policy = "native_boolean_required_for_normal_hard_surface_cuts"
    if selected_method in {"architectural_opening", "boolean_construction"}:
        return {
            "comparison_required": False,
            "direct_candidate": "BOOLEAN",
            "node_candidate": None,
            "selected_system": "BOOLEAN",
            "selection_reason": (
                "A semantic host volume and evaluated native Boolean own an ordinary hard-surface cut; "
                "a node graph may generate cutters but cannot replace Boolean ownership."
            ),
            "rejected_alternative": "Geometry Nodes is not a substitute for the host Boolean and cleanup review.",
            "node_justification": [],
            "boolean_policy": boolean_policy,
        }

    node_routes = {
        "geometry_nodes_instances": (
            "ARRAY_OR_COLLECTION_INSTANCES",
            ["field-driven distribution or scalable instances"],
        ),
        "geometry_nodes_simulation": (
            "PARTICLES_OR_CURVES",
            ["stateful node simulation or coordinated procedural time state"],
        ),
        "inverted_hull_outline": (
            "LINE_ART_OR_MATERIAL_OUTLINE",
            ["evaluated deformation-following object-space outline"],
        ),
    }
    if selected_method in node_routes:
        direct_candidate, justification = node_routes[selected_method]
        return {
            "comparison_required": True,
            "direct_candidate": direct_candidate,
            "node_candidate": "GEOMETRY_NODES",
            "selected_system": native,
            "selection_reason": (
                "The selected route requires node-owned controls; confirm the listed per-part benefit "
                "before formal execution and retain an evaluated-output validation record."
            ),
            "rejected_alternative": (
                f"{direct_candidate} does not expose the selected route's required node-level controls."
            ),
            "node_justification": justification,
            "boolean_policy": boolean_policy,
        }

    comparable_direct_routes = {
        "directional_structure",
        "array_instances",
        "curve_profile_construction",
        "curve_deform",
        "particles_and_boids",
    }
    if selected_method in comparable_direct_routes:
        return {
            "comparison_required": True,
            "direct_candidate": native,
            "node_candidate": "GEOMETRY_NODES",
            "selected_system": native,
            "selection_reason": (
                "The requested dependency is currently expressed by the smaller direct Blender system; "
                "escalate only after a specific field, adaptive-variation, coordinated-source, or "
                "node-state requirement is demonstrated."
            ),
            "rejected_alternative": (
                "Geometry Nodes has no demonstrated control or evaluated-output advantage at route selection."
            ),
            "node_justification": [],
            "boolean_policy": boolean_policy,
        }

    return {
        "comparison_required": bool(archetypes),
        "direct_candidate": native,
        "node_candidate": None,
        "selected_system": native,
        "selection_reason": "The current route has one credible owner; do not add a node graph without a concrete control benefit.",
        "rejected_alternative": "No credible node alternative was identified at route selection.",
        "node_justification": [],
        "boolean_policy": boolean_policy,
    }


def _native_component_decision(
    selected_method: str,
    archetypes: list[dict[str, Any]],
    deliverable: str,
) -> dict[str, Any]:
    native = _native_system(selected_method)
    direct = native in {"MESH_DATA", "BMESH", "BMESH_OR_CURVE", "REMESH_SCULPT"}
    return {
        "status": "deferred_per_part" if selected_method == "reference_reconstruction" else "planned",
        "primary_system": native,
        "parameter_owners": {
            item["id"]: list(item.get("parameter_owners", [])) for item in archetypes
        },
        "source_policy": "one semantic source/control object per dependent system",
        "python_role": "direct_topology_exception" if direct else "orchestration",
        "application_policy": "keep_non_destructive",
        "fallback_reason": (
            "unique form requires direct topology until a native component can express the silhouette"
            if direct else None
        ),
        "scene_design_required": _needs_scene_design(selected_method, deliverable),
        "system_choice": _system_choice(selected_method, native, archetypes),
    }


def _detect_construction_archetypes(text: str) -> list[dict[str, Any]]:
    detected: list[dict[str, Any]] = []
    for archetype in CONSTRUCTION_ARCHETYPES:
        matched = [
            keyword
            for keyword in archetype["keywords"]
            if str(keyword).lower() in text
        ]
        if not matched:
            continue
        detected.append(
            {
                "id": archetype["id"],
                "matched_terms": matched,
                "primary_method": archetype["primary_method"],
                "comparison_methods": list(archetype.get("comparison_methods", [])),
                "parameter_owners": list(archetype.get("parameter_owners", [])),
                "prerequisites": list(archetype.get("prerequisites", [])),
                "forbidden_substitutions": list(
                    archetype.get("forbidden_substitutions", [])
                ),
                "validation": list(archetype.get("validation", [])),
            }
        )
    return detected


def _deliverable(text: str) -> str:
    reference_locked = any(
        word in text
        for word in ["参考图", "参考图片", "参考照片", "按照图片", "复刻", "还原画面", "match reference", "recreate from image"]
    )
    full_environment = any(
        word in text
        for word in [
            "完整环境",
            "可漫游",
            "镜头外完整",
            "镜头外也要",
            "完整空间",
            "真实空间",
            "full environment",
            "navigable",
            "walkable",
        ]
    )
    explicit_shot_only = any(
        word in text
        for word in [
            "只做主镜头",
            "只要主镜头",
            "只需要单张",
            "固定镜头成片",
            "镜头外不用",
            "单张成片",
            "shot-only",
            "fixed-shot only",
        ]
    )
    environment_terms = any(
        word in text
        for word in [
            "环境",
            "场景",
            "空间",
            "室内",
            "房间",
            "浴室",
            "车站",
            "建筑",
            "走廊",
            "森林",
            "城市",
            "environment",
            "interior",
            "architecture",
            "room",
            "station",
        ]
    )
    reference_asset_terms = any(
        word in text
        for word in [
            "独立资产",
            "单独模型",
            "产品模型",
            "角色模型",
            "道具模型",
            "reusable asset",
            "character model",
            "prop model",
            "product model",
        ]
    )
    if reference_locked and explicit_shot_only:
        return "shot"
    if full_environment or (reference_locked and environment_terms):
        return "environment"
    if reference_locked and reference_asset_terms and not explicit_shot_only:
        return "asset"
    if reference_locked:
        return "shot"
    if environment_terms:
        return "environment"
    if any(word in text for word in ["动画", "运动", "循环", "animated", "animation"]):
        return "animated_asset"
    if any(word in text for word in ["渲染", "成片", "镜头", "海报", "shot", "render"]):
        return "shot"
    return "asset"


def classify_request(request: str, capabilities: dict[str, Any] | None = None) -> dict[str, Any]:
    text = request.lower().strip()
    cards = _load_cards()
    archetypes = _detect_construction_archetypes(text)
    node_escalations = _node_escalation_matches(text)
    candidates: list[dict[str, Any]] = []
    for route in ROUTES:
        matched = [keyword for keyword in route["keywords"] if keyword.lower() in text]
        inferred_node_terms = node_escalations.get(route["id"], [])
        primary_archetypes = [
            item for item in archetypes if item["primary_method"] == route["id"]
        ]
        comparison_archetypes = [
            item
            for item in archetypes
            if route["id"] in item.get("comparison_methods", [])
        ]
        if not matched and not inferred_node_terms and not primary_archetypes and not comparison_archetypes:
            continue
        score = (
            route["priority"]
            + len(matched) * 4
            + len(inferred_node_terms) * 8
            + len(primary_archetypes) * 12
            + len(comparison_archetypes) * 3
        )
        available = _capability_available(route["id"], capabilities)
        if available is False:
            score -= 100
        card = cards.get(route["id"], {})
        reasons = list(card.get("use_when", route["classes"]))
        reasons.extend(
            f"primary native route for construction archetype: {item['id']}"
            for item in primary_archetypes
        )
        reasons.extend(
            f"comparison route for construction archetype: {item['id']}"
            for item in comparison_archetypes
        )
        if inferred_node_terms:
            reasons.append(
                "inferred node-system escalation from: " + ", ".join(inferred_node_terms)
            )
        candidates.append(
            {
                "method": route["id"],
                "skill": route["skill"],
                "score": score,
                "matched_terms": matched + [f"system-choice:{term}" for term in inferred_node_terms],
                "reasons": reasons,
                "risks": card.get("failure_signs", []),
                "available": available,
            }
        )
    if not candidates:
        candidates.append(
            {
                "method": "direct_mesh_editing",
                "skill": "blender-direct-surface-modeling",
                "score": 1,
                "matched_terms": [],
                "reasons": ["default unique static form route; inspect before execution"],
                "risks": ["request requires further decomposition"],
                "available": _capability_available("direct_mesh_editing", capabilities),
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["method"]))
    reference_candidate = next(
        (
            item
            for item in candidates
            if item["method"] == "reference_reconstruction"
            and item["available"] is not False
        ),
        None,
    )
    selected = reference_candidate or next(
        (item for item in candidates if item["available"] is not False), candidates[0]
    )
    if candidates[0] is not selected:
        candidates = [selected] + [item for item in candidates if item is not selected]
    selected_route = next(route for route in ROUTES if route["id"] == selected["method"])
    selected_card = cards.get(selected["method"], {})
    existing_methods = {item["method"] for item in candidates}
    for index, alternative in enumerate(selected_card.get("alternatives", [])):
        if len(candidates) >= 4:
            break
        slug = "".join(
            character.lower() if character.isalnum() else "_"
            for character in str(alternative)
        ).strip("_")
        alias = {
            "array_modifier": "array_instances",
            "curve_modifier": "curve_deform",
            "geometry_nodes": "geometry_nodes_instances",
            "geometry_nodes_instances": "geometry_nodes_instances",
            "shrinkwrap": "shrinkwrap",
            "direct_mesh_editing": "direct_mesh_editing",
        }.get(slug, slug)
        method = f"alternative:{slug or index + 1}"
        if method in existing_methods or alias in existing_methods:
            continue
        candidates.append(
            {
                "method": method,
                "skill": "blender-production-router",
                "score": selected["score"] - 10 - index,
                "matched_terms": [],
                "reasons": [f"documented alternative to compare: {alternative}"],
                "risks": ["requires task-specific prerequisite and downstream compatibility review"],
                "available": None,
            }
        )
        existing_methods.add(method)
    classes = sorted({value for item in candidates[:4] for route in ROUTES if route["id"] == item["method"] for value in route["classes"]})
    causes = sorted({value for item in candidates[:4] for route in ROUTES if route["id"] == item["method"] for value in route["causes"]})
    prerequisites = list(cards.get(selected["method"], {}).get("prerequisites", []))
    for archetype in archetypes:
        prerequisites.extend(archetype.get("prerequisites", []))
    if selected["available"] is None:
        prerequisites.insert(0, "probe current Blender capabilities")
    forbidden = [
        "unclassified_visible_intersections",
        "unclassified_mesh_islands",
        "primitive_stacking_after_blockout",
        "primitive_only_formal_modeling",
        "color_block_partition_as_part_graph",
        "scene_or_world_reset_without_authorization",
        "blockout_proxy_as_final_topology",
        "join_objects_as_topology_fusion",
        "smooth_shading_or_weighted_normal_as_bevel",
        "detail_before_transition_forms",
        "material_or_lighting_as_geometry_concealment",
    ]
    forbidden.extend(FORBIDDEN.get(selected["method"], []))
    for archetype in archetypes:
        forbidden.extend(archetype.get("forbidden_substitutions", []))
    validation = list(VALIDATION.get(
        selected["method"],
        list(cards.get(selected["method"], {}).get("validation", ["geometry and visual validation"])),
    ))
    validation.extend(
        [
            "approved Part Graph and construction methods",
            "front side top hero clay and wireframe evidence",
            "formal-topology conversion after Blockout",
            "topology rollback strike audit",
        ]
    )
    for archetype in archetypes:
        validation.extend(archetype.get("validation", []))
    local_asset_library = _local_asset_library_decision(request, selected["method"])
    specialist_sequence = ["blender-production-router"]
    if local_asset_library["requested"]:
        specialist_sequence.append("blender-local-asset-library")
    design_required = _needs_scene_design(selected["method"], _deliverable(text))
    if selected["method"] == "reference_reconstruction":
        specialist_sequence.extend(
            [
                "blender-reference-reconstruction",
                "blender-scene-design",
                "blender-direct-surface-modeling",
                "blender-assembly-structure",
            ]
        )
        specialist_sequence.extend(
            item["skill"]
            for item in candidates[:4]
            if item["method"] != "reference_reconstruction"
        )
        specialist_sequence.extend(
            ["blender-material-surfacing", "blender-lighting-analysis"]
        )
    else:
        if design_required:
            specialist_sequence.append("blender-scene-design")
        specialist_sequence.append(selected["skill"])
        if any(value in selected_route["classes"] for value in {"static_geometry", "object_assembly", "spatial_connection"}):
            specialist_sequence.append("blender-assembly-structure")
    if any(
        item["method"] in {"geometry_nodes_instances", "geometry_nodes_simulation"}
        for item in candidates[:4]
    ):
        specialist_sequence.append("blender-geometry-nodes-studio")
    specialist_sequence.append("blender-geometry-validation")
    construction_method_decision = {
        "shape_grammar_review_required": True,
        "detected_archetypes": [item["id"] for item in archetypes],
        "parameter_owners": {
            item["id"]: item["parameter_owners"] for item in archetypes
        },
        "native_generator_comparisons": [
            {
                "archetype": item["id"],
                "primary_method": item["primary_method"],
                "comparison_methods": item["comparison_methods"],
                "manual_assembly_requires_documented_exception": True,
            }
            for item in archetypes
        ],
        "fallback_when_no_archetype_matches": (
            "inspect the form and declare unique topology, deformation, distribution, "
            "simulation, assembly, or shading ownership before primitive creation"
        ),
        "native_component_decision": _native_component_decision(
            selected["method"], archetypes, _deliverable(text)
        ),
    }
    design_owner = "blender-scene-design" if design_required or selected["method"] == "reference_reconstruction" else "not_applicable"
    native_decision = construction_method_decision["native_component_decision"]
    native_decision["official_sources"] = list(selected_card.get("official_sources", []))
    native_decision["official_verification_policy"] = (
        "search official Blender Manual/API for unfamiliar or version-sensitive components; "
        "use cached index plus RNA probing when offline"
    )
    fallback_reason = native_decision.get("fallback_reason")
    return {
        "schema_version": SCHEMA_VERSION,
        "request": request,
        "deliverable": _deliverable(text),
        "classes": classes,
        "physical_causes": causes,
        "candidates": candidates[:4],
        "selected_method": selected["method"],
        "selected_skill": selected["skill"],
        "secondary_methods": [item["method"] for item in candidates if item["method"] != selected["method"]][:3],
        "forbidden_substitutions": sorted(set(forbidden)),
        "prerequisites": prerequisites,
        "validation": validation,
        "required_specialists": list(dict.fromkeys(specialist_sequence)),
        "construction_archetypes": archetypes,
        "construction_method_decision": construction_method_decision,
        "design_owner": design_owner,
        "native_component_decision": native_decision,
        "local_asset_library": local_asset_library,
        "official_doc_resolution": {
            "schema_version": SCHEMA_VERSION,
            "status": "pending_capability_probe",
            "version": None,
            "query": None,
            "cache_path": None,
            "declared_sources": list(native_decision.get("official_sources", [])),
            "results": [],
            "resolved_sources": list(native_decision.get("official_sources", [])),
            "errors": [],
        },
        "code_role": native_decision.get("python_role", "orchestration"),
        "application_policy": native_decision.get("application_policy", "keep_non_destructive"),
        "fallback_reason": fallback_reason,
    }


def _construction_graph(route: dict[str, Any]) -> dict[str, Any]:
    selected = route["selected_method"]
    if selected == "reference_reconstruction":
        parts = [
            {
                "id": "reference_scope",
                "role": "helper",
                "construction": "pending_spatial_hypothesis",
            },
        ]
        relationships = []
    elif selected in {
        "lighting_analysis",
        "shader_nodes",
        "material_surfacing",
        "metal_material",
        "wood_material",
        "water_material",
        "inverted_hull_outline",
        "camera_line_art",
        "cycles_raycast_outline",
        "toon_shader_banding",
    }:
        parts = [
            {
                "id": "existing_scene_receiver_scope",
                "role": "helper",
                "construction": "inspect_and_map_existing_scene_objects",
            }
        ]
        relationships = []
    elif selected == "assembly_structure":
        parts = [
            {
                "id": "assembly_part_graph_scope",
                "role": "helper",
                "construction": "inspect_manufacturing_and_motion_boundaries",
            }
        ]
        relationships = []
    elif selected == "architectural_opening":
        parts = [
            {
                "id": "opening_host",
                "role": "primary_form",
                "construction": "closed_monolithic_host_volume",
            },
            {
                "id": "opening_cutter",
                "role": "cutter",
                "construction": "semantic_through_thickness_boolean_cutter",
            },
        ]
        relationships = [
            {
                "a": "opening_host",
                "b": "opening_cutter",
                "type": "boolean_fused",
                "validation": [
                    "closed host",
                    "through-thickness cutter",
                    "evaluated reveal and wall thickness",
                ],
            }
        ]
    elif selected == "curve_profile_construction":
        parts = [
            {
                "id": "profile_path",
                "role": "helper",
                "construction": "ordered_bezier_or_nurbs_path",
            },
            {
                "id": "profile_source",
                "role": "helper",
                "construction": "bevel_depth_or_profile_object",
            },
            {
                "id": "swept_output",
                "role": "structural_part",
                "construction": "curve_profile_construction",
            },
        ]
        relationships = [
            {
                "a": "profile_path",
                "b": "swept_output",
                "type": "embedded_component",
                "validation": ["path order", "profile frame", "endpoint fit"],
            },
            {
                "a": "profile_source",
                "b": "swept_output",
                "type": "embedded_component",
                "validation": ["profile ownership", "bevel resolution", "twist"],
            },
        ]
    elif selected == "precision_snapping":
        parts = [
            {
                "id": "snap_source",
                "role": "structural_part",
                "construction": "existing_or_formal_source_part",
            },
            {
                "id": "snap_target",
                "role": "structural_part",
                "construction": "declared_vertex_edge_face_grid_or_connector_target",
            },
        ]
        relationships = [
            {
                "a": "snap_source",
                "b": "snap_target",
                "type": "physical_contact",
                "validation": ["snap settings", "measured gap", "orientation"],
            }
        ]
    elif selected == "displace_surface":
        parts = [
            {
                "id": "displace_source_surface",
                "role": "primary_form",
                "construction": "density_controlled_source_mesh",
            },
            {
                "id": "displace_coordinate_control",
                "role": "helper",
                "construction": "texture_coordinate_and_strength_control",
            },
        ]
        relationships = [
            {
                "a": "displace_source_surface",
                "b": "displace_coordinate_control",
                "type": "intentionally_independent",
                "validation": ["coordinate space", "strength", "evaluated relief"],
            }
        ]
    elif selected == "bridge_and_weld":
        parts = [
            {"id": "surface_a", "role": "primary_form", "construction": "direct_mesh_editing"},
            {"id": "surface_b", "role": "primary_form", "construction": "direct_mesh_editing"},
        ]
        relationships = [
            {
                "a": "surface_a",
                "b": "surface_b",
                "type": "continuous_surface",
                "validation": ["boundary gap", "adjacent normals", "manifold state"],
            }
        ]
    elif selected in {"cloth", "soft_body", "rigid_body", "fluid"}:
        parts = [
            {"id": "simulated_subject", "role": "primary_form", "construction": selected},
            {"id": "collider", "role": "structural_part", "construction": "collision"},
        ]
        relationships = [
            {
                "a": "simulated_subject",
                "b": "collider",
                "type": "physical_contact",
                "validation": ["participant roles", "penetration"],
            }
        ]
    elif selected in {"geometry_nodes_instances", "array_instances", "particles_and_boids"}:
        parts = [
            {"id": "source_asset", "role": "structural_part", "construction": "direct_mesh_editing"},
            {"id": "distributed_result", "role": "primary_form", "construction": selected},
        ]
        relationships = [
            {
                "a": "source_asset",
                "b": "distributed_result",
                "type": "instanced_element",
                "validation": ["source and instance counts", "realization policy"],
            }
        ]
    elif selected == "directional_structure":
        parts = [
            {
                "id": "directional_skeleton",
                "role": "helper",
                "construction": "ordered_semantic_path_or_flight_graph",
            },
            {
                "id": "directional_structure_output",
                "role": "structural_part",
                "construction": "regenerate_from_directional_skeleton",
            },
        ]
        relationships = [
            {
                "a": "directional_skeleton",
                "b": "directional_structure_output",
                "type": "instanced_element",
                "validation": ["anchor order", "ascent direction", "regeneration ownership"],
            }
        ]
    else:
        parts = [{"id": "subject", "role": "primary_form", "construction": selected}]
        relationships = []
    form_level_by_role = {
        "primary_form": "primary",
        "structural_part": "structural",
        "functional_detail": "functional",
        "decorative_detail": "detail",
        "cutter": "structural",
        "helper": "helper",
        "presentation": "helper",
        "lighting_region": "helper",
        "camera_effect": "helper",
    }
    for part in parts:
        role = str(part.get("role", "helper"))
        non_geometric = role in {"helper", "presentation", "lighting_region", "camera_effect"}
        part.setdefault("form_level", form_level_by_role.get(role, "structural"))
        part.setdefault("physical_function", "non_geometric" if non_geometric else "unresolved")
        part.setdefault("separation_policy", "non_geometric" if non_geometric else "unresolved")
        part.setdefault("separation_reason", "non_geometric" if non_geometric else "unresolved")
        part.setdefault("construction_method", part.get("construction", "unresolved"))
        part.setdefault("connection_method", "not_applicable" if non_geometric else "unresolved")
        part.setdefault("combination_level", "NOT_APPLICABLE" if non_geometric else "unresolved")
        part.setdefault(
            "bevel_policy",
            {
                "classes": [],
                "method": "not_applicable" if non_geometric else "unresolved",
                "widths": {},
            },
        )
        part.setdefault("modifier_stack_intent", [])
        part.setdefault("asset_provenance", {})
        part.setdefault("final_object_name", part.get("object", "unresolved"))
        part.setdefault("blockout_proxy", False if non_geometric else True)
        part.setdefault("topology_status", "not_applicable" if non_geometric else "planned")
        part.setdefault("blockout_object_names", [])
        part.setdefault("assembly_interfaces", [])
        part.setdefault(
            "topology_evidence",
            {
                "construction_operations": [],
                "connected_component_count": None,
                "evaluated_bevel_geometry": None,
                "boolean_cleanup_passed": None,
                "primitive_retained_reason": None,
                "wireframe": None,
            },
        )
        component = _component_metadata(
            part,
            route.get("selected_method", "direct_mesh_editing"),
            route.get("construction_archetypes", []),
        )
        component["native_component_evidence"]["official_sources"] = list(
            route.get("native_component_decision", {}).get("official_sources", [])
        )
        for key, value in component.items():
            part.setdefault(key, value)
    graph = {
        "schema_version": SCHEMA_VERSION,
        "part_graph_status": "analysis_required",
        "parts": parts,
        "relationships": relationships,
        "unclassified_visible_intersections_allowed": False,
        "modeling_contract": {
            "analysis_before_mutation": True,
            "minimum_viable_analysis_allows_reversible_blockout": True,
            "part_analysis_required_before_formal_topology": True,
            "primitive_blockout_is_final": False,
            "continuous_shell_requires_single_component": True,
            "difficulty_is_valid_separation_reason": False,
            "functional_or_detail_before_transition_allowed": False,
            "material_or_lighting_may_conceal_geometry_failure": False,
            "wireframe_acceptance_required": True,
            "real_bevel_geometry_required": True,
            "shape_grammar_before_primitive_creation": True,
            "native_generator_comparison_required": True,
            "manual_assembly_requires_documented_exception": True,
            "python_is_orchestration_layer": True,
            "native_component_ownership_required": True,
            "manual_count_driven_fragments_allowed": False,
        },
        "construction_archetypes": route.get("construction_archetypes", []),
        "construction_method_decision": route.get(
            "construction_method_decision", {}
        ),
        "design_owner": route.get("design_owner", "not_applicable"),
        "native_component_decision": route.get("native_component_decision", {}),
        "local_asset_library": route.get("local_asset_library", {}),
        "code_role": route.get("code_role", "orchestration"),
        "application_policy": route.get("application_policy", "keep_non_destructive"),
        "fallback_reason": route.get("fallback_reason"),
    }
    if selected == "reference_reconstruction":
        graph["reference_audit_required"] = True
        graph["spatial_hypothesis_required"] = True
        graph["expansion_policy"] = (
            "Replace the placeholder after R0 with buildable observations and real receivers; "
            "keep regions, lighting, atmosphere, post, and negative space out of fake geometry"
        )
    if selected == "directional_structure":
        graph["directional_skeleton_required"] = True
        graph["generation_policy"] = (
            "Solve endpoints, ascent or travel direction, supported edge, landings, up axis, "
            "control path, and clearances before creating generated geometry. Repair the skeleton "
            "and regenerate instead of moving generated members."
        )
    return graph


def _stage_state(protected_objects: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "current_stage": "preflight",
        "modeling_stage": "analysis",
        "iteration": 0,
        "visual_gate": "none",
        "gate_status": "open",
        "analysis_gate_status": "open",
        "topology_gate_status": "open",
        "form_gates": {
            "primary_masses": "open",
            "structural_forms": "open",
            "transition_forms": "open",
            "functional_parts": "open",
            "surface_details": "open",
        },
        "review_evidence": {
            "front_clay": None,
            "side_clay": None,
            "top_clay": None,
            "hero_clay": None,
            "wireframe": None,
        },
        "topology_rollback_strikes": [],
        "rollback": {"required": False, "target": None, "reasons": []},
        "part_progress": {
            "active": [],
            "continuable": [],
            "paused": [],
            "needs_user_review": [],
        },
        "protected_objects": protected_objects,
        "checkpoints": [],
        "mutations_blocked": True,
        "allowed_operations": [
            "inspect existing scene",
            "analyze references and requirements",
            "resolve non-blocking reference derivative attempts",
            "complete production_analysis.json",
            "complete and approve the Part Graph",
        ],
        "project_disposition": {
            "status": "active",
            "explicit_user_confirmation_required": True,
            "deletion_candidate_paths": [],
            "task_owned_paths": [],
            "confirmation": None,
        },
        "authority": {
            "state_owner": "blender-production-router",
            "design_owner": "blender-scene-design",
            "reference_owner": "blender-reference-reconstruction",
            "validator_can_reroute": False,
            "specialist_can_restart_analysis": False,
        },
        "review_budgets": {
            "minimum_analysis_reviews": 2,
            "technical_repairs_per_stage": 3,
            "part_reviews_per_part_stage": 2,
            "consecutive_white_model_under_40_stop": 2,
            "route_candidate_replacements": 1,
            "unchanged_geometry_render_counts_as_attempt": False,
        },
        "route_conflict": {"replacement_count": 0, "replacement_limit": 1},
        "local_repair_requests": [],
    }


def _production_analysis(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "open",
        "execution_allowed": False,
        "execution_scope": "none",
        "deliverable": route["deliverable"],
        "completion_scope": "unresolved",
        "protected_scope": {
            "status": "open",
            "objects": [],
            "task_owned_collection": None,
        },
        "real_scale": {"status": "unresolved", "units": "METRIC", "anchors": []},
        "minimum_viable_analysis": {
            "status": "open",
            "attempts": 0,
            "max_automatic_reviews": 2,
            "required_decisions": {
                "deliverable_scope": False,
                "protected_scope": False,
                "major_parts_or_regions": False,
                "scale_strategy": False,
                "provisional_route": False,
            },
            "evidence": [],
        },
        "design_intent": {
            "status": "unresolved",
            "visual_thesis": "",
            "scope": "original_or_reference_guided",
            "evidence": [],
            "unknowns": [],
        },
        "focal_hierarchy": [],
        "depth_layers": [],
        "visual_flow": {
            "leading_lines": [],
            "occlusion_order": [],
            "negative_space": [],
            "scale_rhythm": [],
            "repetition_rhythm": [],
        },
        "camera_mobility": {
            "mode": "unresolved",
            "allowed_move": None,
            "parallax_requirements": [],
        },
        "representation_budget": {
            "status": "unresolved",
            "real_geometry": [],
            "instances": [],
            "shader_or_normal": [],
            "distant_simplification": [],
        },
        "performance_budget": {
            "status": "unresolved",
            "object_limit": None,
            "instance_limit": None,
            "realization_policy": "unresolved",
            "simulation_preview": None,
            "render_target": None,
        },
        "failure_repair_policy": {},
        "reference_inputs": [],
        "camera_and_perspective": {"status": "unresolved", "evidence": [], "unknowns": []},
        "primary_silhouette_and_proportion": {"status": "unresolved", "evidence": [], "unknowns": []},
        "spatial_and_support_structure": {"status": "unresolved", "evidence": [], "unknowns": []},
        "object_partition_basis": [],
        "geometry_vs_shading": [],
        "form_hierarchy": {
            "primary_masses": [],
            "structural_forms": [],
            "transition_forms": [],
            "functional_parts": [],
            "surface_details": [],
        },
        "part_graph_status": "open",
        "lighting_analysis": {"status": "unresolved", "evidence": [], "unknowns": []},
        "material_analysis": {"status": "unresolved", "classes": [], "scale_evidence": [], "unknowns": []},
        "systems_analysis": {
            "deformation": [],
            "simulation": [],
            "procedural": [],
            "animation": [],
            "export": [],
        },
        "critical_blockers": [],
        "blocking_unknowns": [],
        "assumptions": [],
        "approvals": [],
    }


def _initial_reference_derivatives(reference_paths: list[str] | None) -> dict[str, Any]:
    resolved = [str(Path(value).expanduser().resolve()) for value in (reference_paths or [])]
    has_references = bool(resolved)
    status = "pending" if has_references else "skipped_no_reference"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_references": resolved,
        "generation_capability": "unknown" if has_references else "unavailable",
        "attempt_limit": 1,
        "blocking": False,
        "authority": "auxiliary_hypothesis_only",
        "depth_map": {
            "status": status,
            "attempts": 0,
            "path": None,
            "method": None,
        },
        "white_model_guide": {
            "status": status,
            "attempts": 0,
            "path": None,
            "method": None,
        },
    }


def _part_stage_state(disposition: str = "not_scored") -> dict[str, Any]:
    return {
        "attempts": 0,
        "current_score": None,
        "disposition": disposition,
        "gate_clear": disposition == "deferred",
        "consecutive_below_60": 0,
        "history": [],
    }


def _initial_part_review_scores(
    route: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, Any]:
    system_methods = {
        "simple_deform",
        "curve_deform",
        "directional_structure",
        "lattice_deform",
        "mesh_or_surface_deform",
        "shrinkwrap",
        "armature_constraints",
        "cloth",
        "soft_body",
        "rigid_body",
        "rigid_body_constraints",
        "fracture",
        "fluid",
        "ocean",
        "wave_dynamic_paint",
        "particles_and_boids",
        "geometry_nodes_instances",
        "geometry_nodes_simulation",
        "array_instances",
    }
    system_required = route.get("selected_method") in system_methods
    parts: list[dict[str, Any]] = []
    for part in graph.get("parts", []):
        if not isinstance(part, dict) or not part.get("id"):
            continue
        role = str(part.get("role", "helper"))
        buildable = role in {
            "primary_form",
            "structural_part",
            "functional_detail",
            "decorative_detail",
            "cutter",
        }
        critical = role == "primary_form" or (
            route.get("selected_method") == "directional_structure"
            and part.get("id") == "directional_structure_output"
        )
        stages = {
            stage: _part_stage_state("not_scored" if buildable else "deferred")
            for stage in PART_REVIEW_CRITERIA
        }
        if buildable and not system_required:
            stages["systems"] = _part_stage_state("deferred")
        parts.append(
            {
                "part_id": str(part["id"]),
                "critical": critical,
                "stages": stages,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "max_automatic_reviews_per_part_stage": 2,
        "thresholds": {
            "pass": 80,
            "pass_with_local_repairs": 60,
            "rebuild_part": 40,
        },
        "stage_criteria": PART_REVIEW_CRITERIA,
        "parts": parts,
        "project_policy": {
            "noncritical_failure_scope": "part_only",
            "critical_failure_scope": "current_visual_gate_only",
            "project_delete_from_part_failure": False,
        },
    }


def _initial_lighting_plan() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis_status": "open",
        "reference_evidence": {
            "contact_points": [],
            "shadow_endpoints": [],
            "shadow_direction": None,
            "shadow_length": None,
            "estimated_source_elevation": None,
            "penumbra": None,
            "lit_and_unlit_faces": [],
            "visible_sources": [],
            "unknowns": [],
        },
        "first_pass": {
            "status": "open",
            "allowed_sources": ["SUN", "WORLD"],
            "gray_model_required": True,
            "topology_gate_required": True,
            "evidence": [],
        },
        "lights": [],
        "color_management": {},
        "unresolved_blockers": [],
    }


def _initial_validation_report() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "overall_status": "WARN",
        "checks": [],
        "thresholds": {},
        "intentional_exceptions": [],
        "not_evaluated": [
            "mesh_legality",
            "surface_quality",
            "construction_relationships",
            "simulation_stability",
            "protected_scene_state",
            "visual_evidence",
        ],
        "repair_suggestions": ["Run blender-geometry-validation after scene execution"],
    }


def write_artifacts(
    request: str,
    output_dir: Path,
    capabilities: dict[str, Any] | None,
    protected_objects: list[str],
    reference_paths: list[str] | None = None,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    route = classify_request(request, capabilities)
    route["official_doc_resolution"] = _resolve_official_docs(route, request, capabilities)
    resolved_sources = route["official_doc_resolution"].get("resolved_sources", [])
    if resolved_sources:
        route.setdefault("native_component_decision", {})["official_sources"] = list(
            dict.fromkeys(str(value) for value in resolved_sources)
        )
        route.setdefault("construction_method_decision", {}).setdefault(
            "native_component_decision", {}
        )["official_sources"] = list(
            dict.fromkeys(str(value) for value in resolved_sources)
        )
    task_id = hashlib.sha256(request.encode("utf-8")).hexdigest()[:12]
    route["task_id"] = task_id
    route["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    construction_graph = _construction_graph(route)
    artifacts = {
        "task_route.json": route,
        "production_analysis.json": _production_analysis(route),
        "reference_derivatives.json": _initial_reference_derivatives(reference_paths),
        "construction_graph.json": construction_graph,
        "part_review_scores.json": _initial_part_review_scores(route, construction_graph),
        "stage_state.json": _stage_state(protected_objects),
        "lighting_plan.json": _initial_lighting_plan(),
        "validation_report.json": _initial_validation_report(),
    }
    artifacts["production_analysis.json"]["protected_scope"]["objects"] = list(protected_objects)
    if capabilities:
        artifacts["blender_capabilities.json"] = capabilities
    if route["selected_method"] == "reference_reconstruction" and reference_paths:
        resolved_references = [
            str(Path(value).expanduser().resolve()) for value in reference_paths
        ]
        artifacts["production_analysis.json"]["reference_inputs"] = resolved_references
        script = ROOT.parent / "blender-reference-reconstruction" / "scripts" / "init_reference_artifacts.py"
        spec = importlib.util.spec_from_file_location("blender_reference_artifacts", script)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load reference artifact initializer: {script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reference_artifacts = module.build(
            [Path(value) for value in resolved_references],
            deliverable=route["deliverable"],
        )
        artifacts.update(reference_artifacts)
    paths: dict[str, str] = {}
    for name, payload in artifacts.items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        paths[name] = str(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--capabilities")
    parser.add_argument("--protected-object", action="append", default=[])
    parser.add_argument("--reference", action="append", default=[])
    args = parser.parse_args()
    capabilities = None
    if args.capabilities:
        capabilities = json.loads(Path(args.capabilities).read_text(encoding="utf-8"))
    paths = write_artifacts(
        args.request,
        Path(args.output_dir).expanduser().resolve(),
        capabilities,
        args.protected_object,
        args.reference,
    )
    print(json.dumps({"status": "ok", "artifacts": paths}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
