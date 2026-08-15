# Wood And Plank Material Workflow

## 1. Separate Wood Geometry From Wood Shading

Geometry must carry:

- individual board length, width, thickness, bow, twist, cupping, overlap, missing pieces;
- broken silhouettes, splinters, deep checks, gaps, nail holes, exposed support beams;
- large rot cavities and compressed or eroded edges visible in shadow.

The shader must carry:

- growth-ring and fiber color structure;
- pores and fine cracks;
- roughness variation;
- small height, dirt, discoloration, wetness, moss, and fungal staining.

Do not solve a perfectly regular bridge or floor with a stronger wood texture.

## 2. UV And Grain Orientation

For every hero board:

1. Apply or account for object scale.
2. Mark seams so long grain follows the board length.
3. Give top, side, and end faces intentional mapping.
4. Provide end-grain material or UV regions on cut ends.
5. Keep real-world grain scale consistent across boards.
6. Offset or choose texture regions per board without changing physical scale arbitrarily.
7. Check UV stretching numerically and with a direction test texture.

Avoid shared Generated/Box projection when it rotates fibers across adjacent faces or makes every
board repeat the same knot and crack.

## 3. Build The Clean Wood Hierarchy

Use at least three scales when visible:

- macro: heartwood/sapwood or board-wide value drift and knots;
- meso: longitudinal grain and growth-ring direction;
- micro: pores, fibers, saw marks, and fine roughness.

Drive Base Color, roughness, and bump with related but non-identical signals. Grain may influence
all three, but each channel needs its own range and secondary variation.

Use anisotropy or directional normal detail only when the finish/reference produces directional
highlights. Raw rough wood usually reads more through broad roughness, fibers, pores, and broken
geometry than through a strong polished anisotropic highlight.

## 4. Board Variation

Vary per board:

- source texture offset or UDIM region;
- subtle hue/value and roughness;
- wetness amount and drying edges;
- damage, nails, cracks, moss, and dirt masks;
- geometry bow, thickness, end damage, and local sag.

Keep species, processing scale, and environment coherent. Random rotation by 90 degrees is not
acceptable when it turns grain across the board width.

## 5. Aged, Rotten, And Wet Wood

### Aged

- desaturate and lighten exposed dry fibers according to reference;
- increase fiber breakup, checking, and roughness;
- retain protected or recently exposed darker material in cavities and broken faces.

### Rotten

- remove or collapse volume at large scale;
- soften and fragment edges;
- add porous dark material, fungal staining, and inconsistent density;
- keep rot concentrated where water, soil contact, or poor drainage explains it.

### Wet

- darken substrate moderately because of absorption;
- narrow roughness and strengthen continuous grazing reflections;
- add a separate thin water-film or puddle layer where water accumulates;
- keep raised fibers and dry islands from becoming uniformly glossy;
- use actual puddle geometry for visible water depth or reflected silhouettes.

Do not represent wetness by multiplying Base Color toward black across the whole board.

## 6. Moss, Mud, And Fasteners

- Moss grows in persistent moisture, shade, cavities, and low-traffic areas.
- Mud splashes follow height and direction; sediment gathers in recesses.
- Nail heads are separate metal material with contact staining, rust transfer, and recess geometry.
- Avoid using moss to cover UV errors, identical geometry, or missing board damage.

## 7. Distance-Based Detail

- Foreground: true displacement/geometry for splinters, deep cracks, lifted fibers, and puddles.
- Midground: restrained displacement plus normal/bump.
- Background: normal, roughness, and color only unless silhouette damage is visible.

## 8. Validation

Require:

- correct grain direction on top, side, and end faces;
- no conspicuous repeated knots/cracks in the hero region;
- board-to-board variation without species/scale drift;
- wet highlights follow pooling and surface slope;
- end grain exists on broken/cut ends;
- geometry supplies major damage and shader supplies microstructure;
- diffuse, grazing-reflection, and final-light reviews at final camera distance.

Official coordinate and displacement basis:

- https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/texture_coordinate.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/vector/displacement.html
