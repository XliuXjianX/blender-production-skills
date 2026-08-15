# Cloth Production Workflow

## Contents

1. Route the fabric problem
2. Prepare simulation topology
3. Establish scale and transforms
4. Build the modifier stack
5. Pinning, sewing, rest shape, and pressure
6. Calibrate physical properties
7. Collision construction
8. Garments on animated characters
9. Forces and timing
10. Cache, bake, and finalization
11. Troubleshooting ladder
12. Validation gate
13. Blender Python implementation pattern
14. Official sources

## 1. Route The Fabric Problem

Use Cloth when a thin flexible sheet changes shape because of gravity, inertia, contact, wind,
pinning, sewing, or pressure. Do not use Cloth merely because a material is soft.

Choose a different route when:

- the object is a spring-like volume: Soft Body or Cloth with pressure/internal springs after testing;
- the user wants a single art-directed static wrinkle with no physical cause: sculpt or Cloth Filter;
- the object is a rigid hinged sheet: constraints/rigid body;
- the fabric is already baked and only needs cleanup: direct mesh/sculpt correction;
- the requested folds are caused by a character: armature baseline plus Cloth and collisions.

Write down fabric type, real dimensions, attachment points, motion source, colliders, required frame,
and whether the result must animate or only settle into a static pose.

## 2. Prepare Simulation Topology

1. Start from the simplest surface that contains the required seams and silhouette.
2. Use reasonably uniform edge lengths in deforming regions.
3. Avoid long thin faces, tiny isolated edges, duplicate vertices, accidental internal faces,
   non-manifold seams, and abrupt density changes.
4. Add enough resolution for the smallest required fold, but not render microstructure.
5. Put extra resolution only where contact, pin gradients, seam curvature, or hero folds require it.
6. Keep topology stable before baking. Any modifier above Cloth changes the simulated mesh.
7. Test diagonal/triangulation bias on long quads and irregular patches by running a neutral drop.
8. Keep render thickness and high-frequency subdivision below Cloth unless the simulation
   specifically needs them.

Judge density from world-space edge length and desired fold radius. Do not use one subdivision
count for a handkerchief, stage curtain, denim coat, and building tarp.

## 3. Establish Scale And Transforms

- Set scene units and real object dimensions before tuning properties.
- Apply or explicitly account for non-uniform object scale.
- Confirm gravity direction and magnitude.
- Inspect collider scale and animation transforms.
- Start the cloth clear of accidental interpenetration; intended pre-contact must still respect
  collision distance.
- Allow pre-roll or early settling frames when the hero frame begins after the cloth reaches rest.

Changing scale after calibration invalidates mass, fold size, collision distance, and apparent
stiffness. Recalibrate instead of compensating with arbitrary strength values.

## 4. Build The Modifier Stack

Choose order from evaluated intent:

- Mirror or topology-generating modifier above Cloth: simulated topology includes it. Keep seam
  merge stable and test for self-collision at the symmetry plane.
- Armature/deformation above Cloth: provides the animated baseline that Cloth follows or departs from.
- Cloth: owns gravity, inertia, spring response, and collisions.
- Corrective Smooth or restrained cleanup below Cloth: fixes solver artifacts without redefining rest shape.
- Subdivision below Cloth: render smoothing after simulation.
- Solidify below Cloth: final thickness after simulation.

Do not blindly apply this order. A modifier that must affect rest shape belongs above Cloth; a
render-only effect belongs below. Record the reason for every modifier around Cloth.

## 5. Pinning, Sewing, Rest Shape, And Pressure

### Pinning

- Create a named vertex group for attachments.
- Use weight 1 only for truly fixed vertices.
- Use a gradient where cloth should transition from attachment to free motion.
- Inspect pin weights in isolation and test with colliders disabled.
- Pin to the evaluated position from modifiers above Cloth; do not animate cloth vertices by hand.

### Sewing

