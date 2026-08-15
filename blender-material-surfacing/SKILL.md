---
name: blender-material-surfacing
description: Build, calibrate, layer, and validate production Blender materials including bare and coated metal, brushed steel, rust, aged and wet wood planks, stone, concrete, plastic, glass, fabric, water, dirt, moss, and wetness. Use when material identity, UV direction, real-world texture scale, PBR channel handling, roughness response, anisotropy, normal/bump/displacement, transmission, volume absorption, aging, or surface layering determines realism.
---

# Blender Material Surfacing

Build a material as evidence of a physical surface, not as a decorative color graph.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns substrate response, mapping, node graphs, and
material evidence only; it cannot use surfacing to conceal geometry or restart production analysis.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md`. Shader nodes are the
normal native owner of material response; Geometry Nodes do not replace substrate, coating, roughness,
or texture-scale decisions. When an explicitly requested local library shader or material function
is compatible, `blender-local-asset-library` may inspect it read-only. This Skill decides whether
its public controls, physical semantics, and render-engine behavior improve the material. NPR and
compositor assets remain with their engine-specific owners rather than entering the PBR workflow as
opaque materials.

## Upstream Gate

Material classification and scale hypotheses belong in Production Analysis. Apart from neutral
clay/diagnostic materials, do not begin look development until the target part passes Primary,
Structural, Transition, connection, real-bevel, and wireframe gates. Reject any request to use
color, roughness, normal, bump, displacement, darkness, or wetness to conceal wrong geometry or an
unclassified intersection.

## Start With Material Identity

Before creating nodes, record:

- substrate: metal, wood, stone, concrete, plastic, glass, fabric, liquid, or another material;
- manufacturing state: cast, machined, brushed, painted, varnished, sawn, planed, weathered, soaked, polished, or corroded;
- physical scale and visible texel scale;
- orientation: grain, brushing, rolling, weave, flow, or sediment direction;
- layer stack: substrate, coating, oxide, dirt, water film, moss, dust, and damage;
- geometry-changing features versus shader-only microdetail;
- target engine, camera distance, final resolution, and lighting environment.

Do not approve a material from its Base Color alone.

Read only the route-specific reference:

- `references/material-production.md` for the common PBR, mapping, scale, layering, and validation workflow.
- `references/metal-materials.md` for bare, brushed, coated, weathered, and corroded metal.
- `references/wood-materials.md` for boards, grain orientation, end grain, cracks, wetness, rot, and moss.
- `references/water-and-wetness-materials.md` for water surfaces, contained liquid, water films, puddles, and damp substrates.
- `references/common-materials.md` for stone, concrete, ceramic, plastic, rubber, glass, fabric,
  painted surfaces, soil, mud, dust, and moss.

## Production Protocol

1. Inspect geometry, dimensions, UV maps, face orientation, material slots, and reference evidence.
2. Choose UV, object, generated, triplanar, tangent, or curve coordinates from the material's physical direction and editability.
3. Establish real-world texture scale before tuning color or roughness.
4. Build the clean substrate first.
5. Add manufacturing direction and mid-scale structure.
6. Add roughness variation independently from color variation.
7. Add normal or bump for microrelief and displacement or geometry only for silhouette-relevant relief.
8. Add coatings, oxidation, dirt, wetness, moss, and damage with causal masks.
9. Validate under neutral diffuse light, a moving elongated reflection, and the production lighting.
10. Record texture paths, color spaces, mapping scale, material class, and known exceptions.
11. Recheck silhouette-relevant displacement, board edges, corrosion loss, cracks, and layered
    interfaces as geometry; return them to direct modeling when they change form or contact.

## Mapping Rules

- Use UVs for directional manufactured surfaces, boards, hero assets, decals, and image PBR sets.
- Align tangent direction with brushed metal, rolled metal, wood grain, fabric weave, and other anisotropic structure.
- Give each visible wooden board a valid UV island and intentional grain direction; do not use one shared box projection for all boards.
- Use object or triplanar mapping for non-hero irregular rock, concrete, dirt, or inaccessible background geometry when seams are less harmful than UV cost.
- Keep Base Color images in a color space intended for color data. Treat roughness, metallic, normal, height, masks, and displacement as non-color data.
- Never infer physical texture scale from a Noise Texture default value or object bounding box alone.

## Layering Rules

- Keep dielectric coatings separate from conductive metal beneath them.
- Treat rust, oxide, dirt, moss, and water as spatially limited layers with causes such as exposure, pooling, cavities, contact, drainage, edge wear, or orientation.
- Do not use one Noise Texture to drive color, roughness, normal, damage, and wetness identically.
- Break correlation between channels while preserving shared causal masks where appropriate.
- Keep puddles and thick water as geometry with volume; use a shader-only wetness layer only for a thin film.

## Completion Gate

Do not mark surfacing complete until:

- material class and layer stack match the reference or declared design;
- real-world texture scale and directional mapping are recorded;
- PBR image color spaces and normal-map conventions are correct;
- roughness produces material-specific highlight width under neutral review lighting;
- normal, bump, and displacement operate at distinct scales without double-strength artifacts;
- metal, wood, and liquid route checks from the references pass;
- repeated parts do not show synchronized or impossible mapping unless manufactured that way;
- `scripts/audit_materials.py` reports no blocking failures for required hero materials;
- unique review renders exist for diffuse, grazing-reflection, and production-light states.

Hand geometric cracks, board damage, deformed edges, and silhouette wear to `blender-direct-surface-modeling`. Hand flowing liquid, splashes, Ocean motion, Dynamic Paint, and caches to `blender-simulation-effects`.
