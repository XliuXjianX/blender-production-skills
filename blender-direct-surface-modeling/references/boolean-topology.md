# Boolean Construction And Cleanup

## Contents

1. Decide whether Boolean is correct
2. Prepare target and cutters
3. Choose operation and solver
4. Choose modifier order
5. Inspect the evaluated result
6. Choose the downstream topology route
7. Union and connection policy
8. Repeated and layered cuts
9. Failure diagnosis
10. Blender Python pattern
11. Validation gate
12. Official sources

## 1. Decide Whether Boolean Is Correct

Use Boolean for volume logic:

- Difference for drilled holes, vents, recesses, slots, panel cutouts, and negative volumes;
- Union for volumes that must become one manufactured/static body;
- Intersect for keeping only shared volume or constructing a derived region.

Do not use Boolean for:

- physical contact between independent objects;
- a mechanical seam that should remain open;
- a shallow visual line better made by inset, normal, or decal;
- a smooth product surface when the cutter topology would create uncontrolled highlight dents;
- cloth, fluid, or deforming contact.

Classify the resulting relationship as `boolean_fused`, `mechanical_seam`, `embedded_component`,
or `intentionally_independent` before construction.

## 2. Prepare Target And Cutters

### Target

- Confirm real scale and object transforms.
- Inspect manifold state, normals, duplicate faces, tiny edges, existing self-intersections, and
  modifiers that change the target before Boolean evaluation.
- Decide whether the cut belongs to the base cage, thickened shell, deformed object, or evaluated
  subdivided surface.

### Cutter

- Give every cutter a semantic name and collection.
- Use a closed manifold volume for predictable volume cuts whenever possible.
- Extend a Difference cutter cleanly through the target rather than ending coplanar with a face.
- Avoid barely touching surfaces and ambiguous coplanar overlap.
- Match cutter bevel/radius to the desired manufactured cut, not to the convenience of the primitive.
- Keep cutter resolution proportional to final silhouette/highlight requirements.
- Hide cutters from final render without deleting their editability.

Use a collection operand for coordinated cutter sets only when ordering and material behavior are understood.

## 3. Choose Operation And Solver

### Float (Legacy Documentation May Call This Fast)

Use the installed `FLOAT` solver for clean manifold operands with simple non-overlapping
intersections when speed matters. Older documentation and versions may expose a `FAST` name. It is
less reliable for overlapping/coplanar complexity. If the result is wrong, repair the operands or
use a more suitable solver rather than only increasing overlap threshold.

### Exact

Use for coplanar or overlapping cases, self-intersection handling, material transfer requirements,
or difficult operands. It is slower and still requires result inspection. Hole Tolerant and Self
Intersection options are targeted repairs, not defaults for every cut.

### Manifold

Use when all participating meshes satisfy its manifold requirements and performance matters. It
does not replace validation; unsupported non-manifold input must be repaired or routed elsewhere.

Record solver and solver options per Boolean. Do not standardize one solver for the whole project.

## 4. Choose Modifier Order

Examples are conditional, not universal:

- Mirror -> Boolean: cut participates in symmetry or cutter exists in evaluated mirrored space.
- Boolean -> Mirror: cut only the source side and mirror the result.
- Boolean -> Bevel: manufactured cut edges receive a common downstream radius.
- Bevel -> Boolean: cutter removes already-rounded geometry and may create different edge behavior.
- Solidify -> Boolean: cut a real shell volume through inner and outer walls.
- Boolean -> Solidify: cut an open sheet, then generate thickness around the opening.
- Subdivision -> Boolean: cut an evaluated smooth surface, usually higher cost and harder topology.
- Boolean -> Subdivision: Boolean result must support subdivision; often requires controlled cleanup/retopology.

Test the intended evaluated result at final view. Modifier order is a construction decision, not a formula.

## 5. Inspect The Evaluated Result

Inspect with cutter wireframe visible, X-Ray, face orientation, neutral MatCap, and moving reflective light.

Check:

- internal faces and trapped shells;
- new boundary/non-manifold edges;
- zero-area or extremely small faces;
- long thin slivers and near-coincident vertices;
- inverted normals or material assignment errors;
- coplanar flicker and missing regions;
- shading dents across intended planar/curved surfaces;
- bevel width consistency around generated edges;
- connected components after Union;
- silhouette and opening dimensions against the reference.

A visually empty hole from one camera is not proof that the volume cut is valid.

## 6. Choose The Downstream Topology Route

### Keep Non-Destructive

Use for changing hard-surface designs, static render assets, and cutters that shade correctly. Keep
operands named, grouped, and render-disabled. UV only the surfaces that exist before the stack or
use a later application checkpoint when the design is locked.

