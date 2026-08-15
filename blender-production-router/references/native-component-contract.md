# Blender Component And System-Choice Contract

## Authority

The Router owns route, stage, retry budgets, rollback target, pauses, and deletion questions.
Scene Design owns visual intent. Reference Reconstruction owns reference evidence and spatial
hypotheses. Specialists configure their assigned systems. Geometry Validation reports status and
evidence only. Specialists and validators must not create another state machine.

Read `system-choice-contract.md` before treating a direct component or a node graph as the
default. The legacy artifact name `native_component_decision` remains for compatibility, but it
records the selected Blender system and comparison evidence rather than imposing a non-node result.

## Construction Order

For every buildable result:

1. Identify the Blender system that should own the result, comparing a direct component and a node
   system whenever both could credibly satisfy the requested output.
2. Create the minimum source or control objects.
3. Configure a Modifier, Curve, Constraint, Driver, Armature, Shader Node graph, Physics system,
   instance system, or intentional mesh topology.
4. Let Blender evaluate the dependency graph.
5. Apply or realize only when a downstream topology, sculpt, simulation, export, or per-element edit requires it.
6. Record the component, semantic parameters, dependencies, application policy, and evidence.

## System Routing And Choice

- Volume opening or hard subtraction: native Boolean Difference. Geometry Nodes may only generate
  semantic cutters or their distribution when that logic is genuinely better; the host Boolean
  remains the evaluated construction owner.
- Regular vector repetition: Array.
- Constant profile along a path: Bezier/NURBS Curve with bevel depth or bevel object.
- Existing mesh deformed along a path: Curve Modifier.
- One-time exact placement: Snap, with restored tool settings.
- Persistent surface conformity: Shrinkwrap or Surface Deform.
- Predictable bend, twist, taper, or cage deformation: native deformation Modifier.
- Controlled mechanical relation: Armature, Constraint, or Driver.
- Gravity, collision, inertia, flexibility, flow, pressure, or breakage: the corresponding Simulation.
- Microscopic color, roughness, normal, or volume response: Shader Nodes.
- Large distribution, field processing, adaptive variation, coordinated source rules, reusable
  procedural topology, or node simulation: instances or Geometry Nodes.
- Unique topology no native component can express: BMesh, Mesh API, Boolean cleanup, sculpt, or retopology.

Geometry Nodes is one native system, not the default definition of non-destructive work and not a
last-resort system. Use it when its field or graph controls materially improve the requested result;
otherwise keep the smaller direct component. Read `system-choice-contract.md` for the comparison
criteria and the required decision evidence.

## Python Role

Python may create data, configure native components, set semantic parameters, establish collections
and controls, run validation, preserve context, and write artifacts. It must not loop over a count
to create final independent fragments when Array, instances, a curve, Geometry Nodes, or a
simulation expresses the dependency.

Direct BMesh or Mesh API construction is allowed only with `code_role=direct_topology_exception`
and a `fallback_reason` explaining why no native component owns the unique form. Python familiarity,
shorter code, or operator-context avoidance is not a valid reason.

## Required Record

Every routed construction records:

```json
{
  "native_system": "ARRAY",
  "source_objects": ["STAIR_SOURCE"],
  "semantic_inputs": {
    "count": 18,
    "constant_offset": [0.0, 0.28, 0.17]
  },
  "generated_dependents": ["evaluated stair flight"],
  "code_role": "orchestration",
  "application_policy": "keep_non_destructive",
  "native_component_evidence": {
    "modifier_name": "Stair_Array",
    "modifier_type": "ARRAY",
    "evaluated_instance_count": 18
  },
  "official_sources": [
    "https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/array.html"
  ],
  "official_verification_policy": "search versioned Manual/API or use cached index plus RNA probing"
}
```

Allowed application policies are `keep_non_destructive`, `apply_for_downstream_topology`,
`realize_for_export`, `bake_simulation`, and `not_applicable`.

The route-level `native_component_decision` must also contain a `system_choice` record with direct
and node candidates, selected system, selection reason, rejected alternative, and an empty or
non-empty node justification. An empty node justification is valid only when a direct component
wins. Normal hard-surface Boolean work records
`native_boolean_required_for_normal_hard_surface_cuts`.

## Execution Modes

- `reversible_blockout`: allow semantic anchors, proxy source objects, Boolean cutters, Arrays,
  curve paths, snapped modules, and low-cost preview generators. A provisional Part Graph is enough.
- `formal_production`: require approved affected parts, formal source objects, named component
  ownership, downstream policy, and validation evidence.

No Specialist may use a formal-production prerequisite to block all reversible Blockout work.

## Failure Handling

Return a local repair request containing symptom, evidence, likely owner, affected part, and
recommended rollback target. Do not change `task_route.json`, `stage_state.json`, or retry counters.
The Router may replace one route candidate at most once. Geometry Validation may report
`PASS`, `WARN`, or `FAIL` but never reroute or roll back by itself.
