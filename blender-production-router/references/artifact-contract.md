# Public Artifact Contract

All non-trivial tasks use schema version `1.0`.

## `blender_capabilities.json`

Required keys:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601",
  "blender": {
    "version": "5.2.0 LTS",
    "version_tuple": [5, 2, 0],
    "executable": "absolute path"
  },
  "capabilities": {
    "modifier_types": [],
    "constraint_types": [],
    "rna_types": [],
    "operators": {},
    "geometry_nodes": [],
    "shader_nodes": [],
    "render_engines": [],
    "enabled_addons": []
  }
}
```

## `task_route.json`

Required keys:

```json
{
  "schema_version": "1.0",
  "request": "",
  "deliverable": "asset|animated_asset|environment|shot",
  "classes": [],
  "physical_causes": [],
  "candidates": [],
  "selected_method": "",
  "selected_skill": "",
  "secondary_methods": [],
  "forbidden_substitutions": [],
  "prerequisites": [],
  "validation": [],
  "required_specialists": [],
  "design_owner": "blender-scene-design|not_applicable",
  "native_component_decision": {},
  "local_asset_library": {
    "status": "not_requested|available|unavailable",
    "requested": false,
    "request_origin": "not_requested|user_explicit|router_node_candidate",
    "root": null,
    "eligible_catalogs": []
  },
  "official_doc_resolution": {
    "status": "pending_capability_probe|cached|live_built|unavailable",
    "version": null,
    "query": null,
    "declared_sources": [],
    "resolved_sources": [],
    "results": []
  },
  "code_role": "orchestration|direct_topology_exception|none",
  "application_policy": "keep_non_destructive|apply_for_downstream_topology|realize_for_export|bake_simulation|not_applicable",
  "fallback_reason": null
}
```

Require two to four candidates. Each candidate contains `method`, `skill`, `score`, `reasons`,
`risks`, and `available`; documented alternatives may remain unresolved until their prerequisites
are compared.

`native_component_decision.system_choice` records direct and node candidates, the selected system,
concrete selection and rejected-alternative reasons, node justification, and the native Boolean
policy. `local_asset_library` is discovery metadata, not a route override. It may be enabled by an
explicit local-library request or by a Router-selected node-centric candidate route; direct Boolean,
simple Array, and simple curve routes do not enable it just because a library exists.
New Router output always includes `request_origin`; validators accept its absence in existing
schema-1.0 task artifacts so prior projects remain readable.

## `production_analysis.json`

This artifact is mandatory before Blender mutation. It supports a provisional Blockout state and a
separate formal-production state:

```json
{
  "schema_version": "1.0",
  "status": "open|provisional|complete|passed|failed",
  "execution_allowed": false,
  "execution_scope": "none|reversible_blockout|formal_production",
  "deliverable": "asset|animated_asset|environment|shot",
  "completion_scope": "hero_only|camera_visible|reusable_asset|navigable_environment",
  "protected_scope": {"status": "open|passed", "objects": [], "task_owned_collection": null},
  "real_scale": {"status": "unresolved", "units": "METRIC", "anchors": []},
  "minimum_viable_analysis": {
    "status": "open|passed|failed",
    "attempts": 0,
    "max_automatic_reviews": 2,
    "required_decisions": {
      "deliverable_scope": false,
      "protected_scope": false,
      "major_parts_or_regions": false,
      "scale_strategy": false,
      "provisional_route": false
    },
    "evidence": []
  },
  "design_intent": {},
  "focal_hierarchy": [],
  "depth_layers": [],
  "visual_flow": {},
  "camera_mobility": {},
  "representation_budget": {},
  "performance_budget": {},
  "failure_repair_policy": {},
  "camera_and_perspective": {},
  "primary_silhouette_and_proportion": {},
  "spatial_and_support_structure": {},
  "object_partition_basis": [],
  "geometry_vs_shading": [],
  "form_hierarchy": {
    "primary_masses": [],
    "structural_forms": [],
    "transition_forms": [],
    "functional_parts": [],
    "surface_details": []
  },
  "part_graph_status": "open|provisional|approved",
  "lighting_analysis": {},
  "material_analysis": {},
  "systems_analysis": {},
  "critical_blockers": [],
  "blocking_unknowns": [],
  "assumptions": []
}
```

Set `execution_allowed=true` with `execution_scope=reversible_blockout` after the minimum viable
analysis passes and `critical_blockers` is empty. In this state only task-owned, reversible proxy
geometry and semantic control objects are allowed. Ordinary uncertainty belongs in `assumptions`.

Set `execution_scope=formal_production` only after full analysis and the Part Graph pass. Before
formal execution, each nested analysis section must be `resolved`, `passed`, or explicitly
`not_applicable`; `primary_masses`, `structural_forms`, and `transition_forms` each require at least
one decision record. Use a reasoned `not_applicable` record for a genuinely simple form instead of
silently skipping the level. Never increment minimum-analysis attempts beyond two.

## `reference_derivatives.json`

Create this for every non-trivial task. Tasks without reference images use
`skipped_no_reference`. For reference tasks, resolve both entries before Blockout begins:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601",
  "source_references": [],
  "generation_capability": "unknown|available|unavailable",
  "attempt_limit": 1,
  "blocking": false,
  "authority": "auxiliary_hypothesis_only",
  "depth_map": {
    "status": "pending|generated|skipped_capability_unavailable|failed_non_blocking|skipped_no_reference",
    "attempts": 0,
    "path": null,
    "method": null
  },
  "white_model_guide": {
    "status": "pending|generated|skipped_capability_unavailable|failed_non_blocking|skipped_no_reference",
    "attempts": 0,
    "path": null,
    "method": null
  }
}
```

