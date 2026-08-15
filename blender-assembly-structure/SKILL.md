---
name: blender-assembly-structure
description: Plan, build, place, and validate physically meaningful Blender object assemblies, including manufactured part boundaries, mechanical seams, mounting interfaces, pivots, hierarchy, constraints, instancing, modular grids, connector planes, and precision snapping. Use when several objects must form one product, machine, architectural module, vehicle, furniture item, mechanism, or environment structure without incorrectly welding independent parts, eyeballing alignment, or leaving continuous shells as overlapping primitives.
---

# Blender Assembly Structure

Own object-level construction and scene assembly. Do not claim topology fusion merely because
objects share a parent, collection, material, or object container.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router alone owns
route, stage, budgets, rollback, and pauses. This skill owns object boundaries, interfaces,
placement, and assembly evidence only; it cannot restart analysis, reroute, or delete a project.

Use a provisional Part Graph for reversible Blockout. Require an approved Part Graph only when
entering `formal_production` or committing Functional Parts. Emit local repair requests instead of
creating a second state machine.

## Required Part Graph

Before assembly, classify every buildable part in `construction_graph.json`:

- physical function and form level;
- continuous or separate manufacturing state;
- reason for separation;
- construction method and final object name;
- combination level `A`, `B`, `C`, or `D`;
- connection or interface method;
- pivot, motion, constraint, material, modifier, instance, and export ownership;
- bevel class and clearance policy.

Difficulty is never a valid reason to split one continuous shell into several penetrating objects.
Run `scripts/validate_part_graph.py` before formal production and again before Functional Parts.

Derive part boundaries from manufacturing, independent motion, a real material/transparent
interface, instancing, modifier/export ownership, or a visible seam. Do not split by reference
color blocks, convenience, or local modeling difficulty. A complex continuous shell remains one
topological responsibility even when several temporary construction objects help create it.

Read `references/assembly-production.md` for the complete assembly and interface protocol.
Read `../blender-direct-surface-modeling/references/construction-method-playbook.md` when the
assembly uses modular grids, snapping, repeated modules, host openings, or path-generated parts.

## Combination Levels

- `A_VISUAL_GROUPING`: transforms, parenting, or collection organization; valid for Blockout or
  already independent parts, never topology proof.
- `B_OBJECT_JOIN`: one object container with possibly several disconnected mesh islands; use only
  when one data container is useful and the islands remain semantically independent.
- `C_PHYSICAL_ASSEMBLY`: separate manufactured or moving parts with seams, mating surfaces,
  clearances, mounts, fasteners, pivots, or constraints.
- `D_TOPOLOGY_FUSION`: one continuous volume or shell created through shared topology, Bridge,
  Weld, Boolean Union plus cleanup, remesh, or reconstruction. Hand this route to
  `blender-direct-surface-modeling`.

## Assembly Protocol

1. In `reversible_blockout`, record provisional part roles and interfaces before mutation; approve
   the affected Part Graph before formal production.
2. After Blockout, replace or convert proxies and send every `D_TOPOLOGY_FUSION` part to
   `blender-direct-surface-modeling` before assembly detail.
3. Build primary load-bearing parts and receiving interfaces first.
4. Establish mating surfaces, wall thickness, recesses, sockets, pivots, and scale-derived clearance.
5. Establish grid units, module origins, connector planes, snap element/base/orientation, and
   target ownership before placing repeated architectural or product modules.
6. Add hinges, fasteners, latches, seals, handles, or constraints only when their function and
   attachment are defined.
7. Organize collections by production role: model, cutters, controls, fasteners, glass, collision,
   simulation, lighting, cameras, and export.
8. Test open/closed or extreme mechanical states where parts move.
9. Validate every visible contact and every unexplained overlap from front, side, top, hero, and
   wireframe views.

## Hard Rules

- Join Objects does not weld vertices or remove disconnected islands.
- Parent and Collection do not create physical interfaces.
- A shared material does not make objects one manufactured part.
- Do not push a button, handle, bearing, or panel through its receiver without a recess, mount, or
  documented hidden tolerance.
- Do not Boolean-union parts that must move, be replaced, remain transparent, or preserve a seam.
- Do not keep a continuous shell fragmented because one local transition is difficult.
- Do not use fasteners as decoration before the mounting logic exists.
- Do not create Functional or Detail parts before Primary, Structural, and Transition gates pass.
- Do not eyeball modular alignment or accumulate repeated transform drift. Snap one source or
  instance from a declared origin/connector convention and measure the resulting gap.

## Completion Gate

Require mapped final objects, valid collection ownership, classified combination levels, intentional
mesh-island counts, mating interfaces, seam/clearance evidence, tested pivots or constraints, and no
unclassified visible intersections. Send continuous topology to `blender-direct-surface-modeling`
and final checks to `blender-geometry-validation`.
