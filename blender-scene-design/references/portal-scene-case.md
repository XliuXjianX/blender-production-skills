# Layered Portal Scene Case

This is a design case, not a portal-specific routing rule.

The executable native-component example is
`../../blender-procedural-systems/scripts/blender_forced_perspective_portal_case.py`. Load it only
when the task needs this case; the design layer itself does not execute geometry.

## Transferable Decisions

- Establish a hero focus, supporting repetitions, foreground/midground/background layers, leading
  lines, and intentional negative space before adding detail.
- Treat terrain, water, vegetation, architecture, repeated assets, light, and camera as one scene
  system with explicit interfaces.
- Allocate real geometry to near silhouettes, tunnel depth, step contact, river banks, cast shadows,
  and moving-camera parallax.
- Use Collection Instances for distant repeated portals and Geometry Nodes instances for broad
  vegetation fields; keep preview helpers outside instanced collections.
- Keep river bed and water surface separate. Use the bed for depth/contact and the water material
  for optical response.
- Use semantic parameter groups for portal dimensions, stair flight, tunnel depth, repetition,
  terrain, water, vegetation, and review quality.

## Native Construction Example

- Portal opening: one host frame or wall plus a through-thickness Boolean cutter.
- Straight stair flight: one formal tread/riser source plus one Array Modifier whose constant
  offset carries local run and rise; optional Object Offset may add non-destructive forced-perspective taper.
- Rail or stream guide: a Bezier/NURBS path with stable direction and local frame.
- Distant portals: Collection Instances of a generator-owned production collection.
- Grass: source clumps instanced by Geometry Nodes with terrain, water, portal, and camera masks.

Python may create and configure these controls. It must not loop over step count to bake separate
step boxes, duplicate each distant portal, or emit each grass blade as an object.

## Ownership And Review

- A generator modifies only collections and data blocks carrying its ownership identifier.
- A same-name unowned collection or material is a hard conflict, not permission to clear it.
- Preview lights and diagnostic materials live outside production instance collections.
- A rerun preserves unrelated objects, selection, active object, mode, camera, World, and render settings.
- Repair a failed local system from its semantic controls instead of restarting scene analysis.