Attempt each derivative at most once. `generated` requires an existing uniquely named file and
method. Missing image-generation capability and generation failure are terminal non-blocking
states. Generated derivatives never become reference observations, topology truth, or final
validation evidence.

## `construction_graph.json`

Required keys:

```json
{
  "schema_version": "1.0",
  "part_graph_status": "analysis_required|provisional|approved|failed",
  "parts": [
    {
      "id": "semantic id",
      "role": "primary_form|structural_part|functional_detail|decorative_detail|presentation|lighting_region|camera_effect|cutter|helper",
      "construction": "method id",
      "form_level": "primary|structural|transition|functional|detail|helper",
      "physical_function": "",
      "separation_policy": "continuous_shell|separate_manufactured_part|moving_part|transparent_part|instance_source|temporary_construction|non_geometric",
      "separation_reason": "",
      "construction_method": "BOX_MODELING|POLYGON_MODELING|PROFILE_EXTRUSION|INSET_EXTRUSION|EDGE_LOOP_SECTIONS|BRIDGE_EDGE_LOOPS|BOOLEAN_AND_CLEANUP|SCREW_OR_SPIN|CURVE_SWEEP|SUBDIVISION_SURFACE|SCULPT_AND_RETOPOLOGY|MODULAR_ASSEMBLY|GEOMETRY_NODES_GENERATION",
      "connection_method": "",
      "combination_level": "A_VISUAL_GROUPING|B_OBJECT_JOIN|C_PHYSICAL_ASSEMBLY|D_TOPOLOGY_FUSION|NOT_APPLICABLE",
      "bevel_policy": {"classes": [], "method": "", "widths": {}},
      "modifier_stack_intent": [],
      "native_system": "ARRAY|BOOLEAN|CURVE|MESH_DATA|SHADER_NODES|...",
      "source_objects": [],
      "semantic_inputs": {},
      "generated_dependents": [],
      "code_role": "orchestration|direct_topology_exception|none",
      "application_policy": "keep_non_destructive|apply_for_downstream_topology|realize_for_export|bake_simulation|not_applicable",
      "native_component_evidence": {},
      "asset_provenance": {},
      "final_object_name": "",
      "blockout_proxy": true,
      "topology_status": "planned|in_progress|passed|deferred|not_applicable",
      "blockout_object_names": [],
      "assembly_interfaces": [],
      "topology_evidence": {
        "construction_operations": [],
        "connected_component_count": null,
        "evaluated_bevel_geometry": null,
        "boolean_cleanup_passed": null,
        "primitive_retained_reason": null,
        "wireframe": null
      }
    }
  ],
  "relationships": [
    {
      "a": "part id",
      "b": "part id",
      "type": "continuous_surface|boolean_fused|mechanical_seam|embedded_component|constraint_connection|physical_contact|instanced_element|intentionally_independent",
      "validation": []
    }
  ],
  "unclassified_visible_intersections_allowed": false,
  "modeling_contract": {
    "analysis_before_mutation": true,
    "minimum_viable_analysis_allows_reversible_blockout": true,
    "part_analysis_required_before_formal_topology": true,
    "primitive_blockout_is_final": false,
    "continuous_shell_requires_single_component": true,
    "difficulty_is_valid_separation_reason": false,
    "functional_or_detail_before_transition_allowed": false,
    "material_or_lighting_may_conceal_geometry_failure": false,
    "wireframe_acceptance_required": true,
    "real_bevel_geometry_required": true,
    "python_is_orchestration_layer": true,
    "native_component_ownership_required": true,
    "manual_count_driven_fragments_allowed": false
  }
}
```

