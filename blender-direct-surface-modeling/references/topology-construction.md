# Direct Topology Construction

## Contents

1. Define topology requirements
2. Semantic selection
3. Vertex, edge, and face operations
4. Edge flow and density
5. Subdivision topology
6. Hard-surface topology
7. Connections and boundaries
8. Retopology
9. Cleanup and validation
10. Blender Python and BMesh pattern
11. Failure diagnosis
12. Official sources

## 1. Define Topology Requirements

Before editing, classify the asset:

- static hard-surface render;
- subdivision product surface;
- deforming/rigged asset;
- sculpt/Multiresolution asset;
- simulation mesh;
- export/game mesh;
- architectural/environment shell.

Record required symmetry, silhouette views, deformations, UV seams, material boundaries, thickness,
connections, target density, and whether N-gons/triangles are acceptable for this use.

Topology is successful when it supports shape, shading, deformation, UV, and downstream editing.
All-quads alone are not a quality metric.

## 2. Semantic Selection

Do not depend on raw element indices across topology changes. Select through:

- named vertex groups and custom attributes;
- boundary/non-manifold state;
- connected components and shortest/topological paths;
- local coordinate ranges and symmetry plane distance;
- face/vertex normal direction;
- material regions and seams;
- edge angle, valence, loop/ring neighborhoods;
- proximity to named helper geometry or reference landmarks.

Raw indices are acceptable only inside one deterministic operation before topology changes.

## 3. Vertex, Edge, And Face Operations

Use existing geometry before adding another primitive:

- Move/scale/rotate vertices or loops to correct silhouette and curvature.
- Extrude faces/edges to continue the same structural surface.
- Inset to create controlled panel boundaries or recessed regions.
- Loop Cut/Subdivide to add resolution where a shape or deformation needs control.
- Edge/Vertex Slide to reposition control without destroying surrounding form.
- Merge/Weld to create one boundary; use scale-derived tolerance.
- Bridge Edge Loops to connect compatible open boundaries.
- Dissolve to remove unnecessary topology while preserving the surface.
- Bevel selected edges/vertices for real transition width.
- Knife/Bisect/Intersect for purposeful cuts with a cleanup plan.
- Grid Fill for suitable regular holes; inspect pole placement and interpolation.

Perform one shape problem at a time, then inspect all required views.

## 4. Edge Flow And Density

- Put loops where they control silhouette, curvature, deformation, material seams, openings, or
  contact. Every dense loop should have a reason.
- Keep spacing gradual across smooth surfaces.
- Avoid sudden density jumps, long thin faces, tiny isolated faces, and high-valence poles in hero highlights.
- Align loops with bending/compression directions on deforming assets.
- Keep poles away from joints, eyelids/mouths, high curvature, and moving highlight paths when possible.
- Preserve a low-density editable cage; use Subdivision for evaluation, not as a substitute for control.

## 5. Subdivision Topology

1. Establish primary silhouette with the lowest practical cage density.
2. Keep symmetry seam aligned and welded through Mirror.
3. Add support loops or creases only where edge sharpness changes.
4. Use even quad flow through broad curvature.
5. Route unavoidable poles to flatter, less visible, or lower-deformation regions.
6. Build openings after the primary surface passes unless they define the silhouette.
7. Compare cage and evaluated surface under reflective lighting.
8. Correct the cage when the evaluated surface pinches, dents, or loses volume.

Do not stack support loops tightly around every edge; it produces rigid, difficult-to-edit surfaces.

## 6. Hard-Surface Topology

- Preserve planar faces and manufactured radii.
- N-gons may be valid on static planar regions when triangulation/shading remains stable and no
  downstream deformation/subdivision depends on them.
- Triangles may terminate flow or support export, but keep them away from smooth deformation/highlight problems.
- Use Bevel, Weighted Normal, and smooth/sharp policies only on valid geometry.
- Use Boolean for volume construction and choose cleanup depth from downstream requirements.
- Separate mechanically independent parts and build actual seams/clearance instead of deep overlap.

## 7. Connections And Boundaries

### Continuous Surface

1. Expose clean boundary loops.
2. Match winding and correspondence.
3. Reconcile loop counts deliberately.
4. Bridge with enough cuts for the transition.
5. Weld boundary vertices.
6. Relax spacing while preserving silhouette.
7. Inspect positional gap, normals, curvature, edge-length change, and manifold state.

