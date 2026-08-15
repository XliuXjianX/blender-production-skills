# Blender Production Protocol

## Contents

1. Deliverable split
2. Priority and conflict resolution
3. Preflight
4. Method routing
5. Stage gates
6. Transaction size
7. Recovery
8. Authority and retry budgets

## Deliverable Split

Choose one primary production path before work:

- **Reusable asset**: geometry, editability, topology, UV, naming, and export are primary. Camera and lighting are review tools.
- **Animated asset**: reusable asset requirements plus deformation, rig range, cache, and motion gates.
- **Environment**: connected spatial regions, elevation transitions, support geometry, modular
  structure, repetition, performance, navigable off-camera completion, and scene organization are
  primary. A reference image remains a required validation view but does not reduce this scope.
- **Shot-only result**: camera projection and visible-frame fidelity may permit lower off-camera fidelity, but visible intersections and physical logic still require classification.

## Priority And Conflict Resolution

Declare required checks separately from advisory checks before production:

- A required check protects the primary deliverable or a visible `P0` identity, silhouette,
  contact, material class, deformation, simulation, or export constraint.
- An advisory check improves hygiene, evidence, or off-camera robustness but cannot justify
  degrading an accepted user-facing result.

For reference-locked work, Reference Reconstruction owns observed evidence and spatial confidence;
Scene Design owns accepted focal hierarchy and visual intent. Geometry and simulation specialists
own how those targets are built. If a technical implementation fails, change the implementation
rather than moving the visual target. If no implementation satisfies both, keep the accepted
checkpoint and report the conflict instead of silently trading fidelity for a green report.

Artifacts support decisions. Keep them minimal until a gate requires additional evidence. Never
use artifact completeness, object count, or validator check count as a proxy for scene quality.

## Preflight

1. Record Blender version, file path, render engine, active camera, World, collection tree, object inventory, enabled add-ons, and available systems.
2. Mark protected objects and data blocks.
3. Decide whether work occurs in a new task collection or modifies named existing objects.
4. Save a checkpoint before destructive work.
5. Do not clear the scene, replace the World, or create another visible Blender process unless explicitly requested.

For an image-defined task, initialize the `blender-reference-reconstruction` artifacts, including
`spatial_hypothesis.json` and `reference_derivatives.json`. If image generation/editing is
available, attempt one depth guide and one neutral white-model guide. If it is unavailable or an
attempt fails, record the non-blocking skip/failure and continue. Generated guides are spatial
hypotheses only; the source reference remains authoritative.

Pass the minimum-analysis entry check before creating reversible Blockout geometry. Complete Gate
R0 before choosing final object categories, material identities, physical states, or formal
topology. Preserve alternative hypotheses when the image is ambiguous. Do not infer `shot` scope
merely because a reference exists.

## Method Routing

Ask what causes the result:

- A unique designed form is modeled.
- A predictable mapping is deformed.
- A controlled mechanism is rigged or constrained.
- Repetition and fields are instanced or procedural.
- Gravity, collision, inertia, pressure, flow, or breakage are simulated.
- Substrate identity, manufacturing direction, coating, roughness, wetness, and microscopic
  appearance are surfaced with scale-aware materials.

Then classify the construction grammar before creating formal geometry:

- negative space in one solid -> host volume plus Boolean cutter;
- regular vector repetition -> one source plus Array or linked instances;
- regular elevation sequence -> directional flight graph plus rise/run Array;
- constant profile along a path -> curve path plus bevel depth/object;
- one-time exact placement -> snapping;
- persistent surface relationship -> Shrinkwrap or Surface Deform;
- silhouette-affecting sampled relief -> sufficient topology plus Displace;
- unique non-parametric silhouette -> direct topology, subdivision, Boolean block-in, or sculpt.

Apply `native-component-contract.md`: identify the owning Blender component, create the minimum
source/control objects, configure it, evaluate it, and keep it non-destructive unless downstream
topology, simulation, sculpt, export, or per-element editing requires application. Python is the
orchestration layer. A direct BMesh/Mesh implementation must explain why no native component can
express the unique result.

For each detected grammar, record its parameter owners and compare the native generator with
manual assembly. Prefer the route in which a small semantic parameter set updates every dependent
part. Manual assembly must state a physical or downstream reason; familiarity is not a reason.

Produce two to four candidates only when more than one system is plausible. Score each on:

- causal fit;
- editability;
- art direction;
- runtime and memory cost;
- version/extension availability;
- downstream compatibility.

Reject a shortcut explicitly when it would create unexplained overlap, excessive objects, manual fake physics, or an unnecessary Geometry Nodes graph.
Also reject three-piece frames used to imitate a cut in one monolithic wall, individually moved
regular steps/modules, overlapping segments used to imitate a continuous sweep, unmeasured visual
alignment, and displacement without declared topology density or coordinates.

