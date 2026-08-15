# Common Material Workflows

## Stone And Concrete

Separate structure by scale:

- geometry/displacement: broken edges, large aggregate exposure, cracks that cast shadows, chipped corners;
- normal/bump: pores, fine aggregate, tool marks, small pitting;
- roughness/color: cement variation, staining, dust, polishing, wetness.

Concrete is a dielectric composite, not uniform gray noise. Use formwork seams, cast direction,
aggregate scale, efflorescence, water runoff, ground contact, and repair patches when supported.
Keep cracks connected to stress, joints, openings, settlement, impact, or weathering rather than a
random all-over Voronoi pattern.

## Ceramic, Tile, And Glaze

- Build tile size and grout spacing in real units.
- Use geometry or displacement for visible grout depth and chipped edges.
- Keep ceramic body dielectric; add a smooth glaze/coat only when present.
- Vary tile orientation, batch color, dirt, and wear subtly without destroying the manufactured grid.
- Put rough dirt and mineral residue in grout/cavities; polished walking areas may narrow roughness.
- For tactile paving, model the bump profile when it affects silhouette/contact shadow.

## Plastic And Rubber

- Treat ordinary plastic and rubber as dielectrics, not metallic surfaces.
- Choose roughness from molded, polished, textured, soft-touch, scratched, or weathered state.
- Add molding grain at micro scale and parting lines/ejector marks only when manufacturing evidence supports them.
- Use clear coat for lacquered plastic, not every shiny polymer.
- Use restrained subsurface only for materials and thicknesses that visibly transmit/scatter light.
- Rubber usually has broad highlights, dark but not perfectly black color, deformation/contact cues,
  and abrasion/polish in used areas.

## Glass

- Use closed geometry with real thickness for hero glass.
- Set physically plausible IOR and transmission; use roughness for frosted/dirty glass.
- Add absorption/tint by thickness rather than painting edges dark.
- Separate dust, fingerprints, condensation, scratches, labels, and coating from the glass body.
- Verify refraction, reflection, shadow/transmission, normals, and engine-specific settings.
- Do not use alpha transparency as the only glass model for a hero object.

## Fabric Shading

Cloth physics creates folds; the material creates fibers, weave, sheen, fuzz, dye, wear, and stains.

- Align UV/weave with pattern-cut direction and seams.
- Use normal/bump for weave at a scale visible in highlights, not giant woven relief.
- Use sheen for suitable fibers and grazing response; do not add it uniformly to leather or plastic.
- Separate warp/weft color and roughness only when visible at the camera distance.
- Add fuzz/hair only for close shots where it contributes to silhouette or grazing light.
- Keep wear at cuffs, seats, folds, contact, and sun exposure.

Read `blender-simulation-effects/references/cloth-production.md` for motion and collision. Shader
weave must not be used as evidence that Cloth physics is calibrated.

## Painted Walls And Plaster

- Separate wall geometry, plaster/substrate, primer/paint, repairs, dirt, moisture, and peeling.
- Paint is dielectric and often has a subtle roller/brush roughness scale.
- Use geometry for lifted flakes and deep missing plaster in hero views.
- Put water stains below leaks and along gravity/drainage paths.
- Keep corners, hand height, floor contact, and fixtures as distinct wear zones.

## Soil, Mud, Dust, Moss, And Organic Growth

- Soil and mud need aggregate scale, compaction, moisture, footprints/ruts, and contact with objects.
- Wet mud darkens and narrows roughness but retains broken clumps and shallow water separately.
- Dust accumulates on upward, sheltered, low-contact surfaces and softens roughness contrast.
- Moss/algae depend on persistent moisture, shade, porosity, and low traffic.
- Use geometry/instances for visible clumps and shader masks for thin coverage.
- Do not scatter growth uniformly across sunlit, dry, vertical, and heavily touched regions.

## Common Validation

For each material require substrate identity, physical scale, directional mapping where relevant,
roughness behavior, detail ownership, causal aging masks, and diffuse/grazing/final-light reviews.
Reject a material when its identity disappears after disabling Base Color.
