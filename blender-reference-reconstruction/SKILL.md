---
name: blender-reference-reconstruction
description: Convert image references into spatial hypotheses, camera constraints, construction routes, material evidence, and measurable Blender reconstruction gates. Use whenever a user asks to replicate, recreate, match, clone, or reconstruct a scene, environment, object, material, lighting setup, or shot from one or more images, especially when room connectivity, hidden space, perspective, visible-frame fidelity, material identity, aging, wetness, or photographic treatment matters.
---

# Blender Reference Reconstruction

Convert image evidence into a testable three-dimensional explanation. Use a reversible Blockout to
test provisional spatial hypotheses after minimum analysis instead of waiting for every ambiguity
to disappear. This skill owns spatial interpretation, projective reasoning, and visual convergence;
  it does not replace geometry, deformation, simulation, procedural, shading, or validation specialists.

## Suite Authority

This skill owns observed reference evidence, spatial hypotheses, and reference comparison evidence.
`blender-scene-design` owns authored visual intent; `blender-production-router` owns route, stage,
retry, rollback, and deletion state. Map R0-R4 to the Router's existing stages; do not create a
parallel state machine, restart full analysis for a local failure, or choose a construction method.

## Visual Authority

Do not infer the deliverable from the existence of a reference image. For a fixed shot, the visible
frame governs. For a reusable asset or navigable environment, spatial coherence, connections,
support geometry, and off-camera completion are co-primary with reference-frame fidelity.

Preserve an accepted camera, crop, hierarchy, `P0` silhouette, material identity, and lighting
direction while downstream skills change construction methods. Technical evidence may reject an
implementation, but it must not silently redefine either the visual target or the declared spatial
scope.

Judge progress in this order: camera/crop, negative space, `P0` silhouette and contact, grayscale
hierarchy, material identity, lighting direction, then secondary detail. Stop at the earliest failed
category. More detail cannot compensate for an earlier failure.

## Required Artifacts

For every non-trivial reference-locked task, initialize these schema `1.0` files, then fill them
progressively at the gate that needs the decision:

- `reference_observation.json`: source dimensions, observed regions/entities, normalized bounds, production domain, occlusion order, evidence, confidence, and uncertainty register.
- `spatial_hypothesis.json`: coordinate frame, camera region, spatial axes, depth regions, portals, elevation changes, hidden/off-frame support space, scale anchors, alternative hypotheses, invariants, and cross-view blockout evidence.
- `camera_match.json`: projection hypothesis, lens range, horizon, vanishing evidence, frame anchors, negative-space ratios, and tolerances.
- `material_hypotheses.json`: substrate, coating, physical state, aging cause, wetness, required cues, alternatives, and confidence.
- `visual_targets.json`: hierarchy, luminance zones, palette, light sources, depth cues, photographic treatment, and simplification limits.
- `reference_gate.json`: gate state, evidence paths, measured comparison results, approvals, and unresolved blockers.
- `reference_derivatives.json`: one-attempt depth/white-model guide status and provenance. It is
  always non-blocking and never outranks the source reference.

At R0, prioritize observation, spatial topology, provisional camera, and blocking uncertainty.
Defer detailed construction requirements until R2 and final comparison evidence until R4. Do not
elaborate fields that cannot change a route, gate decision, repair, or handoff.

Gate checks are cumulative. Each required check must be `passed` and cite evidence; a global
image score cannot substitute for `semantic_material_identity` or `final_semantic_review`.

Use `scripts/init_reference_artifacts.py` to create the files. Run
`scripts/validate_reference_artifacts.py --stage blockout_entry` before reversible Blockout, then
run the normal gate stage before advancing a visual gate. Read
`references/spatial-reconstruction.md` first for environments or architecture, then read
`references/directional-structure-recovery.md` for stairs, railings, ramps, curved paths, or other
direction-dependent structures, and read
`references/reference-audit.md`, `references/material-forensics.md`, and
`references/visual-comparison-gates.md` as needed.

## Evidence Protocol

1. Inspect every supplied image at original resolution.
2. Separate observation from inference. Record visible evidence first; add one or more hypotheses second.
3. Assign confidence from `0.0` to `1.0`. Never turn a low-confidence hypothesis into an object name or material fact.
4. Fill `spatial_hypothesis.json` before naming final objects: camera region, scene kind, axes,
   regions, connectivity, elevation changes, occlusion order, scale anchors, and alternatives.
5. Mark each observation `P0`, `P1`, or `P2` by visible-frame importance and classify its
   `production_domain` as geometry, material, lighting, atmosphere, post, presentation, or
   spatial region.
6. Record normalized bounds and every visibly supported silhouette, overlap, contact, and
   negative-space cue for `P0` observations. Mark non-applicable or unobservable fields instead of
   inventing evidence.
7. Decompose material appearance into substrate, coating, damage, contamination, wetness, and
   light response. Uniform noise is not material analysis.