Parts may add a backward-compatible optional `requirements` object:

```json
{
  "single_component": true,
  "closed_volume": true,
  "min_smooth_ratio": 0.8,
  "material_class": "liquid",
  "min_bbox_volume_ratio": 0.02
}
```

Material-sensitive parts may also add:

```json
{
  "requirements": {
    "material_class": "metal|wood|liquid|stone|concrete|plastic|glass|fabric",
    "material_variant": "bare|coated|brushed|aged|wet|rotten|contained",
    "physical_texture_scale_m": 0.25,
    "requires_uv": true,
    "requires_end_grain": false,
    "requires_directional_tangent": false,
    "require_volume_absorption": false
  },
  "material_evidence": [
    "unique-diffuse-review.png",
    "unique-grazing-reflection-review.png"
  ]
}
```

These fields describe the required response. They do not authorize fabricating geometry solely to
satisfy a material check.

Simulation parts may add:

```json
{
  "simulation": {
    "system": "cloth|soft_body|rigid_body|fluid|dynamic_paint|ocean|wave|particle|collision",
    "role": "subject|collider|domain|flow|effector",
    "cache_required": true,
    "low_resolution_test": {
      "status": "open|passed|failed",
      "frame_range": [1, 80],
      "max_penetration": 0.0,
      "penetration_threshold": 0.002,
      "evidence": []
    }
  }
}
```

Procedural parts may add:

```json
{
  "procedural": {
    "status": "open|passed|failed",
    "source_objects": [],
    "instance_count": 0,
    "realized_count": 0,
    "realize_reason": "",
    "animated_random": false,
    "stable_ids": true,
    "viewport_vertex_budget": 1000000
  }
}
```

At Systems stage, a Blender simulation, Array, or Geometry Nodes modifier without its matching
declaration is a failure. Realize Instances requires a downstream reason.

Relationships may add `require_overlap`, `min_gap`, `max_gap`, and task-specific evidence thresholds.

Non-geometric observations must not be represented by fabricated visible meshes. They may use:

```json
{
  "id": "top_letterbox",
  "role": "presentation",
  "requirements": {"validation_mode": "visual_only"},
  "evidence": ["absolute/or/task-relative/existing-review.png"]
}
```

`visual_only` is limited to `presentation`, `lighting_region`, `camera_effect`, and `helper`.
Evidence paths must exist. Buildable visible objects, containers, surfaces, contacts, and
architectural negative space may not use this mode. Negative space that implies an opening or
deeper volume belongs in `spatial_hypothesis.json` and must reference its boundaries and connected
region.

## `part_review_scores.json`

