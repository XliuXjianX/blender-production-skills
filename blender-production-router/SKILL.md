---
name: blender-production-router
description: Orchestrate production-grade Blender work by probing the installed Blender version, retrieving relevant official Blender documentation, assigning visual design intent, classifying shape grammar and geometry/deformation/procedural/physics/shading needs, comparing direct Blender components with node systems, creating staged artifacts, and routing to specialist skills. Use for every non-trivial Blender creation, reconstruction, simulation, animation, environment, or scene-modification request, especially when the user does not know whether to use topology, Boolean, Array, curves, snapping, Displace, simulation, Geometry Nodes, or shading.
---

# Blender Production Router

Act as a production supervisor, not a primitive scene assembler.

## Sole State Authority

Own `task_route.json`, `stage_state.json`, retry budgets, rollback targets, visual pauses, and any
project-deletion question. Specialists may report evidence and local repair requests, but they may
not reroute the task, restart complete analysis, advance stages, consume retries, or roll back work.
Geometry Validation reports `PASS`, `WARN`, or `FAIL`; the Router decides the response.

## Supervisory Priority

Choose one primary success criterion before routing specialists:

- For a reference-locked shot, prioritize visible-frame `P0` fidelity, then correct object/material identity, then technical integrity, then artifacts and metrics.
- For a reference-guided environment, prioritize coherent spatial regions, traversable or
  structurally valid connections, scale, and the reference camera together. The reference frame
  remains a required view, not permission to build a 2.5D set.
- For a reusable or animated asset, prioritize deformation/export integrity, then visible form, then presentation evidence.
- Treat JSON files, screenshots, and validator output as evidence of work, never as the work itself.

When requirements compete, preserve the last visually accepted checkpoint and choose another
implementation. Never move an accepted camera, silhouette, hierarchy, or lighting direction only
to reduce a validator warning. A concrete geometry `FAIL` on a required visible object still blocks
that object; an advisory `WARN` on a helper or intentional exception does not outrank the primary
success criterion.

## Start Here

1. Inspect the current scene before changing it. Preserve the existing World, cameras, collections, objects, and materials unless the request explicitly replaces them.
2. Detect Blender capabilities with `scripts/probe_blender_capabilities.py` when the cache is absent or the Blender version changed.
3. Classify the request before modeling. Route visual intent for scenes and standalone assets to
   `blender-scene-design`, then separate:
   - fixed shot, reusable asset, navigable environment, or animated environment deliverable;
   - camera region, spatial axes, connected regions, elevations, and hidden support space;
   - unique static form;
   - topology or volume connection;
   - predictable deformation;
   - mechanical motion;
   - repetition or distribution;
   - time-dependent physical phenomenon;
   - material or shading appearance;
   - reference-locked reconstruction.
   Also classify the construction grammar of each major form: subtractive opening, additive
   fusion, fixed-vector repetition, path repetition, swept profile, revolved profile, predictable
   deformation, one-time snapped placement, persistent conformity, sampled relief, unique form,
   or physical response. Do this before deciding how many primitives to create.
   When one or more images define the target, route reference interpretation to
   `blender-reference-reconstruction`. Pass the minimum-analysis entry check before reversible
   Blockout; complete Gate R0 and the affected part analysis before formal topology or systems.
4. For version-sensitive or unfamiliar systems, query only official Blender sources with
   `scripts/search_official_blender_docs.py`. When `route_blender_task.py` writes artifacts, it
   resolves `official_doc_resolution` against the detected Blender major/minor cache and records
   only the relevant pages. Set `BLENDER_PRODUCTION_OFFLINE=1` to force cached-only behavior.
5. For a non-trivial task, run `scripts/route_blender_task.py` to create the public artifacts before executing product work. Keep initial artifacts skeletal. Expand only fields that change a route, gate decision, repair, or final handoff; do not spend a visual iteration elaborating administrative detail.
   For image-defined work, resolve `reference_derivatives.json` at startup: attempt one depth-map
   guide and one neutral white-model guide only when image generation/editing is available. Mark
   unavailable or failed attempts as non-blocking and continue. Generated guides are hypotheses,
   never reference truth or topology evidence.
   When the user explicitly requests a local asset, node preset, Blueish asset, or Asset Browser
   entry, or when the selected route is a node-centric/reusable node system, load
   `blender-local-asset-library` for read-only candidate discovery and source inspection. Use a
   passed runtime probe as eligibility evidence, then let the owning specialist inspect and
   task-scene validate the actual graph. It cannot import an opaque graph or change the route on
   its own.
