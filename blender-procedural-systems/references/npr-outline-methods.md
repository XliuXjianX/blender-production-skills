# NPR Toon And Outline Routing

Treat toon fill, object silhouette, and scene line extraction as separate effects.

## Three Independent Layers

1. Toon fill: quantized lighting and palette mapping in Shader Nodes.
2. Object outline: an expanded reversed shell around a deforming mesh.
3. Scene line art: camera-aware contours, creases, intersections, material boundaries, and hidden lines.

Do not call all three effects "Geometry Nodes."

## Inverted-Hull Geometry Nodes

Use for a character or prop that needs a stable anime silhouette following its deformation.

Recommended graph:

1. Read source geometry.
2. Create a duplicate outline branch.
3. Expand the branch along evaluated normals by a scale-aware width.
4. Flip outline faces.
5. assign a dedicated unlit or dark outline material.
6. apply an engine-correct face visibility policy.
7. join source and outline branches.
8. expose outline enabled, width, material, masks, and controlled irregularity.

For hand-drawn irregularity, drive noise with `Position` or another deliberate coordinate. Center the noise around zero and project it onto `Normal` before multiplying by a small amplitude. An unconnected Noise Texture vector produces a constant sample and does not create spatially varying line wobble.

Avoid a raw world-unit width. Derive a practical default from object scale and test at near and far camera distances. Use vertex groups or material masks to suppress outlines around eyes, mouths, thin gaps, and regions prone to shell collision.

## Grease Pencil Line Art And Freestyle

Use when the requested lines depend on the active camera or scene relationships:

- visible and hidden contours;
- crease-angle lines;
- object intersections;
- material boundaries;
- selected collections or objects;
- technical illustration or art-directed strokes.

Validate chain stability over animation, occlusion categories, crease density, stroke depth offset, and output resolution.

## Toon Fill

For Eevee, `Shader to RGB` followed by a constant Color Ramp can turn continuous lighting into discrete bands. Add material noise only at a scale that remains stable in animation.

`Shader to RGB` is an Eevee-specific route. For Cycles, choose a Cycles-compatible Toon BSDF, explicit light-vector construction, texture-driven palette, or compositor approach instead of copying the Eevee graph unchanged.

## Cycles Shader Raycast Outline

Blender 5.2 adds a Shader Raycast node that can derive a Cycles silhouette mask. Offset
the shading position in camera-space `+X`, `-X`, `+Y`, and `-Y`, transform those offsets
to world space, cast each shifted point back toward the camera with `Incoming * -1`, and
multiply the four `Is Hit` values. Route this method to `blender-npr-cycles`.

Keep `only_local` enabled by default so neighboring objects do not contaminate the
silhouette. This costs four extra shader-ray queries per shading point and still needs
near/far camera validation because its width is not literal pixels.

## Hybrid Delivery

A production NPR asset often combines:

- toon fill material;
- inverted-hull silhouette for important characters;
- Line Art or Freestyle for selected crease/intersection strokes;
- compositor treatment for final line weight and color.

Record each layer separately in `task_route.json` so engine limits and validation remain visible.

## Validation

- Render front, side, and three-quarter views.
- Render near and far camera distances.
- Test one extreme deformation pose.
- Inspect face culling and material assignment.
- Check shell intersections around narrow gaps.
- Check line flicker over a short animation.
- Confirm toon bands remain stable when lights rotate.
- Confirm the chosen method matches the render engine.

Official references:

- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/extrude_mesh.html
- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/flip_faces.html
- https://docs.blender.org/manual/en/5.2/grease_pencil/modifiers/generate/line_art.html
- https://docs.blender.org/manual/en/5.2/render/freestyle/introduction.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/color/shader_to_rgb.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/toon.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/raycast.html