- Keep garment panel boundaries intentionally open before sewing.
- Match seam length and vertex distribution closely enough to avoid extreme initial spring force.
- Create sewing edges that connect intended vertex pairs and are not part of faces.
- Enable sewing and use a bounded maximum sewing force.
- Begin with panels close to their assembled position; do not ask sewing springs to pull across a
  huge distance in one frame.
- Inspect twisted pair order, crossed seams, gaps, and inverted normals before simulation.

### Rest Shape

- Use a rest shape key when the desired natural state differs from the evaluated start shape.
- Use Dynamic Mesh only when modifiers/shape keys above Cloth intentionally change rest shape each
  frame, such as squash-and-stretch animation.
- Do not enable Dynamic Mesh as a generic fix for sliding cloth.

### Pressure And Internal Springs

- Use pressure for closed or intentionally masked soft shells such as balloons and inflated cushions.
- Verify normals and leaks; holes can create drift or propulsion.
- Use pressure scale and target volume to resist volume loss, then test stability.
- Use internal springs for shell-like volumetric resistance only after standard surface Cloth proves insufficient.
- Use Fluid simulation for visible moving liquid; Cloth fluid density is a pressure/weight
  approximation, not a liquid solver.

## 6. Calibrate Physical Properties

Start from a Blender preset only as an initial state. Change one class at a time:

1. Mass and air viscosity: tune falling speed and inertia.
2. Tension and compression: tune stretch and bunching.
3. Shear: tune diagonal distortion.
4. Bending: tune fold radius and resistance to small wrinkles.
5. Damping: tune oscillation decay without freezing motion.
6. Quality steps: raise only after topology, scale, and property direction are correct.

Interpretation guide:

- silk/light lining: low bending resistance, fine folds, low collision friction, modest damping;
- cotton shirt: moderate bending and damping, readable medium folds;
- denim/canvas/tarp: stronger tension, shear, and bending resistance, larger folds, more damping;
- leather/heavy vinyl: high bending resistance, limited fine wrinkles, stronger thickness/contact cues;
- curtain: gravity-dominant vertical folds, top pin gradient, material-dependent bending;
- flag: wind/air response, stable attachment, enough subdivisions for traveling folds.

These are directions, not universal numeric presets. Calibrate against real dimensions and
reference motion. The fabric shader's sheen/roughness is separate from Cloth physics.

## 7. Collision Construction

For each participant classify Cloth, collider, self-collision region, or non-participant.

- Add Collision to obstacles, not just to the cloth object.
- Use simple, watertight, smoothly animated collision proxies for characters and complex props.
- Keep collision proxies close enough to preserve contact but simple enough for stable solves.
- Derive collision distance from cloth edge length, visual thickness, and scene scale.
- Enable self-collision only where layers can visibly fold onto themselves.
- Use a vertex group to restrict self-collision when full-mesh cost/noise is unnecessary.
- Tune object collision quality and cloth quality after fixing topology and initial intersections.
- Use impulse clamping carefully for tight unstable contact; do not hide a bad starting state.
- Test fast-moving colliders for tunneling over the full animation range.

Reject cloth that visibly floats above a collider because collision distance is oversized.

## 8. Garments On Animated Characters

1. Build or retopologize garment panels with clean seams and required ease.
2. Fit the rest garment without deep body intersections.
3. Use Armature/deformation above Cloth for the baseline motion.
4. Create pin groups for waistband, shoulders, cuffs, or designed attachments.
5. Use simplified body collision proxies and separate proxies for fast limbs if needed.
6. Test the widest pose and fastest motion before the full shot.
7. Add self-collision only after body collision is stable.
8. Use pre-roll into the shot or a settled rest pose.
9. Add render subdivision and thickness below Cloth.
10. Use corrective sculpt/shape keys only after the physical result is accepted and preserve the cache.

## 9. Forces And Timing

- Confirm scene gravity and Cloth field weights.
- Use wind/turbulence only when a source exists.
- Tune force scale with object scale and time scale.
- Avoid high-frequency turbulence before base gravity/contact behavior is stable.
- For looping motion, test continuity at loop boundaries rather than hiding a jump in editing.

