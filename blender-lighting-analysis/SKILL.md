---
name: blender-lighting-analysis
description: Analyze reference-image illumination and build accountable Blender lighting from shadow direction, shadow length, softness, exposed faces, environment fill, bounce, practical sources, and material response. Use for reference matching, daylight, interiors, exterior environments, product scenes, atmospheric lighting, or any task where lights must be physically and visually justified instead of added as arbitrary fill or rim lights.
---

# Blender Lighting Analysis

Separate light inference from light creation. Analyze first; mutate Blender only after the lighting
hypothesis and gray-model prerequisites are recorded.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns illumination evidence, gray-light setup, and
accountable light roles only; it may not move an accepted camera or restart analysis to hide geometry.

## Evidence Order

1. Identify an object-ground contact and the corresponding shadow endpoint.
2. Infer horizontal Sun direction opposite the shadow vector.
3. Estimate Sun elevation from object height and shadow length when the receiving plane and scale
   are credible.
4. Infer source angular size or atmospheric softness from shadow penumbra.
5. Compare lit and unlit faces to estimate World/sky fill and bounce.
6. Identify visible practical sources, window projections, emissive surfaces, and occluders.
7. Record ambiguity and alternative hypotheses instead of inventing lights.

Read `references/lighting-analysis.md` before building a reference-matched rig. Validate the plan
with `scripts/validate_lighting_plan.py`.

## Gray-Light Gate

The first production-light pass may contain only:

- one Sun for the primary directional source;
- one low-intensity World/sky fill;
- accepted gray geometry;
- the review camera chosen by the user or task.

Match shadow direction, length, softness, lit/backlit relationship, dark-side visibility, and
exposure before adding bounce or practical lights. Neutral topology-review lights are separate
diagnostic tools and must not be mistaken for the production rig.

Lighting analysis may happen during Production Analysis, but the production gray-light pass may
use only an accepted clay Blockout. Final lighting remains locked until formal topology,
Structural Forms, Transition Forms, real bevels, and wireframe review pass.

## Additional-Light Contract

Every added light records:

- ID and Blender object name;
- physical or photographic source;
- role;
- reference evidence;
- color/temperature and size rationale;
- affected region;
- what visible evidence is lost if the light is removed.

Add an Area, Point, Spot, emissive mesh, HDRI, bounce card, or volume contribution only when the
Sun/World model cannot explain evidence. Delete or disable lights with no accountable role.

## Hard Rules

- Do not use rim, fill, or colored lights to hide wrong geometry, missing bevels, or failed normals.
- Do not begin final lighting before Transition Forms and topology/wireframe gates pass.
- Do not use an HDRI as an unexplained replacement for source analysis.
- Do not accept a light setup because it makes primitive seams, missing transitions, or faceted
  curves less visible. Re-run neutral MatCap and reflective geometry review first.
- Do not multiply lights until one-source shadow logic has been tested.
- Do not change accepted geometry or camera merely to make the lighting plan easier.
- Do not treat emission color as proof of emitted intensity or real light transport.

## Completion Gate

Require a passed gray-light comparison, documented Sun and World responsibilities, justified extra
lights, stable exposure and color management, shadow evidence, dark-side readability, material
response review, and a `lighting_plan.json` with no unresolved blocking source.
