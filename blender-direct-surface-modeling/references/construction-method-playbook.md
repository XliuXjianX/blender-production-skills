# Construction Method Playbook

## Contents

1. Construction reasoning
2. Shape grammar classification
3. Native-generator comparison
4. Architectural openings
5. Stairs and repeated elevation
6. Curve-profile construction
7. Snapping and persistent conformity
8. Geometric displacement
9. Modular environments
10. Exceptions and validation
11. Official sources and study index

## 1. Construction Reasoning

Model the object's construction logic, not the visible fragments of its silhouette. Before adding
a primitive, identify which source owns each dimension and which operation should propagate later
changes.

Prefer the route with:

- the fewest independent parameter owners;
- dimensions expressed in the user's semantic terms;
- reversible edits while design is uncertain;
- stable downstream topology, UV, deformation, simulation, and export behavior;
- visible evidence that can be validated from more than one view.

A primitive is legitimate as a base volume, Boolean cutter, repeated source module, collision
proxy, or genuinely separate manufactured part. A pile of primitives is not automatically wrong;
it fails when the pieces are only a manual approximation of one continuous or parameterized form.

## 2. Shape Grammar Classification

Classify every major form before choosing a tool:

| Shape grammar | Default construction family |
| --- | --- |
| Negative space cut through a solid | closed host volume plus Boolean Difference cutter |
| Addition of volumes into one static body | Boolean Union plus cleanup, remesh, or reconstructed topology |
| Fixed-vector repetition | one source plus Array or linked instances |
| Repetition along a path | Array plus Curve, curve instances, or Geometry Nodes |
| Constant profile along a path | Bezier/NURBS path plus bevel depth or bevel object |
| Revolved profile | Spin or Screw |
| Regular bend/twist/taper | Simple Deform |
| Persistent surface conformity | Shrinkwrap or Surface Deform |
| One-time exact placement | vertex, edge, face, grid, or increment snapping |
| Height-field geometric relief | subdivided mesh plus Displace, Multires, or true shader displacement |
| Unique designed silhouette | direct topology, subdivision cage, Boolean block-in, sculpt, or remesh |
| Time-dependent physical response | the corresponding simulation system |

Do not decide from tool familiarity. Decide from the relationship between source parameters and
the evaluated result.

## 3. Native-Generator Comparison

For each recognized grammar, compare the native generator against manual assembly before formal
modeling. Keep the comparison short for obvious cases.

Record:

- `shape_grammar`;
- `parameter_owners`;
- `primary_generator`;
- `comparison_methods`;
- `application_state`;
- `downstream_requirements`;
- `rejected_shortcuts`.

Reject manual assembly when all visible members merely reconstruct an operation already owned by
one editable generator. Examples include hand-duplicated regular steps, three boxes imitating a
single wall with a doorway, separate cylinders imitating one swept pipe, and individually moved
posts imitating a path distribution.

Manual construction remains valid when the pieces are physically separate, irregular by design,
need independent motion/material/export ownership, or when the generator produces worse topology
for the declared downstream use. Document that reason.

## 4. Architectural Openings

For a door, window, archway, wall niche, service slot, or portal cut into one monolithic wall:

1. Build one closed wall or shell volume with real thickness.
2. Create a named closed cutter that crosses the entire target thickness with non-coplanar margin.
3. Own opening width, height, sill, head, reveal depth, arch radius, and alignment on the cutter.
4. Add Boolean Difference to the host and keep the cutter editable while dimensions are changing.
5. Build frame, trim, glass, and door leaf as separate manufactured parts only after the opening
   and reveal pass.
6. Validate the evaluated opening, interior reveal faces, wall thickness, slivers, normals,
   shading, and frame clearances.

Do not construct a monolithic wall opening from independent top, left, and right cubes. That route
is acceptable only when the reference or construction brief identifies separate lintel, jamb,
stud, masonry, or modular wall members. In that case, classify and join them through the assembly
graph instead of pretending they are one solid.