## Stage Gates

`modeling_stage` is a one-way production state except when validation explicitly rolls it back:

```text
analysis -> blockout -> topology_construction -> structural_forms ->
transition_forms -> functional_parts -> surface_details -> systems ->
surfacing -> lighting -> final
```

Do not skip a state because the current render is recognizable. A later state may begin only when
the preceding form gate and its scene evidence pass. The only subjective user pauses are the
Blockout, Primary Surface, Systems (when present), and Final visual gates; technical checks run
inside those gates before asking for approval.

### Gate 0A: Minimum Viable Analysis

Keep Blender mutation blocked while determining only:

- deliverable and completion scope;
- protected scene/task-owned scope;
- major parts or spatial regions;
- real-scale strategy or an explicit scale hypothesis;
- provisional construction/system route;
- compact design intent, focal hierarchy, depth/flow, camera mobility, and representation budget;
- critical blockers whose answer would change the asset category or cause destructive work.

Limit automatic review to two rounds. If ordinary uncertainty remains, record an assumption, set
`production_analysis.status=provisional`, set `execution_scope=reversible_blockout`, and begin a
task-owned Blockout. Only missing targets/references, protected-asset risk, destructive ambiguity,
or a choice between materially different irreversible outcomes may keep this gate closed.

### Gate 0B: Production Analysis

Before formal topology, simulation, procedural generation, surfacing, cache, export, or destructive
work, complete reference observations, scale, completion scope, spatial/support structure,
five-level form hierarchy, approved Part Graph, geometry-versus-shading decisions, lighting
evidence, material classes, and system requirements for the affected parts. Set
`execution_scope=formal_production` only when this gate passes.

### Gate R0: Reference Audit

For image-defined work, require source dimensions and enough P0, scale, protected-scope, camera,
region, and provisional-route evidence to enter Blockout. Continue refining spatial axes,
connectivity, portals/elevation changes, occlusion order, material hypotheses, light-source
hypotheses, and alternatives during Blockout. All route-changing uncertainty must be resolved
before Gate R1 passes and formal production begins. R0 is reference evidence attached to
`analysis`; R1 maps to `blockout`; R2 maps to Primary Surface; R3 maps to Surfacing/Lighting; R4
maps to Final. These labels never form a second state machine and never advance work independently
of `stage_state.json`.

### Gate 1: Blockout

Require correct scale, proportion, silhouette, component count, spatial layout, camera
projection, P0 anchor positions, occlusion order, negative-space ratios, portal connectivity, and
hidden support space. Ignore surface polish. Keep the camera provisional while solving; lock it
only after camera view and required orthographic structural views pass.
For reference-locked work this is Gate R1 and a hard lock: no hero materials, simulations,
secondary props, or final lighting may begin while it is not passed.

When stairs, railings, ramps, escalators, tracks, pipes, or curved paths are visible, require a
semantic directional skeleton before generated geometry: ordered endpoints, start/end ownership,
ascent or travel direction, landings, supported edge, up axis, control path, handedness, and
validation views. Dependent steps, posts, rails, and fittings must regenerate from this skeleton.

At substantial white-model completion, score the model body: primary form/proportion `30`, spatial
layout/connectivity `25`, directional structures `25`, and contact/support/clearance `20`. Camera
quality is a separate user-adjustable R1 check and contributes zero points to this score. A critical
direction error caps the model score at `39`.

- First score below `40`: preserve evidence, keep the user's camera unchanged, reopen the
  model/spatial hypothesis, and replace the task-owned Blockout from semantic anchors.
- Second consecutive score below `40`, counted only after a declared full rebuild: stop all scene
  mutation and ask the user whether the exact task project should be deleted.
- Never delete automatically. Require explicit user confirmation after listing candidate and
  protected paths.
- A score at or above `40` clears only the emergency threshold; every normal R1 check must still
  pass.

Do not require the whole-model R1 score merely to enter or iterate inside Blockout. Require it only
when attempting to pass Blockout and enter Formal Topology Conversion.

### Per-Part Reviews

Score every buildable part independently at Analysis Readiness, Blockout, Formal Topology,
Structural/Transition, Systems when applicable, Surfacing, and Final. Use stage-specific criteria
from `part_review_scores.json` and preserve evidence for each attempt.

- `80-100`: pass.
- `60-79`: pass with a local repair list.
- `40-59`: repair locally and rescore without advancing that part.
- below `40`: rebuild only the affected part from its semantic route.
- Two consecutive scores below `60` at the same part/stage: mark `needs_user_review` and stop
  automatic attempts at two.

Pause a non-critical failed part while independent parts continue. Pause the whole task only when
a critical primary part reaches `needs_user_review` at one of the four visual gates. A per-part
failure never requests project deletion; the deletion question remains exclusive to two complete
R1 white-model rebuilds below `40`.

