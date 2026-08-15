---
name: blender-npr-eevee
description: Build and validate Eevee 3D-to-2D rendering with discrete Shader to RGB lighting bands and a deformation-following inverted-hull Geometry Nodes outline. Use for anime, cel-shaded, toon, hand-drawn, or stylized real-time assets that need editable object-space outlines in Blender Eevee.
---

# Blender NPR Eevee

Build toon fill and object outline as two independent layers. Use this skill only after
`blender-production-router` confirms that Eevee is the intended render engine.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns Eevee NPR nodes and outline evidence only;
stylization cannot replace construction or restart analysis.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md`. Eevee toon fill remains
a Shader Node workflow and the inverted hull remains a justified Geometry Nodes workflow because it
must follow evaluated deformation. A requested Blueish stylized or compositor candidate is
read-only input from `blender-local-asset-library`; this Skill verifies Eevee compatibility,
exposed controls, and output evidence before integration. It does not route physical PBR materials
or change the production state.

Require passed formal topology, Structural Forms, Transition Forms, connection, silhouette, and
real-bevel gates first. An inverted hull may stylize an accepted model; it may not hide primitive
stacking, disconnected islands, faceted curves, missing interfaces, or false bevels.

## Engine Gate

- Require Eevee for `Shader to RGB`.
- Do not copy this shader graph into Cycles.
- Route Cycles raycast outlines to `blender-npr-cycles`.
- Route camera-aware creases, intersections, hidden lines, or scene-wide line extraction
  to Grease Pencil Line Art or Freestyle through `blender-procedural-systems`.

## Production Method

1. Inspect selected mesh objects, their scale, modifiers, materials, deformation, and
   camera-distance range.
2. Preserve the current World, cameras, collections, and unrelated materials.
3. Build toon fill as:
   `Diffuse BSDF -> Shader to RGB -> Constant Color Ramp -> stable material variation`.
4. Build the outline as a Geometry Nodes modifier:
   - extrude faces along evaluated normals;
   - isolate the extruded top faces;
   - apply optional position-driven normal wobble;
   - flip faces;
   - assign a dedicated dark outline material;
   - join the outline shell with the untouched source geometry.
5. Enable Eevee backface culling on the outline material.
6. Expose enable, width, noise scale, wobble amount, and outline material.
7. Keep the result non-destructive and follow the object's evaluated deformation.

Use `scripts/build_eevee_npr.py` to create an idempotent production node setup on selected
mesh objects. Existing materials are preserved unless material replacement is explicitly
approved.

## Hard Rules

- Do not reset the scene or World.
- Do not replace an existing user material without explicit approval.
- Do not use an unconnected Noise Texture as line wobble. Drive noise with `Position`,
  center it around zero, and project it along `Normal`.
- Do not keep the original faces from the extruded outline branch; isolate the extruded
  top shell to avoid duplicate surfaces and z-fighting.
- Do not use a single unchecked world-unit width for every asset. Derive a starting width
  from object scale and test near and far camera distances.
- Do not call the outline complete while it intersects thin gaps, eyes, mouths, fingers,
  clothing layers, or nearby geometry.
- Do not use Geometry Nodes to create the toon lighting bands; those belong in Shader
  Nodes.
- Disable the outline and verify the clay model plus wireframe still passes before accepting NPR.

## Validation Gate

Check all of the following before reporting completion:

- Eevee is active and `ShaderNodeShaderToRGB` exists.
- The color ramp uses discrete bands and remains stable as the light rotates.
- The outline graph contains Extrude Mesh, top-face isolation, Set Position, Flip Faces,
  Set Material, Join Geometry, and a Geometry Switch.
- Position drives the noise vector and Normal drives the displacement direction.
- The outline material uses backface culling.
- Front, profile, and three-quarter renders show a continuous silhouette.
- Near/far camera and one extreme deformation pose do not produce unacceptable width
  changes, shell collisions, or flicker.
- Unique review-image paths are used to avoid stale preview caching.

Read `references/eevee-npr-workflow.md` for graph details, limitations, and official
Blender documentation.