For an open sheet or an opening whose edge flow must subdivide/deform, compare direct inset/extrude
or Boolean-to-retopology. Boolean is a volume-logic default, not a commandment to keep poor
evaluated topology.

## 5. Stairs And Repeated Elevation

Treat a stair as a directional structure, not a bag of steps.

First solve:

- lower and upper landing anchors;
- local forward, width, and up axes;
- total rise and total run;
- step count;
- per-step rise and run;
- tread depth, riser policy, nosing, clear width, and endpoint ownership;
- flight/landing graph for L, U, spiral, or split stairs.

For a regular straight flight, the default editable generator is one formal tread or step module
plus an Array using a constant offset that contains both run and rise. Keep relative offset off
when exact architectural dimensions own the flight. Confirm that the final generated level meets
the landing; do not patch the last step.

For bounded-camera forced perspective, an Object Offset may add cumulative taper while Array remains
the count/run/rise source of truth. Keep the taper controller explicit, test the flight from side
and top views, and disable taper for free-camera or measured architectural deliverables.

Choose another route when justified:

- use a profile extrusion, Boolean, or direct mesh for a monolithic concrete stair body;
- use separate flights connected by explicit landings for L/U stairs;
- use a curve or polar generator for spiral stairs;
- use Geometry Nodes when multiple dependent systems, exclusions, or reusable parameterized
  variants require fields;
- keep tread, riser, stringer, support, and railing ownership physically meaningful.

Generate rail paths from the accepted flight/landing graph. Distribute posts by distance or arc
length and build the rail as a continuous curve profile. If direction is wrong, repair axes,
anchor order, or path. Never move generated steps or posts one by one.

## 6. Curve-Profile Construction

Use a Bezier or NURBS path with bevel depth or a separate bevel object for rails, pipes, cables,
hoses, trim, molding, frames, and other constant-profile sweeps.

Declare:

- start/end point order and path direction;
- path dimensions and local up/reference frame;
- profile object, profile scale, and profile orientation;
- path resolution separately from bevel/profile resolution;
- cyclic state, endpoint caps, tilt, radius, and conversion policy.

Use a Curve modifier when an existing mesh must deform along the path. Use curve geometry when the
path itself should generate the final profile. Use Array plus Curve when distinct repeated modules
must follow the path. Convert to mesh only when direct topology, UV, export, Boolean, or simulation
requires evaluated vertices.

Inspect inflections, near-vertical tangents, cyclic seams, tight-radius self-intersection, profile
twist, endpoint fit, and final-resolution faceting.

## 7. Snapping And Persistent Conformity

Use snapping for one-time construction placement and Shrinkwrap/Surface Deform for persistent
relationships.

Before snapping, declare:

- source selection and active element;
- target object or allowed target collection;
- snap element: increment, grid, vertex, edge, face, volume, or edge center/perpendicular;
- snap base and transform pivot;
- transform orientation and constrained axes;
- rotation alignment, backface policy, offset, and whether individual elements project.

After placement, measure the intended contact/gap and restore tool settings if they belong to the
user's protected workspace. Do not rely on viewport appearance as proof of alignment. Do not use
face snapping to fake an attachment that still needs a recess, fastener, weld, or constraint.

For modular environments, establish grid unit, module origin, bounding dimensions, connector
plane, and pivot convention before duplication. Snap source modules or linked instances; do not
accumulate floating-point drift through repeated manual moves.

## 8. Geometric Displacement

Choose relief scale first:

- microscopic response: Bump or Normal;
- render-time surface displacement without editable mesh ownership: material displacement when
  the engine and subdivision mode support it;
- editable or silhouette-affecting relief: sufficient mesh density plus Displace;
- irregular hero damage: sculpt or Multires;
- field-driven terrain/system: Geometry Nodes when native Displace lacks required control.

For Displace Modifier:

1. Establish real scale and maximum allowed displacement.
2. Provide enough source topology before Displace; subdivision order is part of the design.
3. Name the texture and choose UV, object, global, local, or generated coordinates intentionally.
4. Record coordinate object, direction, midlevel, strength, vertex group, and stack order.
5. Test low strength first and inspect silhouette, self-intersection, wall thickness, and UV stretch.
6. Keep micro bump separate from macro geometric relief.

