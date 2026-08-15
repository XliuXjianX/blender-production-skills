# Geometry Nodes Layout Contract

Apply this layout to new or refactored Geometry Nodes groups. Distances use Blender node-editor pixels and describe node centers unless stated otherwise.

## Stages

Arrange frames left to right: `00 INPUT`, `10 DOMAIN`, `20 GENERATE`, `30 SAMPLE`, `40 VARIATION`, `50 INSTANCE`, `60 FINISH`, `90 OUTPUT`.

Keep the main geometry stream at `Y=0`. Place field controls in lanes around `Y=+220` and `Y=-240`; reserve a separate lower lane for animation or simulation controls. Start each stage about 260-420 px right of the prior stage. Give every frame at least 120 px internal padding.

## Connection Distance Rules

The studied asset corpus has a median direct center-to-center link distance of 200 px and a mean of 280 px. Use these as a baseline, not as a constraint on graph semantics.

| Relationship | Preferred distance | Action when exceeded |
|---|---:|---|
| Direct local dependency | 160-360 px | Keep a direct wire |
| Adjacent node edge clearance | 60-220 px | Increase stage spacing if labels overlap |
| Vertical field branch | 180-280 px | Keep it inside the same frame |
| Shared control crossing a stage | 220-420 px per reroute segment | Use one named reroute bus |
| Direct wire over 500 px | Avoid | Split a group or add a documented reroute bus |
| Wire over 900 px | Avoid | Make a functional sub-group or redesign the data flow |

Use reroutes as labeled bus terminals, not as decoration. Keep a reroute segment roughly 220-300 px where practical. Align socket rows and stage boundaries so cables travel predominantly horizontally or vertically.

## Interfaces And Attributes

Expose only artist-facing inputs, in a predictable order: geometry/source, density/spacing, dimensions, variation, seed, material, animation. Add units and min/max values to numeric inputs. Name temporary local fields with labels; name persistent attributes by their meaning and domain.

Capture local values before a short branch. Store named attributes only when a value must cross group boundaries, enter a simulation zone, or survive a topology change. Preserve `ID` before random animation and derive independent random streams from explicit seed offsets.

## Realization And Zones

Keep geometry instanced through distribution, transform, and material stages. Realize immediately before the first operation that demands mesh topology, and never realize merely to simplify a node graph.

Keep simulation input/output nodes on the same horizontal line and frame the whole zone. Put initial state, force/neighbor logic, and output processing in separate internal frames. Do not create an unexplained backward wire outside a zone.