### Gate 2A: Formal Topology Conversion

Convert every Blockout proxy into one of three explicit outcomes: replace with a formal mesh,
convert into an intentional editable construction, or retain as a genuinely separate manufactured
primitive. Archive or remove replaced task-owned proxies. For each major part require a named
construction method, final object mapping, connected-component count, construction operations,
real bevel policy, and unique wireframe evidence. `Join`, parenting, collection membership,
overlap, smooth shading, or Weighted Normal do not satisfy this gate.

### Gate 2B: Structural Forms

Require the large cuts, slopes, frames, cavities, protrusions, supports, portals, and spatial
connections that explain how the primary masses are built. A scene with recognizable primary
blocks and small details but no middle-scale structural forms fails and returns to this gate.

### Gate 2C: Transition Forms

Require real topology or explicitly non-destructive evaluated geometry for blends, radii, shell
turns, section changes, corner flow, welded/fused regions, mating interfaces, and manufactured edge
language. Require front, side, top, hero clay, wireframe, neutral MatCap, and reflective evidence.
Only after this gate may Functional Parts begin.

### Gate 2D: Functional Parts And Surface Details

Build openings, handles, pivots, mounts, buttons, brackets, fasteners, markings, and wear in that
order. Every functional part needs a physical role and receiving interface. Surface details cannot
repair or conceal a failed Primary, Structural, or Transition form.

### Gate 3: Deformation Or Simulation

Require tested control range or low-resolution simulation evidence, stable participants, acceptable intersections, and cache policy.

### Gate 4: Surfacing And Final

Require UV direction and density, physical texture scale, substrate/layer identity, PBR map color
spaces, roughness response, normal/bump/displacement ownership, and neutral plus grazing-reflection
material reviews. Metal, wood, and liquid follow their specialist checks. Then require render or
export checks appropriate to the deliverable and a final validation report.
For image-defined work, also require Gate R4, a unique overlay and difference image, semantic
material-category review, and no unresolved blocking uncertainty.

`WARN`, `REVIEW_REQUIRED`, and a visually rejected candidate are not completion states. Preserve
the candidate with a unique name, return to the earliest failed category, and iterate or report a
real blocker.

## Topology Rollback

After every construction transaction, evaluate the topology-first rollback conditions. One strike
fails the affected part. Two distinct strikes set `rollback.required=true`, reopen either
`topology_construction` or `structural_forms`, block Systems/Surfacing/Lighting work, and preserve
the last accepted checkpoint. Repair only task-owned data. A wireframe that reveals primitive
stacking overrides an attractive clay render.

## Transaction Size

One transaction solves one region-level or system-level problem, not one vertex and not an entire asset:

1. inspect;
2. state local goal;
3. checkpoint if destructive;
4. execute;
5. validate;
6. accept or restore.

Run at most three automatic repair attempts for ordinary technical failures at the same gate.
Preserve evidence and stop after the third materially equivalent failure. The R1 below-40 emergency
policy is stricter: rebuild after the first low score and stop for user decision after the second
consecutive low score.

Per-part review is stricter still: allow at most two scored attempts for one part/stage. Do not use
the three-attempt technical allowance to create a third part score or restart the counter under a
new filename.

Do not repair a later stage while an earlier visual category remains failed. Return to camera and
layout for R1 failures, construction for R2 failures, and lighting/material response for R3 failures.

## Recovery

- Keep the last accepted stage file and the failed attempt.
- Never overwrite accepted simulation caches.
- Use unique filenames for review images.
- Restore only task-owned data from a checkpoint; do not roll back unrelated user changes.

## Authority And Retry Budgets

Use one authority matrix:

- Router: route, production stage, retry counters, rollback target, visual pauses, and deletion question.
- Scene Design: design intent only.
- Reference Reconstruction: reference evidence and spatial hypotheses only.
- Specialist: construction in its assigned domain and local repair evidence only.
- Geometry Validation: `PASS`, `WARN`, or `FAIL` evidence only.
- User: visual approval and explicit deletion decision.

Use one set of budgets in `stage_state.json`:

- minimum-analysis reviews: 2;
- ordinary technical repairs per stage: 3;
- scored reviews per part and stage: 2;
- consecutive complete white-model scores below 40 before stopping: 2;
- route candidate replacements: 1.

An unchanged-geometry rerender does not consume an attempt. A Specialist cannot reset a counter by
renaming an attempt or reopening analysis. A Validator cannot perform rollback. A failed part stays
local unless it is a critical primary part at a visual gate. Project deletion always requires an
explicit user decision.

Every local failure report contains `symptom`, `evidence`, `likely_owner`, `affected_part`,
`recommended_rollback_target`, and `geometry_revision`. The Router rejects duplicate reports for
unchanged geometry and chooses the next action.
