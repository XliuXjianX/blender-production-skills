---
name: blender-deformation-rigging
description: Select, build, and validate Blender deformation and motion-control systems including Simple Deform, Curve, Lattice, Mesh Deform, Shrinkwrap, Surface Deform, Armature, shape keys, hooks, constraints, and drivers. Use when an object must bend, twist, taper, follow a path, conform to a surface, deform smoothly, articulate, or move through controlled mechanical relationships.
---

# Blender Deformation And Rigging

Use a controllable deformation system before manually moving many vertices.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, retries, and rollback. This skill owns native deformation, rigging, constraints, drivers,
and local control-range evidence only. It may not restart analysis or reroute after a failure.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md`. This Skill owns armatures,
constraints, drivers, shape keys, and direct deformation safety. Geometry Nodes may own a
field-driven deformation only when it provides a documented attribute or topology behavior a native
deform system cannot express cleanly; it does not replace mechanical limits, rig relationships, or
tested control ranges. For an explicit local rigging asset request, use
`blender-local-asset-library` only for source inspection and provenance before integrating it.

## Upstream Gate

Require minimum Production Analysis for reversible control previews and an approved Part Graph for
formal deformation. A deformation used to construct a formal static shape may run during
Topology/Transition Forms, but its input mesh, axis, origin,
segment density, and intended application state must be declared. Animation rigs, shape keys,
constraints, and final deformation stacks may not bind to Blockout proxies. Require passed Primary,
Structural, Transition, and topology gates for every influenced render part.

## Method Selection

- Regular bend, twist, taper, or stretch: Simple Deform.
- Follow or bend along a path: Curve modifier or curve-based construction.
- Smooth regional deformation of one or many objects: Lattice.
- Cage-driven complex deformation: Mesh Deform.
- Surface conformity: Shrinkwrap or Surface Deform.
- Reusable articulation or character deformation: Armature.
- Corrective or state-specific shape: shape keys and Corrective Smooth.
- Mechanical limits and relationships: object/bone constraints and drivers.
- Local attachment or falloff control: Hook, vertex groups, or custom properties.

Read `references/deformation-methods.md` for prerequisites and failure patterns.

## Protocol

1. Verify real scale, local axes, origins, topology density, and transform state.
2. Define the control object, influenced region, allowed motion, and preserved boundaries.
3. Create semantic vertex groups instead of hard-coded vertex indices.
4. Add the minimum native system that expresses the deformation.
5. Test extreme poses or full modifier limits, not only the default frame.
6. Check volume loss, twists, self-intersection, texture stretching, and neighboring clearances.
7. Keep the system non-destructive until baking or export requires application.
8. Re-run topology, interface, clearance, and wireframe validation on the evaluated extreme poses.

## Hard Rules

- Do not manually rotate every segment to imitate a regular bend or path deformation.
- For curved rails, pipes, tracks, and path-driven structures, solve ordered endpoints, path
  direction, supported edge, up axis, and local frame before generating the visible mesh. If the
  direction is wrong, fix the path and regenerate; never repair generated segments one by one.
- Do not use Geometry Nodes to imitate a native deform modifier without a field-driven reason.
- Do not bind a cage, armature, or surface deform system before scale and topology are valid.
- Do not use Cloth merely because an object is soft; time-dependent flexible response belongs to simulation.
- Do not apply a rig or deformation stack before testing its full range.
- Do not use deformation to conceal a wrong base silhouette, disconnected shell, missing mating
  surface, or inadequate topology density. Repair the source mesh first.
- Do not route a static manufactured pipe elbow to deformation merely because it bends. Send
  profile-driven static construction to `blender-direct-surface-modeling`; reserve Curve or
  Simple Deform for geometry whose editability or behavior is genuinely deformation-based.

## Completion Gate

Report control objects, modifier/constraint order, semantic groups, tested range, maximum observed penetration, and whether the result remains editable. Hand off physics-dependent motion to `blender-simulation-effects` and all final geometry checks to `blender-geometry-validation`.
