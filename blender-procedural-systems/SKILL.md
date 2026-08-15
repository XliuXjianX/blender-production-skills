---
name: blender-procedural-systems
description: Build efficient Blender repetition, Array-driven stairs/modules/openings, instancing, scattering, Bezier/NURBS curve-profile geometry, Geometry Nodes fields, repeat zones, simulation zones, particle-like systems, and collective motion. Use for stairs, railings, trim, pipes, cables, repeated windows/panels, vegetation, debris, crowds, rain, snow, modular structures, or any request involving dependent elements or reusable parameters.
---

# Blender Procedural Systems

Use procedural systems for repetition, distribution, fields, and reusable relationships, not as a substitute for every native Blender tool.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns source systems, native modifiers, curves,
instances, and procedural evidence only; it may not restart analysis or reroute the task.

Reversible Blockout may use semantic anchors and provisional source/control objects. Formal systems
require approved affected parts and formal sources. Report local failures as repair requests.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md` before choosing Array,
curve, instances, particles, or Geometry Nodes. Within the Router-approved route, this Skill owns
the source relationship, semantic dependencies, and direct-versus-node implementation comparison;
`blender-geometry-nodes-studio` owns the actual graph structure, field contracts, and evaluated
graph evidence. A node system is valid when fields, adaptive variation, coordinated sources,
complex curve data, scalable instances, or node state improve the requested output. A direct Array
or curve remains valid when it exposes the whole required control surface more clearly.

When `local_asset_library.requested=true`, use `blender-local-asset-library` only to discover and
inspect candidates. Do not append an opaque graph. Confirm the source dependencies, exposed inputs,
realization policy, and selected-system benefit before the owner records provenance.

## Upstream Gate

Require passed minimum Production Analysis for reversible Blockout and an approved Part Graph for
formal systems. A provisional source may be used only for reversible preview and must be replaced
or explicitly reclassified before formal production. A procedural system that generates a primary/structural shell must itself expose
the section, connection, realization, weld/Boolean, bevel, and evaluated-topology policy needed to
pass the same gates as a directly modeled mesh.

## Method Selection

- Simple linear or radial repetition: Array, linked duplicates, or collection instances.
- Repeated openings in one host: Array the cutter or source opening system; do not rebuild each
  opening or fragment the host wall into many boxes.
- Geometry following a path: curves, bevel profiles, Curve modifier, or curve-to-mesh nodes.
- Straight regular stairs: solve semantic flight, rise, run, exact count, axes, and landing
  ownership, then use one formal step source plus Array constant offset containing run and rise.
- L/U/spiral stairs and railings: solve flights, landings, supported edges, endpoint order,
  ascent, and bend direction first; generate dependents from that accepted skeleton.
- Rails, pipes, cables, hoses, molding, and trim: prefer a continuous Bezier/NURBS path with bevel
  depth/object; use Array plus Curve only when distinct source modules must follow the path.
- Large surface/volume scatter: Geometry Nodes instances.
- Emission with lifecycle and forces: particles when supported and appropriate.
- Stateful custom collective motion: Geometry Nodes Simulation Zone.
- Directed fish/bird/firefly motion: path or goal field plus local variation; use Boids only after version and control requirements are checked.
- Modular procedural topology: Geometry Nodes with named inputs and documented realization points.
- Animated object-space anime silhouette: route to `blender-npr-eevee`.
- Camera-aware contours, creases, intersections, or hidden lines: Grease Pencil Line Art or Freestyle.
- Eevee cel-shaded light bands: route to `blender-npr-eevee`.
- Cycles Shader Raycast outlines: route to `blender-npr-cycles`.

Read `references/procedural-methods.md` before creating a node group.
Read `references/npr-outline-methods.md` for toon shading or outline requests.
Read `../blender-direct-surface-modeling/references/construction-method-playbook.md` for native
generator comparison, stairs, openings, curve profiles, snapping, Displace, and modular kits.
Use `scripts/blender_forced_perspective_portal_case.py` only as a self-contained regression and
construction example for Boolean ownership, Array stairs, Collection Instances, and safe reruns;
do not treat its portal composition as a global scene template.

## Node And Instance Protocol

1. Define the source asset, distribution domain, density/spacing, orientation, scale range, seed, exclusions, and camera-distance policy.
2. Keep source assets separate and semantic.
3. Preserve instances until real geometry is required for collision, export, per-element edits, or destructive simulation.
4. Expose only meaningful group inputs with units, ranges, and defaults.
5. Lay out node graphs left-to-right with frames and non-overlapping nodes.
6. Test low counts first, then measure evaluated geometry and viewport cost.
7. Validate variation, clipping, synchronization, density falloff, and deterministic seeds.
8. Validate one source, the evaluated output, connected components after any realization, and the
   assembly interfaces at path endpoints before raising counts.

Record each output's native component block in `construction_graph.json`: source objects, system test
status, instance and realized counts, stable-ID policy, realization reason, and viewport vertex
budget. A Geometry Nodes or Array modifier without this declaration cannot pass Systems.

## Hard Rules

- Do not create hundreds of independent mesh objects when instances are sufficient.
- Do not realize instances early without a downstream requirement.
- Do not recreate Mirror, Bevel, Solidify, ordinary Array, or shader noise in Geometry Nodes.
- Do not use random values without stable IDs when animation consistency matters.
- Do not hide source assets or control objects without naming and collection policy.
- Do not correct a wrong stair or railing generator by moving its generated steps/posts. Correct
  the source path, flight, landing, axis, or frame and regenerate all dependents.
- Do not hand-duplicate regular steps, windows, posts, panels, louvers, or modules. Expose count,
  offset, fit, endpoint, and source ownership on one generator.
- Do not use Geometry Nodes merely because a path or Array has parameters. Escalate to Geometry
  Nodes only when fields, multi-source rules, exclusions, reusable topology, or state require it.
- `Join Geometry` is not Weld. When a continuous output is required, use an explicit shared-profile,
  Merge by Distance, Mesh Boolean, or reconstruction route and validate the evaluated mesh.
- Do not use procedural density or detail to conceal missing Structural or Transition Forms.

## Completion Gate

Report source count, instance count, realized geometry count, seed, exposed inputs, node-group name, simulation/cache status, and viewport/render budgets. Require readable node layout and pass the result to `blender-geometry-validation`.
