# Deformation Method Notes

## Simple Deform

- Verify local axis and origin.
- Add segments along the deformation axis.
- Use limits and an origin object for controlled partial bends.
- Test full angle, including a 360-degree ring when requested.
- Check cross-section rotation and end alignment.

## Curve

- Align the mesh deform axis with the curve direction.
- Apply scale or account for it deliberately.
- Keep curve resolution separate from render bevel resolution.
- Use Tilt and Radius only when they are part of the design.
- Inspect path start, direction, offset, and section twist.
- For railings, pipes, tracks, and cables, name start/end anchors and record the declared up axis.
- Generate a continuous profile with curve bevel or Curve-to-Mesh; use Curve Modifier only when a
  source mesh must deform.
- Stabilize the frame when a tangent approaches the up axis. Diagnose tilt and point-order flips
  before editing generated geometry.
- Derive repeated supports by arc length from the accepted path and project them to real support
  surfaces. Do not hand-place posts to hide a bad path.
- Distinguish generated curve geometry from Curve Modifier deformation. Use bevel depth or a bevel
  object when the path owns a constant rail/pipe/cable/trim profile; use Curve Modifier only when
  an existing mesh source must deform along the path.

## Lattice

- Enclose the affected region with enough control points for the desired frequency.
- Limit influence with a semantic vertex group.
- Use one lattice for coordinated multi-object changes when appropriate.
- Check preserved boundaries and UV stability.

## Mesh/Surface Deform

- Validate the cage or source surface before binding.
- Keep a pre-bind checkpoint.
- Test the complete animation range after binding.
- Rebind after topology changes; never assume a stale bind is valid.

## Shrinkwrap

- Choose projection, nearest surface, or target-normal behavior from the topology.
- Define positive/negative direction and offset.
- Detect backface projection and thin-shell ambiguity.
- Do not use zero offset where z-fighting is possible.
- Use viewport/object snapping instead when the relationship is a one-time exact placement. Use
  Shrinkwrap when later target edits must continue to drive the receiver or when many vertices
  must remain conformal.

## Armature, Constraints, Drivers

- Define rest pose, hierarchy, pivot axes, degrees of freedom, and limits first.
- Separate deforming weights from rigid mechanical parenting.
- Avoid cyclic driver/constraint dependencies.
- Test extreme poses, interpolation, and neighboring clearances.
- Use shape keys for corrective or art-directed states, not as a substitute for an obvious native modifier.
