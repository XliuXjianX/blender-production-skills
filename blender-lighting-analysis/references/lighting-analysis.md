# Lighting Analysis And Construction

## Reference Measurements

Record the receiving plane, contact point, shadow endpoint, object-height estimate, shadow length,
shadow direction, penumbra width, lit-face direction, backlit-face luminance, visible sources, and
confidence. When the ground is approximately level:

```text
sun_elevation ≈ atan(object_height / shadow_length)
```

Treat this as a hypothesis, not exact photogrammetry. Perspective, sloped receivers, multiple
sources, and soft contact shadows can invalidate a direct measurement.

## Construction Sequence

1. Use gray materials and disable decorative lighting.
2. Set one Sun from the measured shadow direction and elevation.
3. Set Sun angle from penumbra evidence.
4. Use a dark neutral World, then raise it only enough to match unlit-face visibility.
5. Match exposure without clipping practical sources or crushing required shadow detail.
6. Compare a unique shadow-direction render and grayscale render.
7. Add bounce from a documented wall, floor, window, sky opening, or practical source.
8. Add visible practical lights and emissive geometry with real receivers and falloff.
9. Add atmosphere only after source direction and geometry are accepted.

## Responsibility Examples

```text
Light_Sun_Key
source: exterior sun
role: primary direction and cast shadow
evidence: shadow extends toward frame lower right
loss_if_removed: primary shadow and lit/backlit separation disappear

Light_Sky_Fill
source: open sky / World
role: retain detail on faces not reached by Sun
evidence: reference shadow region remains above black
loss_if_removed: dark faces lose required detail
```

## Failure Signs

- several lights produce competing shadows;
- a rim light outlines every object without a source;
- an HDRI changes reflection but contradicts cast-shadow direction;
- exposure, material roughness, or compositing is used to imitate missing light transport;
- fog hides incorrect source direction;
- production lighting begins while Blockout or topology remains structurally invalid.

