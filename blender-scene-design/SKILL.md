---
name: blender-scene-design
description: Define production-ready visual intent for Blender scenes and standalone assets, including focal hierarchy, depth layers, visual flow, scale and repetition rhythm, camera mobility, representation fidelity, and performance budgets. Use for original or reference-guided Blender work before construction choices are executed, especially environments, architecture, products, hero assets, or scenes whose modeling quality depends on coordinated spatial design rather than isolated objects.
---

# Blender Scene Design

Define what the scene or asset must communicate before specialists decide how to build it.

## Authority Boundary

- Own design intent only: focal hierarchy, depth, flow, rhythm, representation, and performance.
- Read reference evidence from `blender-reference-reconstruction`; do not reinterpret observations as facts.
- Write design fields in `production_analysis.json`; do not create another design artifact.
- Do not select Boolean, Array, Geometry Nodes, simulation, topology, or material implementations.
- Do not mutate Blender, advance `stage_state.json`, score a gate, restart analysis, or request deletion.
- Send a local design repair request to the Router when an implementation contradicts accepted intent.

The Router remains the only route, stage, retry-budget, rollback, and pause authority. Read
`../blender-production-router/references/production-protocol.md` before contributing to a task.

## Design Pass

Write the smallest useful decision set:

1. State a one-sentence visual thesis and the primary deliverable.
2. Rank the primary focus, secondary focus, support masses, background, and intentional negative space.
3. Divide the scene into foreground, midground, and background; for one asset, use silhouette,
   structural, transition, functional, and micro-detail layers.
4. Map leading lines, occlusion sequence, entry/exit paths, scale rhythm, repetition rhythm, and
   density changes. Describe relationships, not merely object lists.
5. Declare camera mobility: fixed, bounded move, turntable, free inspection, or animation path.
6. Allocate representation by silhouette, shadow, contact, occlusion, deformation, distance, and
   camera mobility. Use real geometry where those properties matter; use instances, shaders,
   normals, or distant simplification where they do not.
7. Set object, instance, geometry, texture, simulation, and render budgets at a task-appropriate level.
8. Map visible failure symptoms to local design repairs without changing the route or restarting analysis.

For detailed fields and examples, read [design-intent-contract.md](references/design-intent-contract.md).
Read [portal-scene-case.md](references/portal-scene-case.md) only when a layered environment,
forced perspective, repeated hero asset, water path, terrain, or vegetation distribution is relevant.

## Output Contract

Populate these existing `production_analysis.json` fields:

- `design_intent`
- `focal_hierarchy`
- `depth_layers`
- `visual_flow`
- `camera_mobility`
- `representation_budget`
- `performance_budget`
- `failure_repair_policy`

Use explicit uncertainty and assumptions. Do not invent a reference observation or camera fact.
Original scenes can define intent directly; they do not need a fabricated reference-analysis pass.

## Review Rule

Review design at minimum analysis and once after reversible Blockout. The Router's two-review
analysis budget includes both reviews. Later visible failures return to the earliest local design
field that caused them; they do not reopen the complete design pass.

