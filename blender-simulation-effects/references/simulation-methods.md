# Simulation Method Notes

## Cloth

Use `cloth-production.md` for the full construction, calibration, collision, cache, and repair
workflow. The minimum route is:

- use reasonably uniform simulation topology;
- apply scale and define physical dimensions;
- create pin groups, collider roles, collision distance, and self-collision policy;
- calibrate one property class at a time from a short low-resolution test;
- simulate before adding Solidify or render subdivision;
- inspect penetration, stretch, fold scale, damping, rest shape, and cache reproducibility.

## Soft Body

- Define goal weights, edge springs, stiffness, damping, mass, and self-collision.
- Use for elastic response rather than thin fabric.
- Test volume collapse and oscillation decay.

## Rigid Body

- Classify Active, Passive, Animated, and constraint participants.
- Choose collision shape from accuracy and cost.
- Set mass ratios, friction, restitution, margin, substeps, and iterations intentionally.
- Inspect tunneling, jitter, energy growth, and sleeping behavior.

## Fluid

Use `water-production.md` for contained water, ocean, ripples, liquid domains, mesh, particles,
foam, spray, cache, material ownership, and troubleshooting.

- Define domain, flow, effector, cache directory, frame range, scale, and resolution.
- Verify domain bounds contain the effect for the whole range.
- Start with low resolution and no secondary particles.
- Add mesh, spray, foam, or detail only after base motion passes.

## Static Contained Liquid

- Confirm that the reference supports liquid rather than empty, wet, or reflective container material.
- Build a closed, non-zero-volume mesh conforming to the interior with the waterline below the rim.
- Separate large-scale surface shape from micro-normal detail.
- Use physically plausible IOR, low but nonzero roughness, and volume absorption when thickness is visible.
- Add Wave, Dynamic Paint, or Fluid only when a visible disturbance has a causal source.
- Reject a plane or thin rounded slab presented as a volume.

## Dynamic Paint

- Choose Canvas output type and Brush influence.
- Match resolution to the visible surface scale.
- Verify cache invalidation after setup changes.

## Ocean And Waves

- Use Ocean for large deep-water spectra and foam data.
- Use Wave or Dynamic Paint for local ripples.
- Use shader normals for microstructure.
- Use Fluid only when true volumetric interaction or splashing is required.

## Particles, Boids, And Fracture

- Probe feature and extension availability first.
- Use stable instances and avoid converting every particle to an object.
- For Boids, test rule order, goals, avoidance, speed, and orientation.
- For fracture, provide non-uniform piece size, interior material, rigid-body mass variation, constraints when needed, secondary debris, and dust.