### Mechanical Seam

Keep parts independent. Model receiving surfaces, clearance, wall thickness, fastening/mounting
logic, and compatible bevel radii. Avoid z-fighting and unexplained penetration.

### Embedded Component

Create a recess/socket, contact surface, mounting depth, and visible gap policy. Do not push a box
through the host and call it installed.

### Physical Contact

Keep independent objects and use collision/constraints when motion matters. Do not weld contact points.

## 8. Retopology

Retopologize when sculpt/remesh/Boolean output must deform, subdivide, receive controlled UVs, or
meet an export budget.

- Preserve accepted silhouette and landmarks with Shrinkwrap/projection.
- Build loops around deformation and facial/joint features first.
- Define borders, openings, and material seams.
- Fill broad regions with controlled density.
- Inspect projection offset and backface errors.
- Compare high-to-low distance, normals, silhouette, and baked detail.
- Keep the high-resolution source as a protected reference.

## 9. Cleanup And Validation

Check:

- boundary and non-manifold edges according to asset intent;
- duplicate positions, zero-length edges, zero-area faces, internal faces, and loose geometry;
- connected-component count;
- normals and face orientation;
- symmetry seam position and weld;
- edge-length distribution and abrupt jumps;
- face aspect ratio and tiny faces;
- pole valence/location;
- UV and material seam compatibility;
- modifier stack and unapplied non-uniform scale;
- low cage, subdivided, wireframe, MatCap, reflective, and silhouette views.

Open cloth, sheets, and intentional shells may have boundaries. A closed liquid volume or Boolean
solid must satisfy its declared closed-volume requirement.

### Primitive-Stacking Audit

After each structural transaction, count these as topology strikes:

- a declared continuous shell spans overlapping objects or disconnected islands;
- a visible overlap has no declared seam, interface, fusion, or physical-contact route;
- Functional/Detail geometry exists while Structural/Transition forms remain open;
- smooth normals conceal a primitive intersection;
- required bevel classes have no evaluated transition geometry;
- a Boolean construction has no operand/result cleanup evidence;
- `B_OBJECT_JOIN` or Join Geometry is reported as a fused surface;
- wireframe evidence does not explain the visible structure.

One strike fails the affected part. Two distinct strikes stop later stages and roll back to
Topology Construction or Structural Forms. Do not satisfy this audit by adding meaningless cuts,
merges, or bevels; the topology must carry the intended form and manufacturing relationship.

## 10. Blender Python And BMesh Pattern

```python
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

target = [v for v in bm.verts if v.co.z > limit and v.co.x >= -tolerance]
for vert in target:
    vert.co.z += displacement(vert.co)

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld_tolerance)
bm.normal_update()
bm.to_mesh(mesh)
bm.free()
mesh.update()
```

Derive tolerances from object scale and intended seam. Save a checkpoint before destructive
operations, use geometric/topological predicates, and validate the result immediately.

## 11. Failure Diagnosis

- Shape fixed only in one view: edit silhouette/profile from orthographic and perspective views.
- Lumpy subdivision: too many uneven loops, poles in curvature, or cage shape is wrong.
- Seam ridge: boundary positions/normals/spacing do not match or duplicate vertices remain.
- Shading looks smooth but geometry is broken: normals/Weighted Normal are hiding topology defects.
- Modifier result changes after apply: evaluated stack/order or transforms were not recorded.
- Retopo loses volume: projection target/offset or too-sparse cage does not preserve landmarks.
- Topology becomes dense without better silhouette: dissolve/rebuild the region and justify loops.

## 12. Official Sources

- BMesh API: https://docs.blender.org/api/current/bmesh.html
- Extrude: https://docs.blender.org/manual/en/5.2/modeling/meshes/editing/mesh/extrude.html
- Inset: https://docs.blender.org/manual/en/5.2/modeling/meshes/editing/face/inset_faces.html
- Bridge Edge Loops: https://docs.blender.org/manual/en/5.2/modeling/meshes/editing/edge/bridge_edge_loops.html
- Subdivision Surface: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/subdivision_surface.html
- Retopology: https://docs.blender.org/manual/en/5.2/modeling/meshes/retopology.html
