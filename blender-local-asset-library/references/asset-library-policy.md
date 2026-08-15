# Local Blender Asset Library Policy

## Purpose

The Blueish library is a versioned source of reusable node assets. It is an optional candidate
source, not a second Router, a replacement for Blender's built-in systems, or a license to append
opaque graphs.

## Candidate Selection

Use a library candidate only after the Router has selected a construction class and the owner has
compared it with direct Blender components. A candidate is eligible when all of the following hold:

1. Its catalog and node-tree type match the task.
2. Its declared minimum Blender version is no newer than the probed runtime.
3. Its public interface exposes the controls needed by the task.
4. Its `runtime_probe.status` is `passed` in the current Blender runtime, and its recorded
   integration mode matches the intended use.
5. Its graph improves a measurable need: fields, adaptive variation, coordinated sources,
   reusability, scalable instances, node simulation, shader reuse, compositor effect, rigging
   utility, or approved stylization.
6. Its source dependencies and performance cost are acceptable.

Reject it when a direct built-in component has a smaller semantic control surface and equal output.
Examples: a normal door cut remains `Boolean Difference`; a straight flight remains an `Array`;
a simple rail remains a curve bevel; an ordinary edge round remains `Bevel`.

Treat a source that is missing, a Git LFS pointer, or opens with a newer-Blender warning as
unavailable or forward-compatibility-uncertain. Do not use its metadata alone as evidence that the
graph can be safely integrated in the current runtime.

## Ownership Matrix

| Asset category | Integration owner | This Skill supplies |
| --- | --- | --- |
| Geometry Node | Geometry Nodes Studio | metadata and source-tree inspection |
| Geometry Node used for repetition | Procedural Systems plus Geometry Nodes Studio | source/dependency evidence |
| Material or Material Function | Material Surfacing | shader-group inspection |
| Particle System or VFX motion | Simulation Effects | runtime/version evidence |
| Rigging System | Deformation and Rigging | group/interface evidence |
| Stylized or compositor asset | NPR owner chosen by render engine | engine compatibility evidence |

## Provenance Record

When an owner intentionally imports or links a candidate, attach this optional block to the affected
`construction_graph.json` part. Do not use a provenance record to imply that an asset passed
geometry, material, physics, or visual validation.

```json
{
  "asset_provenance": {
    "library": "Blueish Assets",
    "library_root": "C:\\Users\\Administrator\\Downloads\\Assets-main\\Assets-main\\blender\\assets",
    "source_blend": "GN/geometry_nodes_category_layout.blend",
    "asset_name": "Example Group",
    "catalog": "Geometry Node/Curve",
    "node_tree_type": "GeometryNodeTree",
    "minimum_blender_version": "5.2",
    "inspected_group": "Example Group",
    "owner_skill": "blender-geometry-nodes-studio",
    "integration_mode": "append_copy|link|rebuild_from_inspection",
    "selection_reason": "Needs attribute-aware curve variation that a direct curve bevel cannot express",
    "rejected_alternative": "Curve bevel alone lacks per-point rules"
  }
}
```

## Read-Only Inspection

`search_local_asset_library.py` reads the library's metadata indexes. `inspect_local_asset_blend.py`
runs only in background Blender and writes a report outside the source library. Neither script saves
the source file or changes the user's active Blender project.
