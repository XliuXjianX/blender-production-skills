# Eevee Toon Fill And Inverted-Hull Outline

## Effect Decomposition

Treat these as separate layers:

1. Toon fill: discrete light bands in the material.
2. Object outline: a reversed expanded shell that follows evaluated geometry.
3. Scene lines: camera-aware creases, intersections, material borders, and hidden lines.

This skill owns the first two layers. Grease Pencil Line Art or Freestyle should own the
third layer.

## Toon Fill Graph

Recommended Eevee graph:

```text
Diffuse BSDF
  -> Shader to RGB
  -> Constant Color Ramp
  -> optional stable material variation
  -> Emission
  -> Material Output
```

Use a white Diffuse BSDF when the Color Ramp itself defines the palette. A colored Diffuse
BSDF is also valid, but its luminance and hue then influence ramp lookup. Keep ramp
interpolation `CONSTANT` for graphic bands.

For subtle texture variation:

```text
Generated/Object coordinates -> Noise Texture -> restrained Color Ramp
toon palette * variation -> Emission
```

Avoid high-frequency animated noise that crawls between frames.

## Outline Geometry Nodes

Production graph:

```text
Source Geometry
  -> Extrude Mesh (Faces, Offset Scale = Width)
  -> Separate Geometry (Face domain, Selection = Extrude Top)
  -> Set Position (optional normal-projected wobble)
  -> Flip Faces
  -> Set Material (Outline)
  -> Join Geometry with untouched source
  -> Geometry Switch (Enable)
  -> Output
```

Separating `Top` removes the original and side faces from the extruded branch. This avoids
duplicated surfaces and makes the shell easier to reason about.

Correct irregularity:

```text
Position -> Noise Texture
Noise Factor -> map 0..1 to -1..1
centered noise * Wobble Amount -> Normal scale
Normal * scalar -> Set Position Offset
```

The source asset supplied by the user contained an unconnected noise-vector input. That
samples one constant position and cannot create spatial line wobble. The production graph
must connect Position explicitly.

## Width Policy

Inverted-hull width is object/world space, not pixels. Choose an initial width from the
object's bounding-box diagonal, then test:

- nearest expected camera;
- farthest expected camera;
- front, profile, and three-quarter views;
- one extreme deformation pose.

Use masks for eyes, mouths, fingers, hair gaps, layered clothes, and other collision-prone
regions.

## Material Visibility

The outline material should be dark or unlit and use Eevee backface culling. Flipped
far-side faces remain visible around the silhouette while most front-facing shell surfaces
are culled from the exterior view.

## Failure Signs

- Outline disappears: wrong face orientation, culling, material assignment, or width sign.
- Entire shell is visible: culling disabled or faces not flipped.
- Z-fighting: original faces from the extruded branch were not isolated.
- Uniform offset noise: Noise Texture lacks Position or another spatial coordinate.
- Facial halos and black gaps: shell intersects nearby surfaces; add masks or reduce width.
- Line width changes too much with distance: object-space method is unsuitable for the
  shot; use camera-aware line extraction or compositing.

## Official Blender Sources

- https://docs.blender.org/manual/en/5.2/render/shader_nodes/color/shader_to_rgb.html
- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/extrude_mesh.html
- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/flip_faces.html
- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/geometry/operations/set_material.html
- https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/geometry/write/set_position.html
- https://docs.blender.org/manual/en/5.2/render/eevee/material_settings.html
