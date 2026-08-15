# Material Production Workflow

## Contents

1. Evidence and scale
2. Coordinate routing
3. PBR channel construction
4. Layer and mask logic
5. Detail scale routing
6. Review lighting
7. Failure diagnosis
8. Official sources

## 1. Evidence And Scale

Record the following before node construction:

- material class and manufacturing state;
- object dimensions in meters;
- smallest visible feature at final camera distance;
- directionality and repetition interval;
- whether the surface is continuous across parts or intentionally changes per part;
- reference evidence for wear, wetness, dirt, corrosion, pores, grain, or coating.

Estimate a physical repeat size in meters. Store it as a material custom property such as
`production_texture_scale_m`. Do not tune mapping until the pattern merely "looks busy".

## 2. Coordinate Routing

### UV

Use for hero assets, image PBR sets, directional surfaces, wood boards, brushed sheets, decals,
and anything requiring seam control. Apply scale before unwrapping when object scale affects
texel density. Keep neighboring faces continuous only when the real material is continuous.

### Object Or Generated

Use for procedural blockout, non-directional background material, and quickly changing geometry.
Generated coordinates normalize to object bounds, so identical materials on differently sized
objects can change apparent scale. Correct this with object dimensions or a shared coordinate
object when physical scale matters.

### Triplanar

Use for irregular stone, soil, concrete, or background assets where UV seams are more damaging
than projection blending. Do not use it for end grain, brushed direction, labels, planks, or
anisotropic surfaces.

### Tangent

Provide a stable tangent for anisotropy. The direction must follow brushing, rolling, machining,
wood fiber, or weave. A strong anisotropy value with a wrong tangent is less realistic than an
isotropic material.

## 3. PBR Channel Construction

Build channels independently:

- Base Color: substrate color and broad pigment variation. Do not bake lighting or cavity shadow into it.
- Metallic: conductive substrate mask. Bare metal is near the metallic end; paint, rust, dirt,
  wood, water, and oxide layers are dielectric.
- Roughness: microfacet width. Use measured/reference-driven ranges and spatial variation rather
  than one constant or an inverted color map by habit.
- Normal: tangent-space directional microstructure from a normal map through a Normal Map node.
- Bump: scalar procedural or height microdetail through a Bump node.
- Displacement: true medium/large relief that changes shadow or silhouette, with adequate mesh
  subdivision and a calibrated midlevel.
- Coat: clear varnish, lacquer, clear paint, or thin polished top layer when physically present.
- Transmission and IOR: glass and liquid behavior, not a substitute for alpha transparency.
- Volume: absorption/scattering for non-zero-thickness glass, liquid, fog, or translucent volume.

Avoid double application: do not feed the same normal information into both Normal Map and Bump
at full strength, and do not combine true displacement with an uncalibrated duplicate bump.

## 4. Layer And Mask Logic

Build the clean substrate first, then add layers in physical order. Useful causes include:

- upward-facing surfaces collect dust or standing water;
- cavities retain dirt and moisture;
- exposed edges lose paint but do not automatically rust everywhere;
- surfaces near ground or waterlines receive splash, mud, algae, or tide marks;
- hand contact can polish roughness and remove dust;
- drainage direction stretches stains vertically;
- separate boards have separate moisture, grain, and damage histories.

Combine geometry attributes, position, normal direction, ambient/cavity approximations, painted
masks, and low-frequency noise. Noise should break regularity, not invent the whole causal model.

## 5. Detail Scale Routing

Classify each feature:

- silhouette scale: model or displace with adequate tessellation;
- shadow scale: geometry, true displacement, or strong bump depending distance;
- highlight scale: normal or bump;
- color-only scale: Base Color or masks.

At final camera distance, disable each layer in turn. Remove a layer if it contributes no visible
evidence, or move it to a cheaper representation.

## 6. Review Lighting

Use three repeatable reviews:

1. Neutral diffuse environment to inspect Base Color and value range.
2. Long area light moving through grazing angles to inspect roughness, anisotropy, normal scale,
   dents, and coating continuity.
3. Production lighting to verify that the material identity survives the final shot.

Use a neutral gray neighboring object to distinguish material response from exposure or grade.
Do not approve roughness from a front-lit still image alone.

## 7. Failure Diagnosis

- Plastic-looking metal: metallic branch missing, roughness too uniform, environment lacks usable
  reflections, bevels/normals are poor, or paint and metal layers are confused.
- Flat wood: no directional grain hierarchy, wrong UV direction, no end grain, uniform roughness,
  or board geometry is too perfect.
- Miniature appearance: texture repeat, scratches, pores, droplets, or edge damage are too large.
- Material swims: Generated/Object coordinates evaluated in an unsuitable space or unapplied
  animation/deformation changes mapping.
- Muddy normals: wrong image color space, DirectX/OpenGL Y mismatch, duplicate bump, or excessive strength.
- Wet means black: color was darkened without narrowing roughness, adding reflection continuity,
  or respecting pooling/contact causes.
- Procedural camouflage: one noise pattern drives every channel with the same scale and phase.

## 8. Official Sources

- Principled BSDF: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html
- Texture Coordinates: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/texture_coordinate.html
- Mapping: https://docs.blender.org/manual/en/5.2/render/shader_nodes/vector/mapping.html
- Normal Map: https://docs.blender.org/manual/en/5.2/render/shader_nodes/vector/normal_map.html
- Bump: https://docs.blender.org/manual/en/5.2/render/shader_nodes/vector/bump.html
- Displacement: https://docs.blender.org/manual/en/5.2/render/shader_nodes/vector/displacement.html