Do not add strength to compensate for insufficient texture contrast or topology. Do not claim
shader bump as geometric relief when the silhouette or collision must change.

## 9. Modular Environments

Use a small kit of dimensionally compatible source modules rather than unique copies:

- define a grid and module increments;
- place origins on meaningful connector planes;
- use linked duplicates or collection instances for exact repeated assets;
- use Array for one-dimensional regular runs;
- use Geometry Nodes for rule-driven multi-source distribution;
- use Boolean cutter arrays for repeated openings when one host owns the wall volume;
- preserve unique end caps, corners, transitions, and damaged variants as explicit modules.

Validate module seams, normals, scale, UV density, end conditions, collision, object count, and
whether a changed source updates every dependent occurrence.

## 10. Exceptions And Validation

Do not make Boolean, Array, Curve, snapping, or Displace universal. Reject the default when:

- source objects are physically separate construction members;
- repetition is intentionally irregular;
- a unique silhouette needs direct control;
- deformation/export requires clean loops the generator cannot provide;
- a simulation or constraint owns the result;
- the evaluated generator creates unacceptable shading, topology, or performance.

The exception must name the failed prerequisite and the replacement route. Difficulty or habit is
not a sufficient reason.

At each stage, validate source objects and evaluated output separately. The presence of a modifier
does not prove that it controls the intended dimensions or creates a usable result.

Record the native component contract for every generator: native system, source objects, semantic
inputs, generated dependents, Python code role, application policy, and component evidence.

## 11. Official Sources And Study Index

Official Blender 5.2 sources:

- Boolean Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/booleans.html
- Boolean Python API: https://docs.blender.org/api/current/bpy.types.BooleanModifier.html
- Array Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/array.html
- Array constant offset API: https://docs.blender.org/api/current/bpy.types.ArrayModifier.html#bpy.types.ArrayModifier.constant_offset_displace
- Curve geometry and bevel object: https://docs.blender.org/manual/en/5.2/modeling/curves/properties/geometry.html
- Curve bevel object API: https://docs.blender.org/api/current/bpy.types.Curve.html#bpy.types.Curve.bevel_object
- 3D View snapping: https://docs.blender.org/manual/en/5.2/editors/3dview/controls/snapping.html
- Snapping API: https://docs.blender.org/api/current/bpy.types.ToolSettings.html#bpy.types.ToolSettings.snap_elements
- Displace Modifier: https://docs.blender.org/manual/en/5.2/modeling/modifiers/deform/displace.html
- Displace API: https://docs.blender.org/api/current/bpy.types.DisplaceModifier.html

Representative tutorial study leads, retained as non-normative discovery metadata:

- Josh Gambrell Boolean workflow: YouTube `lCA1AFEQ_z4`, `lxtHuz6luJM`, `YhAWll3mLtU`.
- Door/window Boolean construction: YouTube `kZD8sSX7NtU`, `fpoUMsmzpyM`.
- Array-driven stairs: YouTube `duhkXgBVjmE`, `alW-aWSu1wA`.
- Blender snapping: YouTube `0p06F1LzTjQ`.
- Array plus Curve: YouTube `DDpedZobA5Q`.
- Displace workflows: YouTube `XBdNZIs1U8w`, `EDVXIwWeoD0`.
- From-zero chair workflow: YouTube `Hf2esGA7vCc`, `px0sJElIUGc`, `BgY3QMXQYLI`.
- Modular environment workflows: YouTube `oRv2xCXkmLA`, `77xPHfzciiY`, `tbYftU3V8JU`.
- Fast environment construction studies: YouTube `v_ikG-u_6r0`, `t_c58ryJ-Sw`, `JjnyapZ_P-g`.

Tutorial metadata is a discovery index, not evidence for an API contract. Recheck exact operations
against the installed Blender version and official documentation before encoding them in scripts.
