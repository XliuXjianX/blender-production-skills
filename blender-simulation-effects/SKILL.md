---
name: blender-simulation-effects
description: Design, configure, test, bake, and validate Blender physical effects including Cloth, Soft Body, Rigid Body, collisions, constraints, Fluid, smoke, fire, Dynamic Paint, Ocean, Wave, particles, Boids, force fields, fracture, debris, and secondary effects. Use when gravity, inertia, collision, flexibility, pressure, flow, flocking, emission, or breaking causes the requested result.
---

# Blender Simulation Effects

Treat physical causes as simulation problems before treating their final appearance as static modeling.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns physical participants, solver setup, preview,
cache, and stability evidence only; it must not restart analysis or silently replace a simulation.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md`. This Skill owns physical
causality, participants, solver choice, cache, and stability. Geometry Nodes may generate emitters,
instances, masks, or post-process a result when it gives a documented procedural advantage, but a
hybrid must declare one `time_state_owner`; a graph cannot silently replace gravity, collision,
flow, or material response. A requested local particle or VFX asset is discovered read-only by
`blender-local-asset-library`; this Skill owns compatibility, integration, and simulation evidence.

## Upstream Gate

Require minimum Production Analysis for a reversible low-resolution test and an approved Part Graph,
real scale, classified physical participants, and passed formal topology/Structural/Transition gates
for final simulation. A dedicated low-resolution
simulation mesh is allowed, but it must be mapped to the render mesh and may not be an unexplained
Blockout proxy. Colliders need real thickness/contact intent appropriate to the solver.

## System Routing

- Thin flexible sheet, clothing, flag, drape: Cloth plus Collision and optional Self Collision.
- Elastic spring-like or volumetric deformation: Soft Body.
- Falling, rolling, stacking, impact: Rigid Body plus passive colliders.
- Hinges, breakable joints, mechanical physics: Rigid Body Constraints.
- Liquid, smoke, fire, inflow, outflow: Fluid domain and flow/effectors.
- Surface response maps and local interaction: Dynamic Paint.
- Deep-water macro waves and foam data: Ocean modifier.
- Local procedural ripples: Wave modifier, Dynamic Paint, or shader detail.
- Static contained liquid with no visible motion: a closed container-conforming volume with
  physically plausible surface and volume shading; use Fluid only when volumetric motion,
  splashing, filling, or collision changes the visible result.
- Emission and lifecycle: particle system or Geometry Nodes points.
- Flocking/schooling: Boids when available, Geometry Nodes simulation, curve-guided instances, or a justified hybrid.
- Destruction: installed fracture extension or deterministic fracture geometry plus rigid bodies, constraints, debris, and dust.

Read `references/simulation-methods.md` before creating a cache.

- For cloth, garments, curtains, flags, sewing, pinning, animated colliders, or fold quality,
  read `references/cloth-production.md` before adding the Cloth modifier.
- For contained water, oceans, ripples, pouring liquid, splashes, wet maps, foam, spray, or
  liquid caches, read `references/water-production.md` before choosing a system.

## Simulation Protocol

1. Probe the current Blender version and installed extensions.
2. Validate units, scale, transforms, topology, thickness, normals, and collider roles.
3. Build a low-resolution isolated test over a short frame range.
4. Record solver, participant, cache, collision, material-response, and field settings.
5. Simulate and inspect penetration, instability, tunneling, explosive bounds, energy gain, and unrealistic synchronization.
6. Adjust one parameter class at a time and repeat up to three technical loops.
7. Bake only after the low-resolution gate passes.
8. Add render subdivision, thickness, secondary debris, spray, foam, or dust after simulation.
9. Preserve the pre-bake setup and report cache paths.
10. Compare the simulated result against the accepted unsimulated silhouette and assembly graph;
    simulation does not excuse detached mounts, missing seams, or impossible support.

Record each participant's `simulation` block in `construction_graph.json`, including system, role,
cache policy, low-resolution frame range, penetration metric/threshold, and evidence. A modifier or
rigid body without this declaration cannot pass the Systems gate.

## Hard Rules

- Do not hand-model gravity folds, impact positions, flow, or fracture when a suitable simulation exists.
- Do not start a final simulation while the source asset still fails topology, transition, support,
  collision-interface, or wireframe gates.
- Do not weld objects merely because they touch physically.
- Do not assume Cell Fracture or another extension is installed.
- Do not use final-resolution settings for the first test.
- Do not claim realism from a successful bake alone; validate material behavior and motion evidence.
- Do not overwrite an accepted cache without a versioned checkpoint.
- Do not call a plane, open surface, or thin beveled slab a liquid volume.
- Do not infer water from a dark or reflective container interior without reference evidence.
- Do not omit volume absorption when visible liquid thickness materially affects the shot.
- Do not use cloth presets as proof of material identity; calibrate mass, stiffness, damping,
  collision, topology, and fold scale against the requested fabric and real scene scale.
- Do not add Solidify or render subdivision ahead of Cloth unless the route explicitly requires
  those evaluated vertices in the simulation and the cost has been tested.
- Do not call a reflective plane a water body, and do not run Mantaflow for a static water volume
  whose shape does not change.

## Completion Gate

Require stable test frames, documented participants, valid cache state, acceptable penetration, bounded velocities and scene bounds, and a review render/contact sheet. Hand off procedural instance systems to `blender-procedural-systems` and numerical validation to `blender-geometry-validation`.

For static contained liquid, replace cache requirements with evidence of a closed non-zero
volume, container conformity, waterline and contact policy, surface/volume material response,
and any visible ripple cause. Preserve the reference hypothesis that justified the liquid.
