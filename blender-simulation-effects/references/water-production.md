# Water And Liquid Production Workflow

## Contents

1. Route the water problem
2. Static contained water
3. Ocean and large water bodies
4. Local waves and surface interaction
5. Mantaflow liquid simulation
6. Meshing, particles, foam, spray, and wet maps
7. Material ownership
8. Cache and iteration
9. Troubleshooting
10. Validation gate
11. Official sources

## 1. Route The Water Problem

Choose from visible causes:

- static contained water or puddle: closed volume plus physical liquid material;
- deep open water with wind spectrum: Ocean modifier;
- regular local ripple: Wave modifier;
- contact-driven surface ripple/wet map: Dynamic Paint;
- pouring, filling, splashing, draining, floating interaction, or changing liquid volume: Fluid liquid simulation;
- only microscopic water texture: shader normal/roughness;
- mist, spray, or suspended droplets: particles, Geometry Nodes points, or volume layered with the main route.

Do not run a liquid domain because the request contains the word "water". Simulate only when
time-dependent volume motion changes the visible result.

## 2. Static Contained Water

1. Confirm the reference actually contains liquid rather than a dark, wet, or reflective interior.
2. Build a closed non-zero-volume mesh conforming to the interior.
3. Keep the waterline below the rim and avoid coplanar overlap with the floor/walls.
4. Decide whether meniscus/contact curvature is visible at the shot scale.
5. Separate large surface shape from small normal waves.
6. Use a physically plausible liquid shader and volume absorption when thickness affects color.
7. Add a thin wetness mask to the container only when splash/contact evidence supports it.

No fluid cache is required when the shape is static.

## 3. Ocean And Large Water Bodies

Use Ocean for deep-water spectral waves, not for a glass of water or small pool interaction.

- Set spatial size, wave scale, smallest wave, wind velocity/direction, choppiness, depth, time,
  repeat, and foam from scene scale and shot evidence.
- Generate enough surface to cover camera/reflection rays without obvious tiling.
- Use Ocean geometry/displacement for macro and mid-scale waves.
- Use material normal detail for smaller waves.
- Route foam data to a separate foam material response.
- Validate horizon silhouette, wave period, crest scale, and camera speed.
- Add Fluid or Dynamic Paint only for local interaction that Ocean cannot represent.

## 4. Local Waves And Surface Interaction

### Wave Modifier

Use for controlled rings or directional propagation on a sufficiently subdivided surface. Set
origin, direction, speed, height, width, damping, texture modulation, and vertex group from the
cause. Avoid a perfectly periodic pattern for natural water unless the reference is stylized.

### Dynamic Paint

Use a water surface as Canvas and contact objects as Brushes when local contact must create waves,
wet maps, or proximity effects. Choose canvas resolution from visible world-space detail, cache the
result, and verify the output attribute/texture exists in render.

### Shader Waves

Use only for microstructure and distant water. Shader displacement/normal cannot create real
collision, fluid volume, foam particles, or silhouette-correct splashes.

## 5. Mantaflow Liquid Simulation

### Participants

- Domain: contains the entire moving effect for every frame.
- Flow: Geometry, Inflow, or Outflow according to emission behavior.
- Effector: obstacle with suitable surface thickness and animation.
- Guide: optional directed velocity field when justified.

### Setup Order

1. Confirm scene scale, gravity, frame rate, and intended duration.
2. Build the smallest domain that safely contains all liquid and spray through the full range.
3. Apply/account for transforms on domain, flows, and effectors.
4. Ensure flow and effector surfaces are closed or intentionally thick enough for the voxel size.
5. Select liquid domain type and a project-specific cache directory.
6. Start with low resolution and no mesh/secondary particles.
7. Test timing, volume, inflow velocity, gravity, outflow, and effector leakage.
8. Raise domain resolution only after motion and containment pass.
9. Bake data, then mesh, then secondary particles/foam in controlled stages.

### Resolution And Scale

Cell size derives from domain dimensions divided by resolution. The smallest opening, collider
thickness, liquid stream, and desired splash must occupy multiple cells. If not, change the domain,
geometry, or resolution; do not expect the solver to preserve sub-cell features.

Keep the domain tight, but include future splash height and lateral motion. Oversized domains waste
memory and erase detail at a fixed resolution.

### Flow Behavior

- Geometry: initial liquid volume or one-time source.
- Inflow: continuously emits while enabled; animate use/velocity when needed.
- Outflow: removes fluid for drains or open boundaries.
- Initial velocity must match the source motion; a moving emitter without inherited velocity can look wrong.

### Viscosity, Surface Tension, And Diffusion

Use water-like defaults only for water. Honey, oil, syrup, mud, and molten material require
different viscosity/surface behavior. Tune motion at low resolution first, then verify that the
final resolution does not change the perceived material.

