# Assembly Production

## Part Boundary Decision

Keep a part separate only for a real reason: independent manufacture, motion, replacement,
transparent/material ownership, modifier ownership, instancing, export, rigging, or a visible seam.
Color blocks and modeling difficulty are not part boundaries.

For each interface, record:

- host and attached part;
- interface type;
- mating surfaces;
- insertion depth or contact region;
- clearance and tolerance source;
- wall thickness around the receiver;
- mounting, fastening, hinge, seal, or constraint;
- bevel/radius compatibility;
- visible seam policy;
- collision role and tested state.

## Interface Routes

### Mechanical Seam

Keep both parts independent. Build real gap, wall thickness, mating surfaces, and compatible edge
radii. Prevent coplanar flicker and unexplained penetration.

### Embedded Component

Create a recess or socket in the host, a matching component depth, a contact surface, and a visible
gap policy. A box pushed through the host fails.

### Constraint Connection

Define pivot, axes, limits, hierarchy, rest state, driven properties, and collision clearance.
Test the complete motion range.

### Physical Contact

Keep objects independent. Use collision, rigid bodies, cloth collision, or constraints when time
and force matter. Never weld vertices merely to represent contact.

### Instanced Element

Keep one source of truth. Record count, spacing, orientation, variation, realization policy, and
whether each instance remains a separate manufactured item.

### Topology Fusion

Route to direct surface modeling. Require shared boundary topology or a cleaned fused volume, not
Join Objects or overlap.

## Scene Organization

Use semantic collections and stable names. Controls, cutters, collision proxies, source assets,
generated outputs, and export objects must remain distinguishable. Hidden helper geometry must have
an owner and lifecycle; unexplained hidden primitives are defects.

## Modular Placement And Snapping

- Define grid increment, module dimensions, origin, pivot, forward/up axes, and connector planes.
- Use linked duplicates or collection instances when occurrences share one asset definition.
- Use Array for a regular one-dimensional run and Geometry Nodes only for field/rule-driven layouts.
- Configure snapping by target, element, snap base, transform orientation, constrained axes,
  rotation alignment, backface policy, and offset; restore protected user tool settings afterward.
- Measure seam gap, overlap, and orientation after snapping. A visually close placement is not
  evidence of an interface.
- Use Shrinkwrap/Surface Deform instead of snapping when the relationship must remain live.

## Review

Review exploded and assembled states where useful. Report object count, mesh-island count, parent
hierarchy, constraints, collection membership, interfaces, gaps, collisions, and intentional hidden
overlap. A visually plausible hero view does not waive assembly evidence.
