# Directional Structure Reconstruction And Recovery

Use this protocol for stairs, ramps, escalators, curved railings, handrails, fences, pipes, tracks,
bridges, cables, and any structure whose correctness depends on ordered endpoints, path direction,
elevation, handedness, or a stable local frame.

## Why These Structures Fail

A collection of steps, posts, or pipe segments can resemble the reference from one angle while
being spatially wrong. Common root causes are reversed endpoints, an incorrect ascending direction,
a curve with unstable tilt, a railing attached to the wrong edge, an impossible landing, or camera
movement used to hide invalid geometry. Do not repair these failures by moving generated pieces.
Repair the semantic skeleton and regenerate all dependent geometry.

## Semantic Skeleton

Before creating renderable geometry, add an entry to `spatial_hypothesis.json` under
`directional_structures`:

```json
{
  "id": "stair_a",
  "type": "stair_system",
  "start_anchor": "lower_landing_a",
  "end_anchor": "upper_landing_b",
  "direction_vector": [0.0, 1.0, 0.4],
  "up_axis": "Z",
  "control_path": [[0, 0, 0], [0, 5, 2.8]],
  "construction_route": "flight_mesh_plus_derived_handrail",
  "step_count": 16,
  "rise": 0.175,
  "run": 0.3125,
  "ascending_from": "lower_landing_a",
  "ascending_to": "upper_landing_b",
  "landing_anchors": ["lower_landing_a", "upper_landing_b"],
  "anchor_object_names": {"start": "ANCHOR_LOWER", "end": "ANCHOR_UPPER"},
  "control_object_names": ["CTRL_STAIR_FLIGHT_A"],
  "generated_object_names": ["STAIR_A", "HANDRAIL_A"],
  "validation": ["camera", "top", "side", "endpoint_contact", "clearance"]
}
```

Use stable named anchors or explicit world-space coordinates. Record the ordered control path,
not just a curve object name. Keep `start_anchor` and `end_anchor` semantically meaningful so a
reversed path is detectable.

## Stair And Ramp Solve

1. Mark lower and upper landing planes and their elevations.
2. Derive the horizontal run vector separately from the vertical rise. State which endpoint is
   lower and which is upper.
3. Solve step count from the allowed riser range, then recompute exact riser and tread depth so the
   final step lands exactly on the upper platform. Do not accumulate rounded per-step error.
4. For L- or U-shaped stairs, represent each flight and landing as a separate path segment in one
   connected graph. Record turn direction and handedness.
5. Build the structural stair or tread system from this solved flight. Use direct mesh construction
   for unique stairs, Array for a straight regular flight, or Geometry Nodes only when several
   flights, variants, or controlled regeneration justify it.
6. Derive stringers, side walls, handrails, and balusters from the accepted flight and supported
   edges. Do not estimate each subsystem independently.
7. Validate the lower contact, upper landing, head clearance, walking width, rail side, and
   ascending direction in camera, top, and side views.

A stair that rises the wrong way, terminates inside a wall, misses its landing, or has a handrail
on the wrong traversable edge is a critical semantic failure.

## Curved Railing And Handrail Solve

1. Identify the real supported edge: platform perimeter, stair nosing line, bridge edge, balcony
   boundary, or wall path.
2. Create one ordered centerline curve with named start/end anchors. Inspect point order, tangent,
   normal/tilt, cyclic state, bend radius, and corner intent before generating geometry.
3. Use a bevel profile or Curve-to-Mesh for a continuous rail. Use a Curve modifier only when an
   existing source mesh must deform along the path.
4. Derive baluster positions by arc length, not by object count guessed in screen space. Compute a
   stable frame from path tangent and the declared up axis; explicitly handle near-vertical
   tangents instead of allowing frame flips.
5. Project each support to its actual floor, stair, or platform contact and reject unsupported or
   penetrating posts. Preserve designed gaps at landings, gates, and wall returns.
6. For tight corners, solve corner joins and post spacing before adding small fittings. Do not hide
   discontinuities with oversized sleeves.
7. Validate rail continuity, supported-edge ownership, start/end contacts, height, post spacing,
   bend direction, and curve twist in camera, top, side, and grazing-highlight views.

A railing that bends to the wrong side, follows the wrong boundary, reverses direction, floats,
or twists its profile is a critical semantic failure.

## Failure Recovery

When a directional structure fails:

1. Freeze materials and downstream detail.
2. Preserve a unique camera render plus top and side evidence.
3. Identify whether the root cause is endpoint order, world axis, curve frame, elevation, landing
   topology, supported-edge choice, or camera projection.
4. Keep reference anchors and the last accepted checkpoint.
5. Remove or quarantine only the task-owned generated output for the failed structure.
6. Correct the semantic skeleton.
7. Regenerate all dependent geometry from the corrected skeleton.
8. Re-score the complete R1 blockout. Do not count a re-render of unchanged geometry as a rebuild.

Keep the user's camera unchanged during model-body recovery. Camera and crop are reviewed
separately and contribute no points to the emergency model score.

Do not patch individual steps, posts, or segments after the generator's path is known to be wrong.
That preserves the error and destroys editability.

## R1 Critical-Failure Policy

Set `critical_directional_failure` when any P0 stair/rail/path has the wrong traversal direction,
wrong bend side, disconnected landing, reversed endpoint ownership, unsupported contact, or
uncontrolled profile twist. The blockout score is then capped at `39/100` even if other image
regions match.

The first score below 40 invalidates the current blockout hypothesis and requires a full R1 rebuild.
The second consecutive below-40 score after a declared rebuild stops all scene mutation and asks
the user whether the exact task-owned project paths should be deleted. Never delete automatically.
