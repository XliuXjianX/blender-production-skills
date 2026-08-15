# Cycles Four-Direction Shader Raycast Outline

## Source Reconstruction

The local tutorial video demonstrated this method at about four minutes. The production
version reconstructs the graph without depending on the video at runtime.

For one offset:

```text
Offset Vector
  -> Vector Transform (Camera to World, Vector)
  -> Vector Math Scale (Width)

Geometry Position + transformed offset
  -> Shader Raycast Position

Geometry Incoming * -1
  -> Shader Raycast Direction

Ray Length
  -> Shader Raycast Length

Shader Raycast Is Hit
  -> sample mask
```

Instantiate the sample four times with:

```text
(+1,  0, 0)
(-1,  0, 0)
( 0, +1, 0)
( 0, -1, 0)
```

Multiply the four `Is Hit` outputs:

```text
mask = hit_pos_x * hit_neg_x * hit_pos_y * hit_neg_y
```

Use `mask = 0` for outline and `mask = 1` for the base shader.

## Why It Works

At an interior surface point, small camera-plane shifts still originate over geometry, so
all four rays toward the camera hit the object. Near a silhouette, at least one shifted
origin falls outside the projected object and its ray misses. The multiplied mask therefore
isolates a screen-oriented border.

## Production Defaults

- Blender: 5.2 or newer.
- Engine: Cycles.
- Direction: `Incoming * -1`.
- Ray length: bounded, default `100`.
- Ray scope: `only_local = true` by default.
- Width: small camera-plane world offset, default chosen from asset scale.
- Base shader: Cycles Toon BSDF or another Cycles-compatible shader.
- Outline shader: dark Emission or another deliberately unlit shader.

## Local And Scene-Aware Modes

`only_local = true` tests the current object's geometry and prevents neighboring objects
from changing its outline. This is the safest default for character or prop outlines.

`only_local = false` may be useful for intentional scene interaction, but nearby objects,
overlaps, and concavities can create false hits. Treat it as a separate artistic mode and
validate it explicitly.

## Limitations

- Four ray queries are evaluated per shaded point.
- Width is not a literal pixel width and changes with projection and distance.
- Thin geometry, holes, concavity, displacement, transparency, and overlapping objects can
  change the mask.
- This is an object/material silhouette method, not a general crease or intersection-line
  extractor.
- Shader Raycast is version-sensitive and must be detected from Blender RNA.

## Validation

1. Confirm `ShaderNodeRaycast` exists and Cycles is active.
2. Inspect all four offset vectors and three multiply nodes.
3. Test front, profile, and three-quarter views.
4. Test nearest and farthest shot distances.
5. Place a neighboring object close to the subject and confirm local-only behavior.
6. Test one concave object and one thin feature.
7. Render a short animated range and inspect line flicker.
8. Record render-time cost relative to the same material without raycasts.

## Fallbacks

- Eevee real-time character outline: inverted-hull Geometry Nodes.
- Camera-aware creases/intersections: Grease Pencil Line Art or Freestyle.
- Screen-space post effect: compositor edge detection.
- Older Cycles version: Toon BSDF plus one of the geometry or camera-line methods.

## Official Blender Sources

- https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/raycast.html
- https://docs.blender.org/api/current/bpy.types.ShaderNodeRaycast.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/converter/vector_transform.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/toon.html