Keep review state per semantic part and production stage:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601",
  "max_automatic_reviews_per_part_stage": 2,
  "thresholds": {
    "pass": 80,
    "pass_with_local_repairs": 60,
    "rebuild_part": 40
  },
  "stage_criteria": {},
  "parts": [
    {
      "part_id": "main_shell",
      "critical": true,
      "stages": {
        "analysis_readiness": {
          "attempts": 0,
          "current_score": null,
          "disposition": "not_scored|pass|repair_local|rebuild_part|needs_user_review|deferred",
          "gate_clear": false,
          "consecutive_below_60": 0,
          "history": []
        }
      }
    }
  ],
  "project_policy": {
    "noncritical_failure_scope": "part_only",
    "critical_failure_scope": "current_visual_gate_only",
    "project_delete_from_part_failure": false
  }
}
```

Every scored history item contains a unique `attempt_id`, component scores, total, evidence, and
timestamp. Component maxima for a stage sum to `100`. A score from `60-79` clears the local gate
with repairs; `40-59` requires another local review; below `40` rebuilds the part. Two consecutive
scores below `60` set `needs_user_review`; no third automatic attempt is legal. Non-critical paused
parts do not block independent parts. Only a critical primary part may close the current visual
gate. Part review never changes `project_disposition` to a deletion state.

## `stage_state.json`

Required keys:

```json
{
  "schema_version": "1.0",
  "current_stage": "preflight|route|blockout|primary_surface|systems|secondary|validation|final",
  "modeling_stage": "analysis|blockout|topology_construction|structural_forms|transition_forms|functional_parts|surface_details|systems|surfacing|lighting|final",
  "iteration": 0,
  "visual_gate": "none|blockout|primary_surface|systems|final",
  "gate_status": "open|passed|failed|waiting_for_user",
  "protected_objects": [],
  "checkpoints": [],
  "analysis_gate_status": "open|provisional|passed|failed",
  "topology_gate_status": "open|passed|failed",
  "form_gates": {
    "primary_masses": "open|passed|failed",
    "structural_forms": "open|passed|failed",
    "transition_forms": "open|passed|failed",
    "functional_parts": "open|passed|failed",
    "surface_details": "open|passed|failed"
  },
  "review_evidence": {
    "front_clay": null,
    "side_clay": null,
    "top_clay": null,
    "hero_clay": null,
    "wireframe": null
  },
  "topology_rollback_strikes": [],
  "rollback": {
    "required": false,
    "target": null,
    "reasons": []
  },
  "part_progress": {
    "active": [],
    "continuable": [],
    "paused": [],
    "needs_user_review": []
  },
  "mutations_blocked": false,
  "allowed_operations": [],
  "project_disposition": {
    "status": "active|rebuild_required|awaiting_deletion_decision|deletion_rejected|deletion_approved",
    "explicit_user_confirmation_required": true,
    "deletion_candidate_paths": [],
    "task_owned_paths": [],
    "confirmation": null
  },
  "authority": {
    "state_owner": "blender-production-router",
    "design_owner": "blender-scene-design",
    "reference_owner": "blender-reference-reconstruction",
    "validator_can_reroute": false,
    "specialist_can_restart_analysis": false
  },
  "review_budgets": {
    "minimum_analysis_reviews": 2,
    "technical_repairs_per_stage": 3,
    "part_reviews_per_part_stage": 2,
    "consecutive_white_model_under_40_stop": 2,
    "route_candidate_replacements": 1,
    "unchanged_geometry_render_counts_as_attempt": false
  },
  "route_conflict": {"replacement_count": 0, "replacement_limit": 1},
  "local_repair_requests": []
}
```

## `lighting_plan.json`

```json
{
  "schema_version": "1.0",
  "analysis_status": "open|passed|failed",
  "reference_evidence": {},
  "first_pass": {
    "status": "open|passed|failed",
    "allowed_sources": ["SUN", "WORLD"],
    "gray_model_required": true,
    "topology_gate_required": true,
    "evidence": []
  },
  "lights": [
    {
      "id": "Light_Sun_Key",
      "source": "sun",
      "role": "primary direction and shadow",
      "evidence": [],
      "loss_if_removed": ""
    }
  ],
  "unresolved_blockers": []
}
```

## `validation_report.json`

Required keys:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601",
  "overall_status": "PASS|WARN|FAIL",
  "checks": [],
  "thresholds": {},
  "intentional_exceptions": [],
  "not_evaluated": [],
  "repair_suggestions": []
}
```

