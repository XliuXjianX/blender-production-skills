# Validation Gates

## Scale-Derived Thresholds

Use the evaluated bounding-box diagonal `D` as the default scale:

- duplicate-position tolerance: `max(D * 1e-6, 1e-7 m)`;
- continuous-boundary gap warning: `D * 1e-4`;
- continuous-boundary gap failure: `D * 5e-4`;
- independent-part clearance thresholds: supplied by the construction graph or measured reference;
- aspect-ratio warning: configurable, default `> 12`;
- non-uniform scale warning: axis ratio difference `> 1e-4`.

These are defaults, not universal manufacturing tolerances.

## Mesh Legality

Evaluate the original mesh and, when relevant, the modifier-evaluated mesh:

- vertices, edges, polygons;
- zero-length edges and zero-area faces;
- boundary and non-manifold edges;
- loose vertices/edges;
- duplicate positions;
- inverted or inconsistent normals where determinable;
- invalid transform scale.

Open cloth, planes, and intentionally open shells must declare that boundary edges are allowed.

When a construction-graph part declares `requirements`, also validate applicable semantic
properties:

- `single_component`: the mesh contains one connected component;
- `closed_volume`: no boundary, wire, or non-manifold edges;
- `min_smooth_ratio`: visible curved faces meet the declared smooth-face coverage;
- `material_class`: the node and geometry checks for that class pass;
- `min_bbox_volume_ratio`: reject implausibly thin stand-ins for a declared volume.

For a genuinely non-geometric observation, allow:

```json
{
  "role": "presentation",
  "requirements": {"validation_mode": "visual_only"},
  "evidence": ["absolute/or/task-relative/existing-review.png"]
}
```

Restrict this mode to presentation, lighting-region, camera-effect, or helper roles. Missing
evidence or using `visual_only` to bypass a buildable object is a failure. Architectural negative
space is validated through `spatial_hypothesis.json`, surrounding geometry, and connected regions;
it is not a visual-only construction part.

## Surface Quality

- Compare edge-length distribution and face aspect ratios.
- Inspect adjacent-face normal angles at intended smooth regions.
- Compare symmetry pairs where the graph declares symmetry.
- Render or capture MatCap and reflective review views for curved surfaces.
- Treat image review as evidence, not the only test.
- Report smooth and flat face counts. A Bevel modifier does not satisfy smooth shading.
- For visible tubular or revolved forms, report radial segments, bend steps, connected
  components, and reflective highlight evidence when supplied by the construction graph.

## Relationship Quality

Validate each construction-graph relationship:

- continuous surface: shared/welded boundary or verified reconstructed topology;
- Boolean fused: one intended volume and no unexplained internal surface;
- mechanical seam: documented gap and no accidental overlap;
- embedded component: receiving interface and intended depth;
- physical contact: independent objects and appropriate collider roles;
- instanced element: source/instance relationship and count;
- intentionally independent: visible separation or documented occlusion.

`continuous_surface` requires the mapped parts to resolve to one mesh object with one connected
component. Object overlap is never sufficient. `embedded_component` and
`constraint_connection` may set `require_overlap: true`; otherwise absence of measurable
contact is at least a warning. `physical_contact` may declare `max_gap` in scene units.

## Formal Topology And Stage Quality

After Blockout, require each major part to map to a real final object and report:

- Blockout replacement or conversion decision;
- semantic construction operations rather than primitive creation alone;
- base and evaluated connected-component counts;
- real bevel method and evaluated geometry where edge classes exist;
- Boolean operand/result cleanup evidence where Boolean participates;
- assembly interfaces and relationship validation;
- distinct front, side, top, hero clay, and wireframe files.

Treat `Join Objects`, Join Geometry, parenting, collections, smooth shading, Weighted Normal,
materials, and lighting as incapable of proving topology fusion or bevel geometry. Unclassified
visible intersections become failures at Topology Construction and later.

When a construction grammar is declared, validate the generator and its parameter ownership:

- monolithic architectural opening: one host volume, through-thickness cutter, evaluated reveal,
  no three-piece wall substitute, and Boolean cleanup evidence;
- regular stair: start/end anchors, rise/run/count, exact Array offset, landing endpoint, and no
  individually patched generated step;
- repeated module: one source of truth, count/fit/offset policy, dependent update behavior, and
  controlled object count;
- curve profile: continuous path, profile ownership, direction/frame, resolution, endpoint fit,
  twist, and evaluated continuity;
- snapped placement: target and snap mode declaration plus measured contact/gap and orientation;
- displaced surface: source density, coordinates, direction, midlevel, strength, stack order,
  silhouette/self-intersection, and evaluated vertex movement.

One rollback condition fails the affected part. Two distinct conditions require deterministic
rollback: use `structural_forms` when middle-scale structure or transition order failed; otherwise
use `topology_construction`. Reopen dependent gates and prohibit Systems, Surfacing, Lighting, and
Final work until the repaired evidence passes.

## Liquid Volume Quality

For a part whose `material_class` is `liquid`, require:

- a closed non-zero-volume mesh and one connected component;
- sufficient bounding-box volume ratio for the declared contained volume;
- at least one Principled surface with plausible IOR and transmission;
- a Volume Absorption node connected to a material output when visible thickness matters;
- container conformity, waterline, and interaction evidence supplied by the task graph.

A plane, open surface, or thin rounded slab fails regardless of its reflective appearance.

## Material Surface Quality

For material-sensitive hero parts require:

- declared substrate, variant, manufacturing state, and layer stack;
- physical texture scale and coordinate route;
- UV maps for directional image materials and an explicit tangent for anisotropy when required;
- Base Color in an appropriate color data space and roughness, metallic, normal, height, masks,
  and displacement treated as non-color data;
- independent evidence for color, roughness, normal/bump, and displacement rather than one shared
  unmodified noise signal;
- diffuse, grazing-reflection, and production-light reviews with unique filenames.

For bare metal, require conductor response, suitable roughness, valid normals/bevels, and
manufacturing-direction evidence for brushing/anisotropy. Painted, oxidized, rusty, dirty, and wet
layers are dielectric and need causal masks.

For wood boards, require real grain scale, long-grain direction, end-grain policy, board-to-board
variation, roughness/relief hierarchy, and geometry for silhouette-scale breakage. Wet wood needs
pooling/contact logic, not uniform black gloss.

Run `blender-material-surfacing/scripts/audit_materials.py` and preserve its raw report. A clean
node audit does not replace visual material review.

## Simulation Stability

Sample the test range and record:

- object bounds;
- displacement and velocity outliers;
- penetration evidence where measurable;
- cache state;
- participants with missing roles;
- topology or modifier changes invalidating a cache.

## Scene Safety

Compare pre/post snapshots:

- protected object existence and data identity;
- transforms and visibility;
- collection membership;
- World and active camera;
- material assignments;
- file path and render output path.

Any unexplained protected-state change is a failure.
