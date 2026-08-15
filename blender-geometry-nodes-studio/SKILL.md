---
name: blender-geometry-nodes-studio
description: Build, inspect, audit, and refactor Blender Geometry Nodes systems for procedural models, instancing, modular effects, curves, scattering, flocks, data visualization, fields, simulation zones, and node-graph cleanup. Use whenever a Blender task specifically calls for Geometry Nodes, reusable procedural node graphs, node connections/layout, or a scalable procedural asset.
---

# Blender Geometry Nodes Studio

Build Geometry Nodes as readable, reusable systems. Use a direct component when it exposes the
whole required result more simply, and use Geometry Nodes when fields, adaptive variation,
coordinated source rules, scalable instances, complex curve data, reusable topology, or node state
provide a documented benefit. Geometry Nodes do not require an explicit user request when that is
the better production system.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns node graphs, fields, instances, simulation
zones, and graph evidence only; it may not restart analysis or reroute the task.

When this skill participates in reversible Blockout, require minimum Production Analysis and
semantic source/control objects. Formal systems require passed Production Analysis and an approved
Part Graph; source assets must then be formal meshes, curves, or intentional instance sources, not
Blockout proxies. If the graph generates a primary or structural surface, record its form
level, construction method, section/connection logic, realization policy, component target,
bevel policy, and evaluated wireframe evidence in `construction_graph.json`.

Before editing a graph, read [graph-layout-contract.md](references/graph-layout-contract.md). Read [asset-library-findings.md](references/asset-library-findings.md) when the task involves outline generation, vegetation, data-flow visuals, text effects, complex modular effects, or flock-like motion.
Also read `../blender-production-router/references/system-choice-contract.md`. When the Router
marks `local_asset_library.requested=true` with `request_origin=user_explicit` or
`request_origin=router_node_candidate`, `blender-local-asset-library` may inspect a source group
but this Skill owns graph selection, integration, field contracts, readable layout, and evaluated
output evidence. Never use a library asset as an unexplained black box.

## Design

1. State the source geometry, domain, density or spacing, orientation, scale range, seed, exclusions, animation requirement, and performance budget.
2. Split large systems into semantic functional groups. Use a thin assembly group to connect generation, sampling, transformation, instancing, material assignment, and output.
3. Expose only meaningful group inputs. Name them by outcome, attach units and ranges, and keep a stable seed input whenever random variation is visible.
4. Preserve instances through the graph. Realize only for a downstream topology operation, collision, export, or per-element edit that requires real geometry.
5. Store or capture IDs and named attributes before topology-changing nodes. Drive time variation from stable IDs rather than random values that reshuffle every frame.

## Graph Layout

Lay graphs left to right in these frames: `00 INPUT`, `10 DOMAIN`, `20 GENERATE`, `30 SAMPLE`, `40 VARIATION`, `50 INSTANCE`, `60 FINISH`, `90 OUTPUT`.

- Keep the main geometry spine on one row.
- Place scalar/vector field controls in lanes above or below the geometry spine.
- Use direct wires for local dependencies; use named reroute buses only for a shared control crossing a stage boundary.
- Keep Zone input/output pairs aligned. A backward wire is valid only for a zone or an explicitly documented feedback relationship.
- Avoid generic node names, unlabeled group inputs, overlapping nodes, and decorative reroute chains.

## Build Rules

- Use `Instance on Points`, collection instances, and curve-to-mesh while preserving instances.
- Use `Store Named Attribute` only for data crossing a group or topology boundary; use `Capture Attribute` for short local flow.
- Use `Simulation Zone` only for stateful motion. For art-directed movement, prefer curves, goal fields, stable phases, or a hybrid.
- Use an `Array`, linked object, or curve before Geometry Nodes for simple regular repetition.
- Do not recreate ordinary Mirror, Bevel, Solidify, Array, or shader-noise work inside Geometry Nodes.
- `Join Geometry` only combines geometry streams. It does not weld boundaries or remove internal
  faces. Use Merge by Distance, Mesh Boolean, a shared curve/profile construction, or downstream
  reconstruction when the Part Graph requires `D_TOPOLOGY_FUSION`.
- Do not use procedural detail density to bypass missing Primary, Structural, or Transition Forms.

## Inspect And Validate

Run `scripts/inspect_geometry_nodes_asset.py` with Blender in background to inspect a reference `.blend` without editing it:

```powershell
& "F:\SteamLibrary\steamapps\common\Blender\blender.exe" --background "<asset.blend>" --python "<skill>/scripts/inspect_geometry_nodes_asset.py" -- "<report.json>"
```

For every delivered graph, verify that public inputs are named, node stages are framed, instances remain unrealized unless justified, random inputs use stable IDs where animation needs it, and the graph is readable at normal zoom. Report the group name, public inputs, source/instance/realized counts, seed behavior, simulation/cache state, and viewport/render budget.

Also compare the evaluated output to its Part Graph: connected-component count, visible
intersections, endpoint interfaces, real bevel geometry, front/side/top/hero clay, and wireframe.
Two topology rollback strikes invalidate the graph output even when the node graph itself is tidy.
Populate the output part's `procedural` contract with source objects, system status, instance and
realized counts, stable-ID policy, realization reason, and viewport vertex budget.
