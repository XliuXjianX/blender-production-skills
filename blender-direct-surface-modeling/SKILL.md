---
name: blender-direct-surface-modeling
description: Build and refine production Blender geometry through semantic vertex/edge/face editing, BMesh, subdivision control cages, Boolean construction, Displace relief, remesh, sculpt preparation, retopology, and deliberate surface connections. Use after blockout for hard-surface, product, organic, architectural openings, terrain/relief, or reference-driven assets when shape quality, topology, continuity, or realistic part integration matters.
---

# Blender Direct Surface Modeling

Replace blockout geometry with intentional construction. Primitive placement is allowed for blockout, cutters, and genuinely separate manufactured parts; it is not a final connection method.

Before work, read `../blender-production-router/references/topology-first-production-contract.md` and
`../blender-production-router/references/native-component-contract.md`.
Require minimum-analysis scope for reversible Blockout and formal-production scope, an approved Part
Graph, and a clear `analysis_readiness` review for formal geometry. A globally provisional analysis
permits Blockout only. Do not edit formal
topology for a part whose physical role, separation reason, construction method, connection method,
final object ownership, or route-changing uncertainty remains unresolved.

The Router owns route, stage, retry, and rollback state. This skill owns direct mesh construction and
local topology evidence only; it must not restart analysis or choose a replacement route.

Read `part_review_scores.json` before each part transaction. Continue independent parts when a
non-critical part is paused. Never touch a part marked `needs_user_review`; do not turn its local
failure into a project deletion request.

## Non-Skippable Form Order

1. `PRIMARY`: dimensions, silhouette, mass, and major negative space.
2. `STRUCTURAL`: large cuts, slopes, frames, cavities, supports, and load paths.
3. `TRANSITION`: blends, radii, shell turns, section changes, corner flow, and interfaces.
4. `FUNCTIONAL`: openings, handles, mounts, pivots, brackets, controls, and joints.
5. `DETAIL`: fasteners, markings, micro seams, wear, and small damage.

Do not add Functional or Detail geometry while Primary, Structural, or Transition is open. When a
model has primary blocks and tiny details but lacks middle-scale structure, roll back to Structural
Forms instead of adding more objects.

## Choose the Construction Route

- Hard-surface shell: direct mesh editing plus Boolean and controlled bevels.
- Smooth product form: low-density subdivision control cage with deliberate edge flow.
- Organic or fused volume: voxel remesh or Boolean union, sculpt cleanup, then retopology when required.
- Profile-driven form: curves, screw/spin, loft-like bridge operations, or contour-derived mesh.
- Reference-guided form: preserve measured silhouettes and landmarks while satisfying the routed
  spatial regions, depth intervals, supports, portals, and cross-view constraints. Do not postpone
  depth until after a screen-space fit.

Read `references/modeling-workflows.md` before executing a route that changes topology.
Read `references/construction-method-playbook.md` before building an architectural opening,
stair source, repeated module, rail/pipe/cable/trim path, snapped assembly, or displaced surface.

- For Boolean Difference, Union, Intersect, cutter stacks, Boolean cleanup, or Boolean-to-subdivision
  handoff, read `references/boolean-topology.md` before creating cutters.
- For vertex/edge/face construction, edge flow, poles, manifold repair, direct BMesh editing,
  subdivision cages, or retopology, read `references/topology-construction.md` before editing.

## Formal Modeling Protocol

1. Map every Blockout proxy to `replace`, `convert`, or `legitimate_independent_primitive`.
2. Record the local shape problem, form level, target semantic region, construction method, and
   expected connected-component count. Also record shape grammar, parameter owners, native
   generator comparison, and why any manual assembly is physically or downstream necessary.
3. Save a reversible checkpoint before destructive topology changes.
4. Select geometry with vertex groups, attributes, coordinates, normals, boundaries, connectivity,
   or edge-loop relationships. Do not rely on unstable raw indices across topology changes.
5. Perform one region-level operation: reshape, connect, subdivide, extrude, inset, bridge, weld,
   dissolve, cut, bevel, Boolean, spin, sweep, remesh, sculpt, or retopologize.
6. Recalculate mesh data and normals, then inspect the base cage and evaluated result.
7. Update `topology_evidence`: construction operations, component count, Boolean cleanup state,
   evaluated bevel state, and unique wireframe path.
8. Validate silhouette, edge flow, topology, continuity, neighboring interfaces, and all required
   views. Keep or restore the checkpoint before solving another unrelated problem.

For an environment reconstructed from images, read the task's `spatial_hypothesis.json` before
Blockout. Build boundaries and connections in region order: camera enclosure, foreground, main
space, elevation transitions, portals, hidden support regions, then off-frame continuations. A
matching camera silhouette does not approve disconnected stairs, zero-depth openings, unsupported
platforms, or black planes standing in for deeper space.

For every visible `primary_form`, `structural_part`, and curved `functional_detail`, record
the control topology, connection method, radial or bend segment policy, and shading policy.
Blockout primitives must be replaced or explicitly reclassified as genuinely separate
manufactured parts before the Primary Surface gate.

Box modeling means editing one or a few intentional meshes through connected vertices, edges, and
faces. It never means preserving a pile of scaled cubes as the formal shell. Prefer profile
extrusion for profile-led parts, section loops plus Bridge for changing cross-sections, Spin/Screw
for revolved bodies, and curve sweep for rails, cables, pipes, and frames.

