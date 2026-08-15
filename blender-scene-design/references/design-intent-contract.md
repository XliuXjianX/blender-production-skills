# Design Intent Contract

## Contents

1. Evidence and intent
2. Focal hierarchy
3. Depth and flow
4. Representation budget
5. Performance budget
6. Local repair map

## Evidence And Intent

Keep three categories separate:

- `observed`: visible or measured evidence supplied by a reference or existing scene;
- `inferred`: a testable spatial or construction hypothesis;
- `authored`: a deliberate design choice for an original or underspecified region.

Reference Reconstruction owns `observed` and spatial confidence. Scene Design may turn accepted
evidence into an authored hierarchy, but it must retain uncertainty and never upgrade an inference
to fact.

## Focal Hierarchy

Record one primary focus and no more than two secondary focuses. For each focus record its role,
expected screen or silhouette importance, contrast mechanism, supporting elements, and elements
that must remain quieter. Negative space is a designed region, not an empty leftover.

Use scale and density rhythm deliberately:

- large quiet mass -> medium structural articulation -> sparse functional detail;
- dominant repetition -> controlled variation -> visual rest;
- foreground framing -> midground focus -> background continuation.

Do not distribute equal contrast, detail, saturation, or repetition everywhere.

## Depth And Flow

Describe foreground, midground, background, region connections, elevation changes, occlusion order,
and leading paths. A stream, stair, rail, curb, wall edge, light band, or repeated module can direct
attention only when its start, direction, destination, and interruption policy are explicit.

For standalone assets, translate depth into form hierarchy:

- primary silhouette;
- structural planes and cavities;
- transition radii and section changes;
- functional interfaces;
- micro surface response.

## Representation Budget

Choose the cheapest representation that preserves the declared deliverable:

| Requirement | Representation |
| --- | --- |
| silhouette, cast shadow, contact, collision, close parallax | real evaluated geometry |
| repeated real forms | one formal source plus Array or instances |
| distant repeated hero assets | Collection Instances |
| field-driven density or masking | Geometry Nodes instances |
| microscopic roughness or color response | Shader Nodes |
| small relief without silhouette effect | bump or normal |
| deforming or colliding relief | geometric displacement or modeled topology |
| fixed-camera background with no parallax requirement | deliberate simplified geometry or image plane |

`camera_mobility` changes the budget. A free camera requires complete depth, backs, contact, and
occlusion that a fixed shot may simplify.

## Performance Budget

Declare practical limits rather than universal numbers:

- maximum task-owned objects and collections;
- instance count and realization policy;
- viewport and render geometry targets;
- texture resolution by importance and screen coverage;
- simulation preview and final cache resolution;
- render samples, engine, and expected frame time when relevant.

Reserve the largest budget for the primary focus and for geometry that affects silhouette, shadow,
contact, deformation, or close inspection.

## Local Repair Map

Use symptom-to-local-repair mapping:

| Symptom | Inspect | Repair scope |
| --- | --- | --- |
| focus is weak | hierarchy, contrast, density, occlusion | focal hierarchy only |
| scene is crowded | mid/background density and negative space | depth layers and representation budget |
| repetition looks synthetic | source variants, spacing, rotation, clustering | repetition rhythm or distribution system |
| object floats | support, contact, snap target, receiving plane | construction relationship |
| black patch or fake hole | thickness, side walls, occlusion, light leak | local geometry and material response |
| stair direction is wrong | semantic anchors, run/rise axis, landing ownership | directional skeleton and generator |
| rail bends to the wrong side | supported edge, path order, local frame | rail control path and frame |
| proportion is wrong | primary silhouette and structural masses | Primary/Structural Forms |

A Specialist reports the symptom and evidence. The Router chooses the rollback target. Do not rerun
the full reference or design analysis for a local failure.

