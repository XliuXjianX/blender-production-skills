# Modeling Workflows

## 0. Blockout To Formal Topology

For every proxy, choose exactly one outcome:

- `replace`: preserve its accepted bounds as reference and rebuild the formal mesh;
- `convert`: continue editing it through connected topology or an intentional modifier stack;
- `legitimate_independent_primitive`: retain it only when the manufactured part is genuinely a
  separate regular solid and record the interface to its neighbors.

Archive or remove replaced task-owned proxies. Record the final object, construction operations,
connected-component target, assembly interfaces, and bevel policy. Do not advance while one
continuous shell is still represented by several overlapping proxies.

Build in this order:

1. Primary silhouette and major negative space.
2. Structural cuts, frames, cavities, slopes, supports, and portals.
3. Transition surfaces, radii, blends, shell turns, seams, and mating interfaces.
4. Functional parts.
5. Surface detail.

The absence of stages 2 or 3 is a modeling failure, even when stages 1 and 5 look recognizable.

## 1. Subdivision Product Surface

1. Start from a low-density half cage and add Mirror.
2. Establish longitudinal and transverse loops only where they control silhouette or curvature.
3. Shape major profiles from orthographic and perspective views.
4. Add openings and seams after the primary surface is stable.
5. Place poles away from high-curvature highlight paths.
6. Inspect the unsubdivided cage, subdivided result, wireframe, and reflective material.
7. Correct the cage instead of adding subdivision levels to hide dents.

## 2. Hard-Surface Boolean Construction

1. Define target, cutter, operation, and whether the cut occurs before or after thickness/deformation.
2. Apply or account for non-uniform scale.
3. Keep cutters semantic and reusable.
4. Use exact Boolean where appropriate.
5. Inspect evaluated geometry for internal faces, slivers, coplanar ambiguity, and shading.
6. Use bevel weights, angle, vertex groups, or direct topology according to edge intent.
7. Apply and reconstruct only when downstream edits require real topology.

## 3. Continuous Loop Connection

1. Confirm the parts should be one continuous surface.
2. Expose and clean both boundary loops.
3. Match loop direction and resolve incompatible counts by deliberate subdivision or dissolve.
4. Bridge loops and weld the seam.
5. Relax spacing while preserving the intended silhouette.
6. Inspect gap, adjacent normals, edge-length change, and curvature flow.
7. Retopologize the transition if bridging alone produces a poor highlight path.

## 4. Organic Volume Fusion

1. Preserve source volumes.
2. Choose Boolean Union for controlled hard boundaries or Voxel Remesh for organic fusion.
3. Set voxel size from the smallest important primary feature.
4. Smooth only the transition; preserve landmarks and silhouette.
5. Add Multiresolution or sculpt detail after the primary volume passes.
6. Retopologize for deformation, UV, or controlled subdivision.

## 5. Mechanical Assembly

Do not fuse parts that manufacture, rotate, slide, fasten, or replace independently.

For each interface define:

- mating surfaces;
- clearance;
- fastener or mount;
- bevel/radius class;
- collision or constraint role;
- whether the seam is visible at the target distance.

## 6. Tubular Elbows And Rolled Profiles

Use one of these routes according to editability and reference evidence:

1. **Spin**: start from a circular or shaped boundary loop, place the transform center at the
   bend center, spin through the required angle with enough steps, and continue extrusion from
   the resulting loop.
2. **Bridge**: build two compatible loops, orient them to the incoming and outgoing directions,
   Bridge Edge Loops with multiple cuts, shape the intermediate rings around the bend center,
   relax spacing, and weld the boundaries.
3. **Curve profile**: use a Bezier or NURBS path with an explicit bevel profile and separate path
   and bevel resolution. Convert only when downstream topology requires it.

For every route, validate one connected component, shared transition vertices, preserved
cross-section, bend radius, end alignment, normal continuity, and final-resolution faceting.
Rotating straight cylinders into each other is never an accepted elbow.

## 7. Smooth Shading And Edge Language

- Mark visible curved faces smooth.
- Keep caps and designed creases sharp by angle or explicit edge marking.
- Use Weighted Normal only when it improves the intended manufactured highlight and does not
  hide invalid topology.
- Record radial segments, bend steps, subdivision level, smoothing angle, and final-resolution
  silhouette evidence.
- Reject a curved surface when a neutral reflective material reveals stepping, pinching, or
  highlight discontinuity.

## Selection And Region Policy

Prefer named vertex groups, custom attributes, connected components, boundary status, local coordinate ranges, normal direction, and topology neighborhoods. Raw element indices may be used only inside a single deterministic operation where topology cannot change before consumption.
