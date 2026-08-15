# Visual Comparison Gates

## Comparison Order

Compare from large structure to small detail:

1. aspect ratio and crop;
2. camera projection and horizon;
3. negative space and major occluders;
4. spatial region connectivity, elevation changes, and hidden support space;
5. `P0` bounds and silhouettes;
6. overlap order and contact points;
7. grayscale hierarchy and practical lights;
8. material category and highlight shape;
9. color palette and wet/dry separation;
10. aging, glass contamination, atmosphere, and photographic treatment.

Do not advance because later-stage polish looks attractive while an earlier category fails.

## Failure Response

Treat the first failed category as the only active visual problem until it passes:

- camera, crop, negative space, occlusion, region connectivity, or scale failure: return to the
  Router-owned `blockout` stage and freeze materials. Determine whether projection or layout failed
  before changing either one;
- silhouette, contact, construction, or material-category failure: return to R2 and keep the accepted camera locked;
- luminance hierarchy, light direction, wet/dry response, atmosphere, or photographic-treatment failure: return to R3 without moving accepted geometry;
- secondary-detail failure: change only the affected region.

Do not average improvements across categories. A lower global error does not compensate for a
regressed camera, hero silhouette, material class, or lighting direction. Preserve the last render
that passed all earlier categories and restore it when a change causes regression.

## R1 White-Model Score

After the white model is substantially complete, record a model-body `0-100` score:

- primary form, silhouette, and proportion: `30`;
- region depth, scale, portals, landings, and connectivity: `25`;
- stair, railing, ramp, and path directionality: `25`;
- contact, support, attachment, clearance, and penetration quality: `20`.

Camera, crop, and projection remain separate R1 checks and may be adjusted by the user. Do not
lower the model-body score for a camera mismatch, and do not reopen or move the camera as an
automatic response to a low model score.

Do not infer this score from global pixel MAE alone. Use the overlay, P0 regions, camera anchors,
top/front/side evidence, and semantic spatial checks. A wrong stair ascent, railing bend side,
supported edge, disconnected landing, reversed path, or uncontrolled curve twist caps the score at
`39`.

- First score below `40`: reject the current hypothesis, preserve evidence, keep the accepted camera,
  and rebuild task-owned Blockout geometry from semantic anchors. Do not restart complete analysis.
- Second consecutive score below `40`: stop all mutations and ask whether the user wants the exact
  task project deleted.
- A second low score counts only after a declared full rebuild. Re-rendering unchanged geometry is
  the same attempt.
- Never delete automatically. Present exact candidate paths and exclude backups, protected scene
  data, shared assets, and unrelated projects.
- A score of `40` or more resets the consecutive-low counter but does not pass R1 automatically.

## Evidence Views

Require unique files for:

- reference-aligned gray blockout;
- top, front, and side blockout views for environments;
- edge or silhouette overlay;
- grayscale comparison;
- neutral MatCap and reflective primary-surface reviews;
- material close-ups for `P0` entities;
- final overlay and difference image.

Always pass `reference_observation.json` to the comparison script. Global image error is easily
diluted by large matching dark or empty areas; require grid metrics and `P0` regional metrics.
A run without valid P0 regions remains `WARN` even when its global error is low.

Comparison artifacts are decision aids, not a production quota. Generate the smallest set needed
to expose the active failure; do not spend an iteration producing additional views that cannot
change the next action.

Review the frame at both thumbnail size and full resolution. Thumbnail review exposes hierarchy; full-resolution review exposes topology, shading, aliasing, and material construction.

## Default Tolerances

Use task-specific values when better evidence exists. Otherwise:

- aspect-ratio error: fail above `1%`;
- `P0` anchor-center error: warn above `2%` of image diagonal, fail above `4%`;
- `P0` width or height error: warn above `5%`, fail above `10%`;
- negative-space ratio error: warn above `3` percentage points, fail above `6`;
- grayscale mean absolute error on aligned thumbnails: warn above `0.12`, fail above `0.20`;
- unresolved blocking uncertainty: fail;
- wrong material category or wrong visible construction: fail regardless of pixel score.

## Decision Integrity

Numerical comparison cannot detect every semantic error. A uniform orange grade may lower pixel error while destroying material separation; a reflective slab may resemble water from one angle while remaining physically wrong. Record both numerical evidence and semantic checks. A semantic failure cannot be waived by an aggregate image score.

Never convert `WARN` or `REVIEW_REQUIRED` into a completion claim. Record the earliest unresolved
category and keep the render labeled as a candidate.
