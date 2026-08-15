# Asset Library Findings

These observations came from a read-only study of `F:\Work Study\CG Design\blender\节点资产`: 14 Blender files, 32 Geometry Nodes groups, 5,953 nodes, and 7,372 links. Connection coordinates were measured after resolving nested Frame offsets.

## Measured Layout

- 3,076 reroute nodes and 75 Frame nodes appear in the corpus.
- Direct links: mean 280.07 px, median 200 px; median horizontal offset is 200 px and median vertical offset is 0 px.
- Links involving reroutes: mean 508.21 px, median 226.81 px.
- Only two links run backward after absolute Frame coordinates are resolved. The dominant convention is left-to-right flow.

The reference library proves that reroutes make very large graphs navigable, but its extremely reroute-heavy graphs are not a default to copy. Prefer fewer, named buses and visible stage frames in new work.

## Reusable Architectural Patterns

### Functional sub-groups plus an assembly group

`小草.blend` keeps individual grass types in separate 78-186 node groups, then uses a compact `草` assembly group to combine four sub-groups. `数据流.blend` splits generation, sampling, calculation, transfer, curvature sampling, and port extraction into nine groups; its `数据流` assembly group connects seven functional groups.

Use this pattern for assets with independent behaviors. Keep each functional group focused on one contract and let the assembly group expose only the artist controls.

### Data is a first-class stream

The data-flow and neural-network assets heavily use `Named Attribute`, `Store Named Attribute`, `Sample Index`, comparison, math, and switch nodes. Their useful lesson is to define a data contract early, pass it through semantic functional groups, and delete or replace it deliberately. Do not leave anonymous long-distance field wires.

### Instancing stays late

The grass, text, data-flow, neural-network, and fish assets all use `Instance on Points`; realization is limited to selected downstream groups. Preserve this separation between distribution and real mesh operations.

### Small effects stay linear

The outline group has 16 nodes and 18 links. It uses a direct input -> material/position/extrude -> join -> switch pattern without reroutes or nested groups. Use a similarly direct graph for small effects rather than over-modularizing them.

## Do Not Copy Blindly

Some complex reference graphs use thousands of reroutes, sparse or absent Frames, and multi-thousand-pixel links. Retain their functional decomposition and stable data-flow ideas, but refactor new work into visible stages with the distance budget from `graph-layout-contract.md`.