For an opening cut through one monolithic wall, preserve one wall host and one semantic Boolean
cutter while dimensions are changing. Do not substitute top, left, and right wall cubes unless
those members are genuinely separate lintel/jamb construction. For editable sampled relief,
declare source subdivision, Displace coordinates, direction, midlevel, strength, and silhouette
budget before evaluating the modifier.

## Connection Classification

- `continuous_surface`: match boundary loops, bridge, weld, relax, and verify positional and normal continuity.
- `boolean_fused`: union closed volumes, remove internal geometry, repair non-manifold regions, and verify shading.
- `mechanical_seam`: keep parts separate with deliberate clearance, mating surfaces, and compatible bevel language.
- `embedded_component`: provide a receiving recess or mounting interface; do not leave unexplained penetration.
- `physical_contact`: keep objects independent and hand off to collision/physics when motion matters.
- `intentionally_independent`: preserve separation and document why.

Deep interpenetration may exist only in temporary hidden Blockout marked for replacement. A real
assembly fit may use a documented shallow insertion depth, but final visible/background assets may
not use deep overlap as a seam, support, or seamless connection.

For static tubular elbows and rolled profiles, prefer one continuous profile construction:
Spin/Screw, an editable curve converted with a deliberate resolution policy, or matched loops
bridged with enough cuts to hold the bend. Separate straight segments inserted into each other
are blockout only. Preserve cross-section area, weld the transition, and validate the bend in
reflective shading.

## Shading Discipline

- Apply smooth shading or Smooth by Angle to visible curved surfaces.
- Preserve intentionally flat caps, panel breaks, and manufactured creases with sharp edges,
  split normals, support geometry, or a documented smoothing-angle policy.
- Choose radial and bend subdivisions from silhouette and highlight error at final resolution,
  not from one universal segment count.
- Treat a Bevel modifier as geometry control, not as a substitute for smooth normals.
- Classify important edges as `PRIMARY_BEVEL`, `SECONDARY_BEVEL`, `MICRO_BEVEL`, or `SHARP_EDGE`.
  Record per-class widths derived from real scale and function; one global width is not an edge
  language. If an unchanged primitive is genuinely the manufactured final part, record the
  physical reason instead of silently treating every Blockout primitive as formal topology.
- Accept Edit/BMesh Bevel, evaluated Bevel Modifier geometry, subdivision support loops, or a
  deliberate crease strategy. Reject Shade Smooth, Weighted Normal, material highlights, bevel
  shaders, or separate corner pieces as evidence of a real bevel.
- Require a neutral MatCap and reflective review for every visible curved primary surface.

## Modifier Discipline

Choose stack order from intent:

- Decide whether a Boolean should cut the base cage, the thickened shell, or the subdivided result.
- Decide whether Bevel controls manufactured edge radius or only shading.
- Decide whether Solidify thickness should inherit deformation.
- Keep Mirror, Array, and deformation origins explicit.
- Keep Array source, count/fit policy, relative/constant/object offset, merge policy, and endpoint
  ownership explicit. A regular stair flight normally uses exact constant run-and-rise offset.
- Keep Displace source density, coordinate system/object, texture, direction, midlevel, strength,
  vertex group, and stack order explicit.
- Apply modifiers only when downstream topology editing, export, or simulation requires evaluated geometry.
- Choose Fast, Exact, or Manifold Boolean solver from operand validity, overlap, and downstream
  needs; do not treat Exact as an automatic substitute for clean operands.
- Preserve non-destructive cutters while the design is changing. Apply and reconstruct only when
  UV, deformation, export, sculpt, or later topology editing requires real evaluated topology.

There is no universal modifier order.

## Completion Gate

Do not mark the modeling stage complete until:

- primary silhouettes pass front, side, top, and perspective review;
- environment regions and portals agree with `spatial_hypothesis.json`, and required camera, top,
  front, and side blockout views exist;
- continuous joins are welded or deliberately reconstructed;
- visible intersections are classified;
- non-manifold, internal-face, normal, and scale checks pass for the intended asset type;
- smooth surfaces pass reflective or MatCap highlight inspection;
- visible curved surfaces report smooth-face coverage, sharp-edge policy, radial segments, and
  projected faceting risk;
- continuous assemblies report one connected component or a documented reconstructed seam,
  not merely overlapping bounding boxes;
- `construction_graph.json` and `validation_report.json` agree with the actual scene.
- Boolean routes report solver, operand validity, coplanar policy, internal-face/sliver checks,
  application state, and downstream topology route.
- topology routes report intended deformation/subdivision/export use, boundary and manifold state,
  edge-flow review, pole placement, aspect-ratio risks, and semantic selection method.
- every replaced Blockout proxy is removed or archived outside the final asset collection;
- every major part reports its actual connected-component count and construction operations;
- Primary, Structural, and Transition gates pass before Functional or Detail objects exist;
- front, side, top, hero clay, and wireframe evidence use distinct existing files;
- fewer than two topology rollback strikes remain. One strike fails its affected part; two force a
  return to Topology Construction or Structural Forms.
- the affected part's current stage review is `pass` or a score of at least `60` with recorded local
  repairs; two lower attempts pause that part without consuming a third attempt.
