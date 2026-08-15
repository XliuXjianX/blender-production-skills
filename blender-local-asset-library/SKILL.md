---
name: blender-local-asset-library
description: Search and inspect the installed Blueish Blender Asset Library without mutating it. Use when a user asks for a local Blender asset, node preset, Blueish asset, Asset Browser entry, or named source, or when the Router has selected a node-centric/reusable Geometry Nodes, material, simulation, rigging, compositor, or NPR route with eligible local catalogs; return compatible, attributable candidates for the Router-approved workflow.
---

# Blender Local Asset Library

Use this Skill as a read-only discovery and compatibility layer. It does not own a production
stage, choose a route, create geometry, append data, change Asset Browser preferences, or replace
an already working Blender system.

## Authority And Scope

Follow `../blender-production-router/references/system-choice-contract.md` and
`../blender-production-router/references/production-protocol.md`.

- The Router alone owns `task_route.json`, `stage_state.json`, retry budgets, rollback, and pauses.
- This Skill discovers candidates and inspects their public interface and provenance.
- The Router-approved specialist owns whether a candidate is used and how it is integrated:
  - geometry graph: `blender-geometry-nodes-studio`;
  - repetition, source dependencies, and procedural route: `blender-procedural-systems`;
  - shader group: `blender-material-surfacing`;
  - physical or particle system: `blender-simulation-effects`;
  - rigging group: `blender-deformation-rigging`;
  - stylized engine-specific group: `blender-npr-eevee` or `blender-npr-cycles`.

The default library root is
`C:\Users\Administrator\Downloads\Assets-main\Assets-main\blender\assets`.
Set `BLENDER_LOCAL_ASSET_LIBRARY_ROOT` or pass `--root` when the library moves.

## Discovery Workflow

1. Use `scripts/search_local_asset_library.py` to search the JSON metadata by outcome, catalog,
   type, and Blender version. It reads files only.
   Run `scripts/check_local_asset_sources.py` once after a library update, or whenever a source
   fails to open, to distinguish a complete `.blend` from a Git LFS pointer file.
2. Reject candidates whose minimum Blender version exceeds the probed runtime.
   Also reject or explicitly defer candidates whose `source_files` are missing or still Git LFS
   pointer files; metadata presence is not proof that a source `.blend` can be opened.
   Once all currently available sources are present, build the inspected capability cache with
   `scripts/build_asset_capability_catalog.py`, then run
   `scripts/probe_local_asset_capabilities.py` against that catalog; read
   [capability-catalog.md](references/capability-catalog.md) for its semantics.
3. Compare the candidate with the Router's approved route using
   [asset-library-policy.md](references/asset-library-policy.md). Do not select a node asset just
   because it exists.
4. Read the candidate's `runtime_probe` before recommending it. A passed probe means it is
   callable in the current Blender runtime, not that it can be pasted blindly into a task scene.
   Respect its `integration_modes`: a `modifier` group can own a Nodes modifier; a
   `nested_group` is a field/helper group that belongs inside another GN graph; shader,
   compositor, object, material, and collection assets belong to their respective owner systems.
5. Inspect a short list of plausible source files in isolated background Blender with
   `scripts/inspect_local_asset_blend.py`. Inspect the actual node tree, public inputs, group type,
   dependencies, and complexity before any integration.
6. Hand the result to the owning specialist. A selected asset must remain explainable as a Blender
   system with named inputs and testable output, never an opaque black box.
6. When a candidate is intentionally used, let the owner add optional `asset_provenance` to the
   affected entry in `construction_graph.json`: library root, source `.blend`, asset name, catalog,
   inspected group identity, runtime version, owner Skill, integration mode, and reason it beats
   the rejected candidate.

Example search:

```powershell
python scripts/search_local_asset_library.py --query "curve mesh" --catalog "Geometry Node/Curve" --blender-version 5.2 --limit 8
```

Build then probe the runtime cache:

```powershell
python scripts/build_asset_capability_catalog.py `
  --blender "F:\SteamLibrary\steamapps\common\Blender\blender.exe" `
  --output "$env:USERPROFILE\.codex\cache\blender-production-suite\5.2\blueish_asset_capabilities.raw.json"

python scripts/probe_local_asset_capabilities.py `
  --catalog "$env:USERPROFILE\.codex\cache\blender-production-suite\5.2\blueish_asset_capabilities.raw.json" `
  --blender "F:\SteamLibrary\steamapps\common\Blender\blender.exe" `
  --output "$env:USERPROFILE\.codex\cache\blender-production-suite\5.2\blueish_asset_capabilities.json" `
  --strict
```

Example isolated inspection:

```powershell
& "F:\SteamLibrary\steamapps\common\Blender\blender.exe" --background --factory-startup "<source.blend>" --python scripts/inspect_local_asset_blend.py -- "<report.json>" --asset-name "<asset name>"
```

## System Choice

Use a local Geometry Nodes asset when it materially improves field-driven logic, adaptive or
context-aware variation, multiple coordinated source rules, reusable procedural topology,
large-scale instancing, or a node simulation. Keep simple Mirror, Bevel, Solidify, straightforward
Array, basic curve profile, and standard deform systems as direct native components when they give
the clearest control.

Normal architectural and hard-surface cuts stay native Boolean operations. A node asset can help
generate or position cutters only when it adds meaningful parameterized logic; it does not replace
the evaluated Boolean ownership of the host volume.

Shader, compositor, rigging, particle, and stylized assets are separate categories. Do not treat a
shader node group as Geometry Nodes, or treat a stylized asset as a physically validated PBR
material.

## Hard Rules

- Do not install extensions, write to the library, alter Asset Browser preferences, or save source `.blend` files.
- Do not auto-append or auto-link an asset based only on a keyword match.
- Do not route a task, change the selected method, consume a retry, or update stage state.
- Do not replace a small native system with a large graph without a recorded control or output benefit.
- Do not replace native Boolean Difference for ordinary host-volume openings or hard-surface cuts.
- Do not assume an asset is compatible until its Blender version and actual group interface have been checked.
- Do not import a material, compositor, rigging, or NPR group through the wrong specialist.

Read [asset-library-policy.md](references/asset-library-policy.md) before recommending a candidate.
