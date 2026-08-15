# Topology-First Blender Production Contract

## Progressive Analysis

Before any scene mutation, complete the minimum viable portion of `production_analysis.json`:

- deliverable/completion scope and protected scene scope;
- major parts or spatial regions;
- scale strategy;
- provisional construction route;
- critical blockers that could make a reversible Blockout unsafe.

Allow at most two automatic analysis reviews. When the minimum fields are known and no critical
blocker remains, set the analysis to `provisional` and permit only task-owned, reversible Blockout.
Record ordinary uncertainty as testable assumptions instead of keeping the task in analysis.

Before formal topology or any destructive/system work, complete:

- deliverable and real scale;
- reference observations, unknowns, and confidence;
- primary silhouette and proportions;
- spatial regions, supports, directions, and traversal;
- five form levels;
- Part Graph and construction method for every buildable part;
- lighting evidence and first-pass hypothesis;
- material classes, mapping direction, and physical scale;
- simulation, deformation, procedural, and export requirements.

Analysis and Blender execution remain separate states, but Blockout is an analysis instrument.
`execution_allowed` may become true with `execution_scope=reversible_blockout` after minimum
analysis. Require `execution_scope=formal_production`, complete affected-part analysis, and an
approved Part Graph before formal topology, systems, surfacing, cache, export, or destructive work.

## Five Form Levels

1. `PRIMARY`: overall dimensions, mass, silhouette, and major negative space.
2. `STRUCTURAL`: major cuts, slopes, frames, cavities, protrusions, and load-bearing relationships.
3. `TRANSITION`: topology connecting structures, radii, blends, corner flow, shell turns, and
   manufactured edge language.
4. `FUNCTIONAL`: handles, pivots, mounts, buttons, joints, openings, brackets, and interfaces.
5. `DETAIL`: fasteners, micro seams, markings, micro bevels, wear, and small surface damage.

Do not create Functional or Detail parts before Primary, Structural, and Transition gates pass.
The absence of middle-scale Structural and Transition forms is a blocking modeling defect.

## Topology And Assembly Are Different

- Topology construction controls shared vertices, edges, faces, loops, boundaries, and surfaces.
- Assembly controls independent objects, seams, mating surfaces, pivots, hierarchy, constraints,
  collections, and instances.
- Join is not Weld. Overlap is not Connection. Smooth Shading is not Bevel.

Use explicit combination levels:

- `A_VISUAL_GROUPING` for Blockout or already independent objects;
- `B_OBJECT_JOIN` for one container with intentional islands;
- `C_PHYSICAL_ASSEMBLY` for real independent parts;
- `D_TOPOLOGY_FUSION` for one continuous shell or volume.

## Blockout Conversion

Blockout primitives are temporary evidence of proportion. After Blockout approval:

1. approve the Part Graph;
2. mark every proxy as replace, convert, or legitimate independent primitive;
3. build continuous primary topology;
4. remove or archive replaced proxies;
5. validate connected components and wireframe;
6. only then build Structural and Transition forms.

No complex model may enter Functional Parts while its main shell is still represented by
overlapping blockout objects.

## Construction Method Requirement

Each major part names one primary method: box/polygon modeling, profile extrusion, inset/extrude,
section loops and Bridge, Boolean plus cleanup, Screw/Spin, curve sweep, subdivision cage,
sculpt/remesh plus retopology, modular assembly, or justified Geometry Nodes generation.
"Create a cube" is not a construction method.

## Real Bevel Contract

Classify edges as Primary, Secondary, Micro, or Sharp. Use Edit/BMesh Bevel, evaluated Bevel
Modifier geometry, subdivision support loops, or controlled crease. Shade Smooth, Weighted Normal,
material highlights, and added corner pieces do not create a bevel. Require evaluated wireframe
evidence and scale-aware widths.

## Review Evidence

At every structural gate, preserve unique front, side, top, hero three-quarter clay, and wireframe
views. Use neutral MatCap and moving reflective light for curved or beveled hero surfaces.

## Automatic Topology Rollback

Count these conditions after each modeling transaction:

- one continuous shell uses several overlapping primitives;
- unexplained mesh islands remain;
- visible intersections lack a seam or fusion route;
- Primary blocks and tiny details exist but Structural/Transition forms are missing;
- smooth normals hide primitive intersections;
- required bevels produce no transition geometry;
- Boolean results lack cleanup evidence;
- every edge uses one bevel width;
- Join Objects is treated as fusion;
- wireframe does not represent the visible structure;
- Functional/Detail objects exist before earlier gates pass;
- material or lighting is used to conceal geometry failure.

One condition fails the affected part. Two conditions stop later-stage work and return the task to
Topology Construction or Structural Forms. Preserve the last accepted checkpoint and replace only
task-owned failed data.