### Apply And Clean

Use when export, UV, direct editing, simulation, sculpt, or downstream tools require real geometry:

1. duplicate/save the non-destructive source;
2. apply at a controlled checkpoint;
3. remove doubles only within a scale-derived tolerance;
4. dissolve redundant coplanar edges without changing silhouette;
5. rebuild local faces where slivers or shading errors matter;
6. recalculate normals and restore sharp/smooth policy;
7. validate manifold state, face quality, and material slots.

### Retopologize/Reconstruct

Use when the result must subdivide smoothly, deform, carry controlled loops, or produce clean hero highlights.

- Rebuild the transition with deliberate quad flow.
- Place poles away from high curvature and deformation paths.
- Keep circular/slot boundaries supported without dense topology radiating across the whole object.
- Project or Shrinkwrap to the accepted Boolean shape while preserving dimension/edge intent.
- Compare the reconstructed result to the saved Boolean reference.

Do not force every static hard-surface Boolean into all-quads. Do not feed arbitrary Boolean N-gons
into Subdivision and hope more levels remove pinching.

## 7. Union And Connection Policy

Boolean Union is only the start of a fused connection. After Union:

- confirm one connected exterior component where required;
- remove internal shells/faces;
- rebuild the visible transition if it needs a continuous radius or curvature;
- add a weld bead or mechanical seam only when physically correct;
- check wall thickness and cavities;
- review high-frequency shading under a long reflection.

For organic fusion, Voxel Remesh and sculpt cleanup may be more suitable. For continuous
subdivision surfaces, matched loops/Bridge or retopology may be better than a Boolean Union.

## 8. Repeated And Layered Cuts

- Use Array or Geometry Nodes to repeat cutters when the pattern is regular and remains editable.
- Keep major, secondary, and micro cuts in separate stages.
- Avoid dozens of independent booleans with overlapping coplanar faces when one coordinated cutter
  volume or collection is clearer.
- Validate performance and dependency order.
- Apply only the stage needed for subsequent topology work.

### Architectural Openings

For a doorway, window, archway, or niche cut into one monolithic wall, use one closed wall host and
one semantic through-thickness Difference cutter. Let the cutter own width, height, sill/head,
reveal depth, and radius while the host owns wall thickness and extent. Add frame, trim, glass, and
door leaf only after the evaluated opening passes.

Reject top/left/right boxes that merely imitate a hole in one wall. Accept separate lintel and jamb
objects only when they are physically separate construction members recorded in the Part Graph.
Array the cutter or opening system for repeated windows; do not fragment the host wall or duplicate
independent cuts by hand.

## 9. Failure Diagnosis

### Missing Or Flickering Faces

Repair coplanar/tangent contact, normals, zero thickness, non-manifold operands, and duplicate faces;
then choose Exact or Manifold according to valid input.

### Shading Dents On Flat Panels

Inspect slivers, N-gon triangulation, bad normals, bevel order, and cutter proximity. Rebuild local
topology or keep the panel planar with explicit sharp/smooth policy.

### Bevel Breaks Around Cut

Check generated edge angles, tiny edges, clamp overlap, scale, bevel order, and whether the cut
radius is smaller than the requested bevel. Reconstruct the boundary when needed.

### Union Still Contains Internal Geometry

Check operand overlap, solver, self-intersections, collection operands, and disconnected source
components. Run interior/manifold checks after application.

### Subdivision Pinches

Do not add levels. Rebuild the cut boundary and edge flow or keep a bevel-based hard-surface route.

## 10. Blender Python Pattern

```python
modifier = target.modifiers.new(name="BOOL_WindowCut", type="BOOLEAN")
modifier.operation = "DIFFERENCE"
modifier.operand_type = "OBJECT"
modifier.object = cutter
modifier.solver = "EXACT"
```

Before execution, feature-detect solver/options from RNA (`FLOAT`/legacy `FAST`, `EXACT`, and
`MANIFOLD` where available), record target/cutter names and transforms,
and save a checkpoint. After evaluation, inspect the evaluated mesh rather than only the modifier stack.

## 11. Validation Gate

Require:

- intended relationship and operation;
- target/cutter manifold and transform report;
- solver and option justification;
- modifier-order justification;
- evaluated internal-face, boundary, sliver, normal, component, and shading checks;
- non-destructive/application/retopology decision;
- reflective and wireframe evidence with unique filenames;
- downstream UV, subdivision, deformation, simulation, and export compatibility.

## 12. Official Sources

- Boolean Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/booleans.html
- Intersect Boolean: https://docs.blender.org/manual/en/5.2/modeling/meshes/editing/mesh/intersect.html
- Bevel Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/bevel.html
- Weld Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/weld.html
