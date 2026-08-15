---
name: blender-geometry-validation
description: Audit Blender scenes and assets for topology, transforms, normals, surface continuity, classified connections, intersections, modifier/node intent, procedural performance, simulation stability, protected-scene changes, and fixed-view visual evidence. Use after every major modeling or simulation stage and before render, bake, export, or claims of completion.
---

# Blender Geometry Validation

Treat validation as an independent gate. A successful Python call or attractive screenshot is not proof of valid geometry.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, retry budgets, rollback, and pauses. This skill reports technical evidence as `PASS`, `WARN`,
or `FAIL`; it cannot reroute, mutate production state, restart analysis, or delete a project.
Send local repair requests with evidence to the Router.

## Required Inputs

- `construction_graph.json` for intended part relationships.
- `stage_state.json` for current stage and protected-scene scope.
- `part_review_scores.json` for bounded local gate decisions.
- A pre-change scene snapshot for mutation comparison.
- Task-specific thresholds derived from scale and relationship type.

Use `scripts/snapshot_scene.py` before high-risk work and `scripts/validate_scene.py` after it.
Always pass `--stage-state stage_state.json`. The validator writes only its report. When the report
recommends rollback, the Router applies it with
`../blender-production-router/scripts/apply_validation_decision.py`.
At Gate R1 or later, pass `--spatial-hypothesis spatial_hypothesis.json` so region mappings,
camera containment, and real connection-depth objects are checked against Blender. Read
`references/validation-gates.md` for interpretation.

## Checks

- Mesh legality: non-manifold edges, boundaries, loose elements, zero-area faces, degenerate edges, duplicate positions, normals, transforms.
- Surface quality: aspect ratios, edge-length jumps, symmetry, boundary gap, adjacent-normal discontinuity, visible shading risk.
- Relationships: classified seams, Boolean fusion, embedded parts, intended independence, physical contact, unexplained overlap.
- Modifiers and nodes: expected stack, missing targets, disabled render state, accidental Geometry Nodes, excessive realization.
- Simulation: participants, collision roles, cache state, frame bounds, excessive displacement, velocity, tunneling evidence.
- Scene safety: protected objects, World, cameras, materials, collections, and file path changes.
- Visual evidence: orthographic, perspective, wireframe, MatCap, and reflective checks with unique filenames.
- Production stage: analysis mutation lock, Blockout proxy conversion, form-gate order, forbidden
  Functional/Detail work, and topology rollback state.
- Progressive analysis: permit only task-owned reversible Blockout when the minimum-analysis gate
  is provisional; require complete affected-part analysis before formal topology or systems.
- Part reviews: validate stage criteria, evidence, unique attempt IDs, a maximum of two automatic
  attempts, local pause/continue lists, and critical-part visual-gate behavior.
- Formal topology: construction-operation evidence, connected-component intent, evaluated bevel
  geometry, Boolean cleanup evidence, final-object mapping, and wireframe acceptance.
- Semantic geometry: required closed volume, connected-component count, smooth-face coverage,
  material class, volume response, and minimum thickness evidence declared per construction part.
- Visual-only regions: presentation masks, negative space, lighting regions, and camera effects may
  use `validation_mode: visual_only` with existing image evidence instead of a fabricated mesh.
- Reference evidence: when `reference_gate.json` exists, require its current gate, blockers, and
  evidence paths to agree with `stage_state.json`.
- Spatial evidence: when `spatial_hypothesis.json` exists, require the camera region, region graph,
  scale anchors, portals/elevation transitions, spatial invariants, camera revision, and required
  cross-view blockout evidence to agree with the scene and reference gate.
- Directional structures: require mapped start/end anchors, control objects, generated objects,
  path order, ascent/travel direction, supported edge, landing ownership, frame stability, endpoint
  contact, support, and clearance. Reversed stairs or railings and hand-patched generated members
  are failures.
- Native construction generators: validate monolithic host/cutter ownership for openings,
  rise/run/count and constant Array offset for regular stairs, source/count/fit dependencies for
  repeated modules, path/profile/frame ownership for curve sweeps, measured gap/orientation for
  snapped placement, and source density/coordinates/evaluated motion for Displace.
- Materials: require declared substrate class, physical mapping scale, UV/tangent direction where
  needed, correct PBR data color spaces, independent roughness/normal/displacement ownership,
  causal layer masks, and neutral plus grazing-reflection evidence. Use
  `blender-material-surfacing/scripts/audit_materials.py` for hero material audits.

## Status Rules

- `PASS`: all required checks and evidence pass.
- `WARN`: known intentional exception is documented and does not block the next stage.
- `FAIL`: required artifact is missing, topology/relationship contradicts intent, simulation is unstable, or protected state changed.

Unknown checks do not become PASS. Report them as `not_evaluated` and keep the relevant gate closed.
An unavailable or failed depth/white-model derivative is not an unknown geometry check and never
blocks production when `reference_derivatives.json.blocking` is false.

## Hard Rules

- Do not require closed-manifold geometry from an intentionally open cloth or surface asset.
- Do not require all-quads for every hard-surface or static asset.
- Do not use one absolute millimeter threshold for every scale.
- Do not approve a continuous surface from object overlap alone.
- Treat unclassified visible intersections as `FAIL` after Blockout; they are topology rollback
  strikes, not advisory warnings.
- Do not approve `B_OBJECT_JOIN`, Join Geometry, parenting, or collection membership as
  `D_TOPOLOGY_FUSION`.
- Do not approve a passed topology part with an unresolved final object, retained Blockout proxy,
  missing construction operations, missing component count, or missing wireframe evidence.
- Do not let lighting or materials hide a geometry failure.
- Do not overwrite review images at the same path.
- Do not approve a liquid material from IOR or reflection alone; require declared volume and
  surface/volume response.
- Do not approve a visible curved surface without smooth-shading and faceting evidence.
- Do not approve stairs, railings, ramps, or path-driven structures from camera appearance alone.
  Require top/side evidence and scene mappings to the same accepted semantic skeleton.
- Do not approve bare metal from gray Base Color plus Metallic alone, wood from box-projected color
  alone, or wetness from uniform darkening/gloss alone.
- Do not replace raw validator output with a manually authored summary that changes status.
- Do not force a non-geometric `P0` observation into visible validation-only geometry. Allow
  `visual_only` only for presentation, lighting-region, camera-effect, or helper roles, and require
  evidence files that exist on disk. Architectural negative space belongs in the spatial graph and
  must be explained by real boundaries and connected regions.
- Do not stop unrelated parts because a non-critical part has two failed reviews. Freeze only the
  failed part. Do not allow a third automatic review attempt under a new attempt ID.

## Completion Gate

Write `validation_report.json` with schema version, overall status, per-check evidence, thresholds, intentional exceptions, and repair suggestions. Refuse final export or completion claims while required checks are `FAIL` or `not_evaluated`.

One topology strike fails its affected part. Two distinct strikes set
`rollback.required=true`, choose `topology_construction` or `structural_forms`, reopen dependent
gates, and block Systems, Surfacing, Lighting, and Final progression until repaired.

Use `scripts/construction_method_integration_smoke.py` only with isolated
`--background --factory-startup` Blender to prove that Boolean, Array, Bezier profile, snapping
configuration/placement, and Displace fixtures evaluate as real Blender data.
