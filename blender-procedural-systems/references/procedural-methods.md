# Procedural Method Notes

## Directional Structures

- Treat the accepted stair flight, landing graph, railing support edge, or ordered curve as the
  source of truth. Generated steps, posts, rails, brackets, and fittings are dependents.
- For a straight stair, solve total rise, total run, exact step count, per-step rise, and per-step
  run before Array or node generation. Use one formal step source and an exact constant offset
  containing both run and rise. Force the final generated level to meet the landing exactly.
- For L- and U-shaped stairs, generate separate flights from one connected landing graph. Do not
  infer turn direction independently inside each node branch.
- For curved railings, distribute supports by arc length and build orientation from tangent plus a
  declared up vector. Add an explicit fallback frame near vertical tangents.
- Keep start/end anchors, path direction, supported-edge ID, handedness, step count, spacing, and
  seed exposed as semantic inputs. Hide low-level sockets that can invalidate the structure.
- If ascent, bend side, landing contact, or profile orientation is wrong, discard the generated
  output and repair the source skeleton. Never move instances into place one by one.

## Repetition Choice

- Array: simple regular sequence with editable source.
- Linked/collection instance: repeated complete asset with low overhead.
- Curve plus Array: regular modules following a path.
- Geometry Nodes: field-driven scatter, multiple sources, exclusions, LOD, or reusable procedural topology.
- Particles: emission, lifecycle, forces, or Boids when the current version supports the required workflow.

For repeated windows or portals in one host wall, repeat semantic cutter/opening controls and keep
one wall volume. For modular wall panels that are physically separate, keep one linked source and
snap instances from declared connector planes. Do not confuse those two construction grammars.

## Curve Profile Choice

- Curve bevel depth/object: one continuous constant-profile rail, pipe, cable, hose, molding, or trim.
- Curve Modifier: deform an existing mesh source along a path.
- Array plus Curve: distinct regularly repeated modules follow a path.
- Geometry Nodes: fields, multiple source rules, exclusions, variable profiles, or reusable
  procedural topology justify the graph.

Keep point order, path direction, up/frame policy, profile orientation, path resolution, bevel
resolution, cyclic state, endpoint caps, and conversion policy explicit.

## Geometry Nodes Graph Contract

1. Name the node group and every public input semantically.
2. Put units, minimum, maximum, and default values on public inputs.
3. Organize nodes left-to-right: input, domain, selection, generation, variation, output.
4. Use frames for stages and keep nodes non-overlapping.
5. Preserve stable IDs before random animated variation.
6. Keep instances until collision, export, or per-element topology requires realization.
7. Record source/evaluated/realized counts.

## Fish, Birds, Fireflies

Choose from:

- Boids for autonomous separation/alignment/cohesion when available.
- Geometry Nodes Simulation Zone for custom stateful behavior.
- Curves or goal fields for art-directed macro motion.
- Noise and stable per-instance phase for local variation.
- A hybrid for hero shots: directed group motion plus independent near-camera actors.

Do not keyframe every individual and do not accept synchronized noise as natural behavior.

## Environment Scatter

- Define inclusion and exclusion masks.
- Use density by area and camera-distance budgets.
- Align orientation to normals only when physically appropriate.
- Introduce scale, rotation, source, and clustering variation independently.
- Prevent intersections with paths, walls, or protected assets.