6. Load only the specialist skills selected by the route:
   - `blender-scene-design`
   - `blender-reference-reconstruction`
   - `blender-direct-surface-modeling`
   - `blender-assembly-structure`
   - `blender-deformation-rigging`
   - `blender-simulation-effects`
   - `blender-procedural-systems`
   - `blender-geometry-nodes-studio`
   - `blender-local-asset-library` when explicitly requested or when the selected node-centric
     route has eligible local catalogs
   - `blender-material-surfacing`
   - `blender-lighting-analysis`
   - `blender-npr-eevee`
   - `blender-npr-cycles`
   - `blender-geometry-validation`

Read `references/production-protocol.md` for stage gates,
`references/topology-first-production-contract.md` before any modeling task, and
`references/artifact-contract.md` for artifact schemas. Read
`references/native-component-contract.md` before choosing or scripting a construction method.
Read `references/system-choice-contract.md` for every direct-component versus node-system decision.
For architectural openings, stairs, repeated modules, rails, pipes, trim, snapping, or geometric
relief, also read
`../blender-direct-surface-modeling/references/construction-method-playbook.md`.

Store runtime caches under
`%USERPROFILE%\.codex\cache\blender-production-suite\<major.minor>\`: use
`blender_capabilities.json` and `official_blender_docs_index.json`. Rebuild both when the detected
major/minor version changes. When the network is unavailable, use only a previously live-verified
cache plus RNA probing and mark official-document verification as cached rather than current.

## Routing Rules

- Use `blender-scene-design` for the visual thesis, focal hierarchy, depth layers, visual flow,
  camera mobility, representation budget, and performance budget. It never owns construction or state.
- Use `blender-reference-reconstruction` before other specialists when an image defines visible-frame composition, object or material identity, lighting, aging, or photographic treatment. This skill supervises evidence and convergence while downstream skills still own construction.
- Use direct topology, subdivision control cages, Boolean, remesh, sculpt, or retopology for unique static form.
- Use one host volume plus a reusable Boolean Difference cutter for a door, window, arch, niche,
  or portal in one monolithic wall. Build separate jamb/lintel pieces only when they are genuinely
  separate construction members.
- Use an accepted directional skeleton plus one source and Array constant offset for a regular
  straight stair flight. Solve rise, run, count, axes, and landing ownership before generation.
- Use a Bezier/NURBS path plus bevel depth or bevel object for constant-profile rails, pipes,
  cables, hoses, molding, and trim. Use Curve Modifier only when an existing mesh must deform.
- Use snapping for one-time exact placement and Shrinkwrap/Surface Deform for persistent
  conformity. Declare snap target, element, base, orientation, axes, and offset.
- Use sufficient topology plus Displace for editable or silhouette-affecting sampled relief;
  keep microscopic bump/normal work in Shader Nodes.
- Use native deform modifiers, curves, lattices, armatures, constraints, shape keys, or drivers for predictable deformation and mechanical motion.
- Use Cloth, Soft Body, Rigid Body, Fluid, Dynamic Paint, Ocean, particles, force fields, or fracture workflows when gravity, inertia, collision, flexibility, flow, pressure, or breaking causes the result.
- Use Array, instances, curves, Geometry Nodes, or particles for repetition, distribution, fields, or stateful procedural systems, then select the smallest one that preserves required control.
- Use `blender-material-surfacing` and Shader Nodes for substrate identity, UV/mapping scale,
  metal/dielectric response, wood grain, roughness, normal, bump, displacement, transmission,
  volume absorption, wetness, aging, and microscopic variation.
- Use `blender-npr-eevee` for Eevee Shader-to-RGB toon bands and deformation-following
  inverted-hull outlines.
- Use `blender-npr-cycles` for Blender 5.2+ Cycles four-direction Shader Raycast outlines.
- Use Line Art or Freestyle for camera-aware creases, intersections, hidden lines, and
  scene-wide line extraction.
- Use Geometry Nodes when fields, context-aware/adaptive variation, coordinated sources, scalable instances, reusable procedural topology, complex curve-data processing, or node simulation materially improve the result. Do not suppress a node route merely because a direct component exists; record the concrete benefit and rejected alternative.
- Treat every visible connection as one of the relationship types in `construction_graph.json`. Unclassified visible intersections are defects.
- Require every buildable route to declare `native_system`, `source_objects`, `semantic_inputs`,
  `generated_dependents`, `code_role`, `application_policy`, and `native_component_evidence`.
- Use Python to create and configure Blender components, controls, validation, and artifacts. Do
  not loop over a count to bake final fragments when Array, instances, curves, Geometry Nodes, or
  simulation should own the dependency.

## Production Stages

Run these stages in order:

1. `analysis`: capability/scene preflight, brief, references, design intent, focal/depth/flow
   hierarchy, representation and performance budgets, scale strategy, completion scope,
   protected scope, major parts, uncertainty, and provisional route. Limit automatic analysis
   review to two rounds. Once this minimum viable analysis passes, allow reversible Blockout with
   `production_analysis.status=provisional`; keep destructive edits, formal topology, systems,
   surfacing, and export blocked until the affected part analysis and full production gate pass.
2. `blockout`: provisional-camera proxy geometry for proportion, silhouette, occlusion, negative space, spatial
   connectivity, scale, and directional structures; lock the camera only after camera and
   cross-view checks pass. Build stairs, railings, ramps, and path-driven systems from ordered
   semantic anchors before generating repeated geometry. Parameterized Boolean cutters, Arrays,
   curve paths, and snapped modules are valid reversible Blockout controls when their semantic
   dimensions are recorded; they do not require waiting for formal topology.
3. `topology_construction`: replace, convert, or explicitly retain each Blockout proxy; build the
   formal primary meshes and record construction operations, component counts, and wireframes.
4. `structural_forms`: build major cuts, slopes, frames, cavities, supports, portals, and spatial
   connections. Missing middle-scale structure is a blocking failure.
5. `transition_forms`: build real blends, radii, shell turns, section changes, mating surfaces,
   fused boundaries, and scale-aware bevel geometry.
6. `functional_parts`, then `surface_details`: build physical interfaces before fasteners,
   markings, micro seams, wear, or decoration.
7. `systems`: add deformation, rigging, low-resolution simulations, or procedural generation only
   after their source geometry and interfaces pass.
8. `surfacing`: UV, substrate response, mapped material scale, and causal surface variation.
9. `lighting`: gray-light proof, accountable production lights, then final render/cache/export.
10. `final`: run all geometry, relationship, simulation, performance, material, and multiview gates.

For reference-guided work, Gate R1 is a hard production lock. If the neutral blockout fails,
identify whether projection or spatial layout failed, then rebuild that hypothesis before creating
hero materials or secondary detail.
Do not compensate for a failed R1 with lighting, depth of field, cropping, extra props, or later
surface polish.

At substantial white-model completion, ask `blender-reference-reconstruction` to record the
four-part model-body `0-100` R1 score. The reference Specialist writes only
`reference_gate.json`; immediately pass that artifact to
`scripts/apply_blockout_score_decision.py`, which is the only operation allowed to change
`stage_state.json` for this decision. The first score below `40` forces a full task-owned Blockout
rebuild. A second consecutive below-40 score after that declared rebuild stops all work and asks the
user whether the exact task project should be deleted. Never delete automatically. This emergency
policy overrides the ordinary three-attempt technical repair allowance.

Pause for user approval at four visual gates only: Blockout, Primary Surface (after Structural and
Transition Forms), Systems when a visible simulation/rig/procedural result exists, and Final.
Before each pause, complete the technical checks and show unique evidence; never ask the user to
approve a known failed candidate. Run up to three technical repair loops inside a gate before
rebuilding the failed hypothesis or reporting a real blocker.

## Part Review And Bounded Recovery

Use `part_review_scores.json` and `scripts/score_part_review.py` for every buildable part at
Analysis Readiness, Blockout, Formal Topology, Structural/Transition, Systems when applicable,
Surfacing, and Final.

- `80-100`: pass.
- `60-79`: pass the local gate with recorded repairs.
- `40-59`: keep the part local, repair and rescore; do not advance that part.
- below `40`: rebuild that part from its semantic anchors or construction route.
- After two consecutive scores below `60` for the same part and stage, stop rescoring and mark only
  that part `needs_user_review`.

Continue independent parts while a non-critical part is paused. A failed critical primary part may
close only its current Blockout, Primary Surface, Systems, or Final visual gate. Part failure never
authorizes project deletion and never increments the separate whole-Blockout below-40 deletion
policy. Do not make a third automatic score attempt.

## Hard Rules

- Do not reset the scene or World as a default cleanup step.
- Do not open another visible Blender instance. Reuse the current MCP instance; use background Blender only for isolated tests.
- Do not solve post-blockout silhouette problems by adding unexplained primitives.
- Do not infer part boundaries from color blocks. Split objects by manufacturing, motion, material
  interface, instancing, export ownership, or a real seam.
- Do not let a Blockout proxy enter Structural Forms. Replace, convert, or explicitly reclassify it.
- Do not treat `Join Objects`, parenting, collections, or shared materials as topology fusion.
- Do not treat Shade Smooth, Weighted Normal, a bevel shader, or a corner insert as bevel geometry.
- Do not create Functional Parts or Surface Details before Structural and Transition Forms pass.
- Do not convert a low-confidence reference hypothesis into a definitive object or material.
- Do not treat every reference task as shot-only; honor the declared environment or asset scope.
- Do not use one matching camera view as proof of valid depth, support, or connectivity.
- Do not lock the camera before the spatial hypothesis and cross-view blockout pass.
- Do not hand-correct generated stair steps or railing posts when the source path, ascent, landing,
  supported edge, or local frame is wrong. Repair the semantic skeleton and regenerate.
- Do not construct a doorway in one monolithic wall from top/left/right boxes. Use one wall host
  and a through-thickness Boolean cutter unless separate lintel/jamb construction is documented.
- Do not duplicate or move regular stair steps, windows, posts, louvers, or panels one by one.
  Keep one source and expose count, offset, endpoint, and fit policy through Array, linked
  instances, a curve system, or Geometry Nodes when fields are actually required.
- Do not approximate one continuous rail, pipe, cable, or molding run with overlapping straight
  segments. Use a continuous profile path or deliberate welded topology.
- Do not eyeball alignment when a semantic vertex, edge, face, grid, connector plane, or surface
  target exists. Use snapping or a persistent conformity modifier and verify the measured gap.
- Do not apply Displace to topology too sparse to represent the requested frequency, and do not
  use Bump as proof of geometric relief when silhouette, collision, or export geometry matters.
- Do not reject Boolean, Array, Curve, snapping, or Displace because direct primitive placement is
  easier to script. Reject a native generator only after recording the failed prerequisite or
  downstream conflict and the replacement construction route.
- Do not force a direct component when a node graph or inspected local node asset has a documented
  field, variation, coordination, scalability, or reusable-control advantage. Do not choose a node
  graph only because it looks advanced or is easier to generate from Python.
- Keep ordinary hard-surface and architectural cuts under an evaluated native Boolean Modifier.
  A graph may generate or distribute cutters but cannot replace Boolean ownership or cleanup.
- Do not use a Python loop to create regular final steps, posts, windows, panels, distant copies,
  or other count-driven fragments. Configure the native source and dependency instead.
- Do not allow a Specialist or Validator to mutate route, stage, retry, rollback, or deletion state.
- Do not reopen full reference/design analysis for a local construction failure. Record symptom,
  evidence, likely owner, affected part, and a proposed local rollback target.
- Do not replace hidden required space, a doorway, corridor, stair landing, or portal with a flat
  dark plane.
- Do not advance formal production while `reference_gate.json` contains a blocker that would
  change projection, connectivity, asset category, material class, simulation class, or an
  irreversible result. Record ordinary ambiguity as an assumption and test it in Blockout.
- Do not treat deep overlap as a seamless connection.
- Do not approve a material from Base Color or a single Noise Texture. Require physical scale,
  mapping direction, independent channel response, and neutral review lighting.
- Do not route static contained water to Fluid merely because it is water; use a closed liquid
  volume and material unless time-dependent flow changes the result.
- Do not memorize one universal modifier order. Choose order from the intended evaluated result.
- Do not hand-model a time-dependent physical effect when a suitable simulation exists.
- Do not assume an add-on or extension is installed. Probe it first.
- Do not use stale same-path images for validation. Save review renders with unique names.
- Do not report completion without `validation_report.json` for non-trivial work.
- When two topology rollback conditions are present, stop later-stage work, restore the last
  accepted task checkpoint, and return to Topology Construction or Structural Forms.
- Do not call a candidate complete while its governing visual gate is `WARN`, `FAIL`, or `REVIEW_REQUIRED`. Continue iterating or report the unresolved blocker explicitly.
- Do not replace visible `P0` phenomena with semantic proxies after Blockout: examples include emission cards standing in for projected light, generic noise standing in for a print, an authored wave standing in for required cloth simulation, or decorative solids standing in for surface decals.
- Do not improve compliance by degrading the user-facing result. Repair the method, narrow an irrelevant check, or preserve a documented exception instead.

## Scripts

- `scripts/probe_blender_capabilities.py`: inspect Blender RNA, operators, nodes, constraints, engines, devices, and enabled add-ons without mutating the scene.
- `scripts/search_official_blender_docs.py`: build and search versioned Blender Manual/API Sphinx inventories.
- `scripts/route_blender_task.py`: classify a request and create route, construction, and stage artifacts.
- `scripts/score_part_review.py`: apply bounded per-part stage scores through the Router state API.
- `scripts/apply_blockout_score_decision.py`: apply a reference Specialist's recorded R1 decision to
  Router-owned `stage_state.json`.
- `scripts/router_state.py`: shared ownership checks and atomic Router state mutations.
- `scripts/apply_validation_decision.py`: apply validator evidence to Router-owned rollback state.
- `scripts/validate_public_artifacts.py`: enforce artifact schemas and required fields.
- `scripts/run_route_evals.py`: run deterministic routing regression tests.
