# Blender System Choice Contract

## Purpose

Choose the Blender system that owns the result, not the system that is easiest to script. Direct
components and node systems are both first-class Blender tools. The decision is made per affected
part after task classification and before formal construction.

The Router owns this choice in `task_route.json`. Specialists may compare implementations and
report evidence, but may not change route, stage, retry, rollback, or deletion state.

## Decision Procedure

1. Define the output's causal requirement, source objects, semantic controls, downstream edits,
   performance target, and Blender-version constraints.
2. Consider a direct Blender component and a node/system alternative only when both are credible.
3. Choose the smallest system that retains the controls and evaluated output the task really needs.
4. Record the rejected alternative and the concrete reason. Do not invent a node candidate merely
   to satisfy paperwork.
5. Validate the evaluated result, not only the presence of a modifier or node group.

## Direct Components Win When

- a hard-surface host needs an ordinary cut, union, or intersecting construction volume;
- one source has simple fixed offsets, such as a normal straight `Array`;
- one profile follows one path without attribute-driven variation, such as a curve bevel;
- an ordinary Mirror, Bevel, Solidify, Subdivision, Shrinkwrap, or native deform modifier directly
  exposes the intended controls;
- a physics solver owns physical causality; or
- a simple shader graph expresses the physical material response.

**Boolean policy:** normal architectural and hard-surface cutting uses a native Boolean Modifier.
Geometry Nodes may create or distribute semantic cutters when it materially improves the input
logic, but it does not replace the host's evaluated Boolean ownership or Boolean cleanup review.

## Nodes Win When

Geometry Nodes or a compatible inspected node asset is the better choice when it adds a required,
measurable benefit that the direct component cannot express cleanly:

- field-driven, attribute-aware, context-dependent, or mask-dependent rules;
- nonuniform or adaptive variation across many elements;
- several coordinated source collections, exclusions, LOD rules, or stable-ID behavior;
- reusable procedural topology, complex curve-data processing, or a node simulation/Repeat Zone;
- scalable instance distribution where direct Array/linked instances become semantically brittle;
- an inspected local asset provides a named, compatible graph whose public controls match the task.

Shader nodes are already the normal owner of material and compositor logic. They are not Geometry
Nodes. A reusable shader or compositor asset still needs material/engine ownership and a physical
or stylistic validation appropriate to its category.

Do not use Geometry Nodes merely because the graph looks advanced, because it is easier to generate
from Python, or to recreate ordinary Boolean, Mirror, Bevel, Solidify, Array, or shader-noise work.

## Physics And Hybrid Systems

When a physical solver and a graph cooperate, declare exactly one `time_state_owner`:

- simulation solver for gravity, collision, inertia, pressure, flow, and material response;
- Geometry Nodes Simulation Zone for deliberately procedural state;
- curves, constraints, or drivers for art-directed deterministic motion.

Geometry Nodes may generate sources, instances, masks, or post-process a physical result. It must
not silently fake the physical cause that the selected simulation owns.

## Required Decision Record

Keep the existing `native_component_decision` artifact key for schema compatibility, but interpret
it as a Blender-system decision, not a demand that a non-node modifier must win:

```json
{
  "primary_system": "GEOMETRY_NODES",
  "system_choice": {
    "comparison_required": true,
    "direct_candidate": "CURVE_BEVEL",
    "node_candidate": "GEOMETRY_NODES",
    "selected_system": "GEOMETRY_NODES",
    "selection_reason": "Per-point radius, exclusions, and stable-ID variation are required along one path",
    "rejected_alternative": "A direct curve bevel has no per-point field controls",
    "node_justification": ["field-driven radius", "stable-ID variation"],
    "boolean_policy": "native_boolean_required_for_normal_hard_surface_cuts"
  }
}
```

For a direct component, set `node_candidate` to `null`, use an empty `node_justification`, and
state why the simpler semantic interface is sufficient. When the user explicitly requests a local
asset or the Router selects a node-centric candidate route, `local_asset_library` may list compatible catalogs and the selected part may later include
`asset_provenance`; discovery alone never changes the choice.