Unknown fields are allowed. Missing required keys, an unsupported schema version, or `FAIL/not_evaluated` on a required gate blocks completion.

## Optional Reference-Locked Extension

Image-defined tasks retain schema version `1.0` and add the following sibling artifacts from
`blender-reference-reconstruction` without changing any existing required file:

- `reference_observation.json`
- `spatial_hypothesis.json`
- `camera_match.json`
- `material_hypotheses.json`
- `visual_targets.json`
- `reference_gate.json`
- `reference_derivatives.json`

The extension is required only when `task_route.json.classes` contains
`reference_locked_reconstruction`. Existing non-reference tasks remain valid without it.

### `spatial_hypothesis.json`

Required top-level keys:

```json
{
  "schema_version": "1.0",
  "deliverable_scope": "asset|animated_asset|environment|shot",
  "scene_kind": "interior|exterior|transitional|object_stage|mixed",
  "coordinate_frame": {},
  "camera_context": {},
  "axes": [],
  "regions": [],
  "connections": [],
  "occlusion_order": [],
  "scale_anchors": [],
  "alternative_hypotheses": [],
  "spatial_invariants": [],
  "blockout_views": []
}
```

For an environment, Gate R1 requires connected non-deferred regions and passed camera, top, front,
and side blockout views. These orthographic views validate spatial coherence, not unseen visual
similarity.

Directional structures may add:

```json
{
  "directional_structures": [
    {
      "id": "rail_a",
      "type": "railing|handrail|stair_flight|stair_system|ramp|escalator|path_structure",
      "start_anchor": "named anchor or coordinates",
      "end_anchor": "named anchor or coordinates",
      "direction_vector": [0, 1, 0],
      "up_axis": "Z",
      "control_path": [[0, 0, 0], [0, 2, 0]],
      "construction_route": "curve_profile_plus_arc_length_posts",
      "anchor_object_names": {"start": "ANCHOR_START", "end": "ANCHOR_END"},
      "control_object_names": ["CTRL_PATH"],
      "generated_object_names": ["RAIL", "RAIL_POSTS"],
      "validation": ["camera", "top", "side"]
    }
  ]
}
```

Stairs additionally require `step_count`, `rise`, `run`, `ascending_from`, `ascending_to`, and
`landing_anchors`. Railings additionally require `supported_edge_id`, `profile`, and
`post_spacing`. At R1 and later, anchor, control, and generated object mappings must identify real
Blender scene objects.

### `reference_gate.json` R1 State

Reference-locked tasks include:

```json
{
  "state_authority": "stage_state.json",
  "stage_mapping": {
    "R0": "analysis",
    "R1": "blockout",
    "R2": "primary_surface",
    "R3": "surfacing_lighting",
    "R4": "final"
  },
  "blockout_scoring": {
    "schema_version": "1.0",
    "scale": 100,
    "emergency_rebuild_threshold": 40,
    "stop_after_consecutive_under_threshold": 2,
    "current_score": null,
    "consecutive_under_40": 0,
    "disposition": "not_scored|continue|rebuild_required|awaiting_deletion_decision",
    "component_maxima": {
      "primary_form_proportion": 30,
      "spatial_layout_connectivity": 25,
      "directional_structures": 25,
      "structural_contact_support_clearance": 20
    },
    "history": []
  },
  "router_decision": {
    "required": false,
    "owner": "blender-production-router",
    "action": null,
    "attempt_id": null,
    "applied": false
  },
  "project_disposition": {
    "status": "active|rebuild_required|awaiting_deletion_decision|deletion_rejected|deletion_approved",
    "explicit_user_confirmation_required": true,
    "deletion_candidate_paths": [],
    "task_owned_paths": [],
    "confirmation": null
  }
}
```

The score history records unique full Blockout attempts. Repeated renders of unchanged geometry do
not count as new attempts. Project deletion is never an automatic state transition.

After a score is recorded, `router_decision.required` becomes `true` and the Reference Specialist
must not record another score until the Router applies it with
`apply_blockout_score_decision.py`. The Router then synchronizes the gate's
`project_disposition` mirror with `stage_state.json` and marks the decision applied.