8. Route each buildable observation to the existing specialist skill that expresses its
   construction or physical cause.
9. Before Gate R2, expand `construction_graph.json` for geometric P0 observations and real material
   receivers. Do not force lighting, atmosphere, post effects, or spatial regions into fake mesh
   objects. Architectural negative space must reference its surrounding boundaries and connected
   spatial region.
10. At startup, inspect whether image generation/editing is callable. If available, attempt one
    depth-map guide and one neutral white-model guide. If unavailable, mark both
    `skipped_capability_unavailable`; if generation fails, mark `failed_non_blocking`. Continue in
    either case. Treat generated images as low-confidence hypotheses and never as topology truth.

## Reconstruction Gates

These are evidence labels attached to the Router's single `stage_state.json`, not an independent
workflow. Use `R0=analysis`, `R1=blockout`, `R2=primary_surface`, `R3=surfacing_lighting`, and
`R4=final`. A reference check may keep the current stage closed or issue a local repair request,
but it cannot advance, roll back, or restart the production state by itself.

### Gate R0: Reference Audit

Use two bounded states:

1. **Blockout entry**: require valid source files, deliverable/protected scope, major P0 parts or
   regions, a scale strategy, provisional camera/spatial route, and no critical destructive blocker.
   After at most two automatic reviews, record ordinary uncertainty as assumptions and allow only
   task-owned reversible Blockout with `production_analysis.status=provisional`.
2. **Formal production readiness**: before R1 can pass, complete at least three camera/composition
   anchors, connected spatial hypothesis, scale anchors, material/light hypotheses, five form
   levels, approved manufacturing Part Graph, geometry-versus-shading decisions, and construction
   routes for affected parts.

Block even Blockout only when ambiguity risks protected assets, changes the deliverable or system
class, lacks the target/reference, or forces materially different irreversible results. Do not use
ordinary uncertainty to loop indefinitely in R0.

### Gate R1: Camera And Blockout

Require a material-free render and reference comparison. Validate projection, horizon, anchor
positions, negative-space ratios, occlusion order, silhouette, region connectivity, portals,
elevation changes, and scale before primary surfaces. For environments, require unique camera,
top, front, and side blockout views. Do not use lighting or depth of field to hide a camera or
layout mismatch.

Score each substantially complete white-model attempt out of 100 when attempting to leave
Blockout, not while entering or iterating inside it, with
`scripts/update_blockout_score.py`: primary form and proportion `30`, spatial layout/connectivity
`25`, directional structures `25`, and structural contact/support/clearance `20`. Camera quality is
reviewed separately and never lowers this model-body score. A wrong stair ascent, railing bend,
supported edge, landing connection, or path frame is a critical directional failure and caps the
total at `39`.

`update_blockout_score.py` is a reference-evidence writer only. It must not mutate
`stage_state.json`. After recording a score, pass the result through the Router-owned
`../blender-production-router/scripts/apply_blockout_score_decision.py`; only that entry point may
apply `rebuild_required`, `continue_r1_checks`, or `stop_and_request_deletion_decision` to the
production state. Do not validate or begin another Blender mutation between these two steps.

Keep the camera `provisional` during the R1 solve. Hold it temporarily while adjusting geometry;
reopen it only when multiple stable lines or anchors demonstrate a projection error. Lock it when
camera-view and cross-view spatial checks both pass. Require explicit pass evidence for camera
projection, `P0` bounds, negative space, occlusion order, silhouette, and spatial connectivity. If
one fails, do not begin hero materials, simulation, secondary props, final lighting, or
photographic effects. On the first score below `40`, preserve evidence, reopen the model/spatial
hypothesis while preserving the user's camera, replace the task-owned Blockout, and rebuild from semantic anchors rather than local
nudges. A second consecutive score below `40` is counted only after a declared full rebuild; then
stop all Blender mutation and ask whether the user wants the exact task project deleted. Never
delete the project, backups, protected objects, or unrelated assets without explicit user approval.

### Gate R2: Primary Form And Material Identity

Require formal geometry from the routed construction method, classified visible connections,
correct material category, scale-consistent edge language, and close-up topology evidence. A
plastic crate rendered with a wood-like construction or a water volume represented by a reflective
slab fails this gate even if its color is similar.

Replace, convert, or explicitly reclassify every Blockout proxy in visible `P0` regions. Require:

- approved Part Graph and final object mappings;
- continuous primary topology with recorded connected-component counts;
- passed Primary, Structural, and Transition Forms;
- real assembly interfaces or fused/welded topology for every visible contact;
- evaluated Primary/Secondary/Micro/Sharp edge policy;
- unique front, side, top, hero clay, wireframe, MatCap, and reflective evidence.

`Join`, overlap, smooth shading, and Weighted Normal are not evidence of topology fusion or bevels.
A generic noise texture is not a floral
print, an emission rectangle is not projected window light, a reflective surface is not water, and
an authored periodic sheet is not a simulated cloth result when cloth behavior is visibly required.