## 6. Meshing, Particles, Foam, Spray, And Wet Maps

### Liquid Mesh

- Enable mesh only after base particles/volume move correctly.
- Tune particle radius/mesh smoothing to preserve volume without blobby inflation.
- Inspect thin sheets, droplets, contact gaps, and temporal flicker.
- Avoid a render Subdivision level on effectors that makes simulation evaluation unnecessarily expensive.

### Secondary Particles

Add spray, foam, and bubbles after the liquid mesh passes. Validate particle count, lifetime,
velocity, clipping, and render representation. Do not convert every particle into an independent object.

### Foam

Foam is not white paint on every crest. Derive it from Ocean data, secondary particles, velocity,
curvature, impact, or a painted mask. Give foam a rough, scattering dielectric response and decay.

### Wet Maps

Use Dynamic Paint, attributes, or baked masks for surfaces contacted by water. Wetness should have
contact and drainage history, and should primarily affect roughness/reflection plus plausible
substrate darkening.

## 7. Material Ownership

- Simulation/Ocean/Wave owns large moving geometry.
- Shader owns reflection, transmission, IOR, absorption, micro-normal detail, sediment, and foam response.
- Geometry owns contained volume, waterline, visible meniscus, and puddle boundary.
- Dynamic Paint/attributes own contact history and wet maps.

Read `blender-material-surfacing/references/water-and-wetness-materials.md` for the liquid and
wet-surface shader. Do not duplicate large wave displacement in both cache and shader.

## 8. Cache And Iteration

1. Use a unique cache directory per accepted version.
2. Save a pre-bake blend checkpoint.
3. Test a short range in Replay or low-cost cache mode.
4. Bake data before dependent mesh/particle stages.
5. Record domain dimensions, resolution, time scale, participants, frame range, and cache type.
6. Invalidate/rebake when topology, transforms, domain, flow, or upstream animation changes.
7. Never overwrite an accepted cache during experimentation.
8. Render early/middle/late and fastest-impact frames before final bake approval.

## 9. Troubleshooting

### Empty Domain

Check domain type, flow type/behavior, flow inside domain, frame range, enabled emission, cache
state, and whether the source occupies enough voxels.

### Leaks Through Collider

Check effector role, normals, manifold/thickness, moving-object sampling, voxel size, collider
resolution, and initial intersections. Simplify or thicken the collision proxy before only raising resolution.

### Liquid Disappears Or Loses Volume

Check outflows, domain boundaries, mesh particle radius, resolution, narrow openings, time scale,
and whether the source/collider is smaller than useful cell size.

### Blobby Or Oversmoothed Mesh

Check domain resolution, mesh particle radius, smoothing, narrow-band settings, and source scale.
Do not sharpen with an unrelated high-frequency displacement.

### Explosive Splash Or Excessive Speed

Check scale, frame rate, inherited velocity, collider animation jumps, gravity, time scale, and initial overlaps.

### Cache Does Not Update

Free/invalidate the correct cache stage, use a new versioned directory, verify file permissions,
and confirm that the rendered frame range matches the bake.

### Water Looks Like Glass Or Plastic

Fix volume/contact geometry, reflection environment, absorption scale, roughness, wave hierarchy,
and foam/sediment evidence in the material route; do not blame the solver first.

## 10. Validation Gate

Require:

- explicit route: static volume, Ocean, Wave, Dynamic Paint, Fluid, or hybrid;
- real scale, domain/volume bounds, waterline/contact policy;
- declared ownership of macro shape, micro waves, foam, spray, wetness, and material response;
- low-resolution motion approval before final resolution;
- no collider leakage, tunneling, unstable bounds, or unexplained volume loss;
- versioned cache with representative frame evidence;
- liquid material and absorption validation when thickness is visible;
- unique top/side/perspective reviews for contained water and early/mid/late reviews for animation.

## 11. Official Sources

- Fluid: https://docs.blender.org/manual/en/5.2/physics/fluid/index.html
- Domain settings: https://docs.blender.org/manual/en/5.2/physics/fluid/type/domain/settings.html
- Liquid settings: https://docs.blender.org/manual/en/5.2/physics/fluid/type/domain/liquid.html
- Liquid mesh: https://docs.blender.org/manual/en/5.2/physics/fluid/type/domain/liquid/mesh.html
- Cache: https://docs.blender.org/manual/en/5.2/physics/fluid/type/domain/cache.html
- Ocean: https://docs.blender.org/manual/en/5.2/modeling/modifiers/physics/ocean.html
- Wave: https://docs.blender.org/manual/en/5.2/modeling/modifiers/deform/wave.html
- Dynamic Paint: https://docs.blender.org/manual/en/5.2/physics/dynamic_paint/index.html