## 10. Cache, Bake, And Finalization

1. Use a short low-resolution frame range for first tests.
2. Record frame start/end, quality, pin groups, collision settings, property values, and modifier order.
3. Save a pre-bake checkpoint.
4. Bake only after penetration, fold scale, and timing pass.
5. Store cache in a versioned project path.
6. Do not edit topology or modifiers above Cloth after baking without invalidating/rebuilding cache.
7. Keep accepted caches immutable; create a new version for changes.
8. Add Solidify, render subdivision, micro-normal weave, fuzz, and material after simulation.
9. Render representative contact frames, fastest-motion frames, and the hero frame.

## 11. Troubleshooting Ladder

### Explodes Immediately

Check initial intersections, unapplied/non-uniform scale, duplicate vertices, crossed sewing edges,
unbounded sewing force, extreme pressure, wrong normals, and collision distances before increasing quality.

### Penetrates Collider

Check collider physics, proxy coverage, frame-to-frame speed, collision distance, cloth/object
quality, mesh density, and whether a high-detail render mesh is incorrectly used as collider.

### Floats Above Surface

Reduce excessive collision distance, inspect proxy offset, account for Solidify placement, and
verify the visual thickness expectation.

### Rubber-Like Stretch

Increase appropriate tension/compression/shear resistance, verify scale, and reduce unsupported
mass/force. Do not use pinning everywhere to hide stretch.

### Too Many Tiny Wrinkles

Increase bending resistance, reduce unnecessary mesh density, inspect object scale, and separate
shader microdetail from simulated folds.

### Too Stiff Or Frozen

Reduce bending/tension or excessive damping and inspect pin weights. Ensure the entire mesh was
not accidentally included in the pin group.

### Noisy Self-Collision

Fix initial self-intersections, simplify folds/proxies, tune distance and friction, restrict the
self-collision group, and raise collision quality only after those repairs.

### Changes Between Viewport And Render

Compare render/viewport modifier visibility, subdivision levels above Cloth, cache validity,
frame range, dependency order, and whether render evaluates a different mesh.

## 12. Validation Gate

Require:

- declared fabric type, dimensions, and attachment/collider roles;
- topology edge-length distribution and no accidental non-manifold defects;
- modifier-order report;
- pin/sewing/rest-shape evidence;
- property calibration notes and no preset-only claim;
- stable representative frames with bounded motion;
- penetration/contact report including self-collision;
- reproducible versioned cache;
- hero, contact, and fastest-motion review renders;
- final material detail added after the simulation surface is approved.

## 13. Blender Python Implementation Pattern

Use RNA feature detection because settings can change between versions:

```python
cloth = obj.modifiers.get("Cloth") or obj.modifiers.new("Cloth", "CLOTH")
settings = cloth.settings

def set_if_present(owner, name, value):
    if hasattr(owner, name):
        setattr(owner, name, value)

set_if_present(settings, "quality", test_quality)
set_if_present(settings, "mass", calibrated_vertex_mass)
set_if_present(settings, "vertex_group_mass", pin_group_name)
set_if_present(settings, "tension_stiffness", tension)
set_if_present(settings, "compression_stiffness", compression)
set_if_present(settings, "shear_stiffness", shear)
set_if_present(settings, "bending_stiffness", bending)
```

Do not paste universal values. Read the installed `ClothSettings` RNA, set only properties present
in that Blender version, record every chosen value, then validate the actual simulation.

## 14. Official Sources

- Cloth overview: https://docs.blender.org/manual/en/5.2/physics/cloth/index.html
- Physical properties: https://docs.blender.org/manual/en/5.2/physics/cloth/settings/physical_properties.html
- Shape, pinning, sewing, rest shape: https://docs.blender.org/manual/en/5.2/physics/cloth/settings/shape.html
- Collisions: https://docs.blender.org/manual/en/5.2/physics/cloth/settings/collisions.html
- Cache: https://docs.blender.org/manual/en/5.2/physics/cloth/settings/cache.html