At this gate, every `P0` entity must exist in `construction_graph.json` under the same ID and
contain a non-empty `requirements` object understood by `blender-geometry-validation`.

### Gate R3: Lighting And Surface State

Require causal wear, localized wetness, practical-light direction, bounce policy, black-level detail, glass transmission, and atmosphere to match the observation artifacts. Dirt must accumulate from gravity, contact, cavities, handling, oxidation, or flow rather than one global procedural noise.

Validate the light transport or documented photographic/compositing cause, not merely the final
color patch. Keep the accepted R1 camera and object layout fixed during this gate unless new image
evidence proves the earlier gate wrong.

### Gate R4: Final Visible Frame

Run `scripts/compare_reference_render.py` with `--observation reference_observation.json`.
Review the overlay and difference image at thumbnail and full resolution. Require all `P0`
anchors, material identities, luminance zones, and unresolved uncertainties to pass. A comparison
without P0 regions can never return PASS. Numerical similarity supports the decision but never
overrides a semantic mismatch.

`WARN` and `REVIEW_REQUIRED` are candidate states, not delivery states. A final candidate may be
shown for review, but it must not be described as complete. Return to the earliest failed category
or report a genuine blocker.

For an autonomous generation request, continue evidence-directed technical iterations while a
concrete repair remains available. Pause at the Blockout, Primary Surface, Systems when present,
and Final visual gates. Do not ask the user to approve a candidate that already fails a measurable
topology, spatial, or reference check.

## Convergence Loop

1. Compare the newest unique render with the reference at thumbnail and full resolution.
2. Name the earliest failed category and the affected `P0` regions.
3. Change one causal system or one region-level construction problem.
4. Render from the locked camera with the same review settings.
5. Accept the change only if the target category improves without regressing an earlier accepted category; otherwise restore the checkpoint.

A score of `40` or more only clears the emergency-rebuild threshold. It does not pass R1 by
itself; all camera, cross-view, spatial, directional, and semantic checks still need evidence.

Also score individual parts through `part_review_scores.json`. Two consecutive scores below `60`
pause that part only. Keep independent parts moving; only a critical primary part may close the
current visual gate. Individual part failure never triggers the whole-project deletion question.

## Hard Rules

- Do not promise first-pass perfection from a single image. Require measured iteration toward a fixed-view result.
- Do not begin formal topology, systems, surfacing, or destructive work before Gate R0 formal
  readiness passes. Reversible task-owned Blockout may begin after the minimum entry state passes.
- Do not partition the model from image color patches; use manufacturing, motion, material
  interface, instancing, export ownership, and real seams.
- Do not carry overlapping Blockout primitives into Structural or Transition Forms.
- Do not accept Functional or Detail parts while middle-scale Structural/Transition Forms are absent.
- Do not accept a clay render without wireframe evidence that explains the visible structure.
- Do not assume that a task is shot-only because it has a reference image.
- Do not lock the camera before the spatial hypothesis and cross-view blockout pass.
- Do not use screen-space agreement as proof of valid depth or connectivity.
- Do not replace a doorway, corridor, stair landing, or hidden required space with a flat dark plane.
- Do not move the camera merely to compensate for incorrect architecture; identify the failed variable.
- Do not identify a hidden or ambiguous state from a convenient modeling shortcut.
- Do not treat color similarity as material identity.
- Do not use shot-only scope to simplify visible hero geometry, visible contacts, reflections, or shadows.
- Do not use uniform noise as a substitute for construction history or aging causes.
- Do not accept a render because it is cinematic, attractive, or plausible when it differs from the reference hierarchy.
- Do not manually rewrite failed comparison evidence into a passing validation report.
- Preserve every accepted review image with a unique filename.
- Do not optimize validator status by moving an accepted camera, changing the target hierarchy, or adding visible validation-only geometry.
- Do not spend a visual iteration expanding administrative artifacts while an earlier visual gate is failed.

## Handoff

- Send spatial boundaries, portals, support geometry, unique static form, and topology connections
  to `blender-direct-surface-modeling`.
- Send manufactured part boundaries, seams, mounts, clearances, pivots, hierarchy, and constraints
  to `blender-assembly-structure`.
- Send controlled bends and path-following construction to `blender-deformation-rigging`.
- Send gravity, flow, collision, and time-dependent state to `blender-simulation-effects`.
- Send repetition and distribution to `blender-procedural-systems`.
- Send substrate, coating, metal, wood, liquid, wetness, PBR mapping, and aging construction to
  `blender-material-surfacing` after material hypotheses are accepted.
- Send shadow/source inference and the accountable Sun/World-to-production-light sequence to
  `blender-lighting-analysis`.
- Send final topology, connection, shading, volume, and evidence checks to `blender-geometry-validation`.

Completion requires `reference_gate.json` at `R4` with `passed`, no unresolved blocking uncertainty, and referenced visual evidence that exists on disk. Otherwise label the result as a candidate and state the earliest unresolved category.
