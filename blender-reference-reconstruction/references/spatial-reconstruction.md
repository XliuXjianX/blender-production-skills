# Spatial Reconstruction From A Single Reference

## Core Principle

Do not begin by naming objects. Build the smallest three-dimensional hypothesis that explains
the image's projection, occlusion, contact, negative space, elevation changes, and visible light
transport.

A reference image is evidence. It does not make the deliverable shot-only. First classify the
deliverable as a fixed shot, reusable asset, navigable environment, or animated environment.

## Reasoning Order

Use this order and stop at the first unresolved structural question:

1. Where is the camera located: inside, outside, at a threshold, near a wall, high, or low?
2. What spatial region contains the camera?
3. What are the depth, lateral, vertical, and diagonal axes?
4. Which regions are foreground, middle, background, occluded, or continuing off-frame?
5. What is in front of what, and which contacts or supports are visible?
6. Which portals, stairs, ramps, platforms, bridges, or corridors connect the regions?
7. Which hidden volumes must exist for openings, shadows, reflections, or traversal to work?
8. Which common-size observations provide scale ranges?
9. Which cues require geometry, a material receiver, lighting, atmosphere, or post-processing?
10. What blockout and cross-view evidence can disprove the current hypothesis?

Do not add surface detail until this chain is coherent.

For stairs, railings, ramps, escalators, curved fences, pipes, and tracks, read
`directional-structure-recovery.md` and create an ordered semantic skeleton before renderable
geometry. Endpoint order, ascent, bend side, supported edge, handedness, and local up axis are
spatial facts, not decorative implementation details.

## Observation, Inference, And Hypothesis

Keep three epistemic levels separate:

- `observed`: directly visible line, silhouette, overlap, contact, boundary, or light change.
- `inferred`: required by several observations, such as a corridor behind a doorway.
- `hypothesis`: one plausible explanation among alternatives.

Every inference and hypothesis needs evidence, confidence, impact if wrong, and a discriminating
test. Never turn a convenient object name into spatial fact.

## Spatial Regions

Represent space as regions rather than a flat object list:

- camera region;
- extreme foreground or camera enclosure;
- foreground;
- main middle region;
- background or axis terminus;
- occluded required-support region;
- off-frame continuation.

For each region record its depth order, elevation range, observed/inferred state, completion tier,
screen evidence, and confidence. A dark area is not automatically a wall; it may be an aperture,
unlit corridor, reflected space, or occluded volume.

## Spatial Connections

Describe the topological chain:

```text
camera region
-> main region
-> elevation transition
-> platform or threshold
-> aperture
-> inner passage
-> deeper or off-frame region
```

Valid connection classes include:

- `opens_into`;
- `connected_by_stairs`;
- `connected_by_ramp`;
- `connected_by_platform`;
- `corridor_continuation`;
- `contains`;
- `adjacent`;
- `separated_by_boundary`;
- `support_contact`;
- `continues_beyond_frame`.

For openings and elevation transitions, record thickness/depth, traversability, level change, and
the hidden support geometry needed by shadows, reflections, or navigation. A black plane does not
count as a doorway or deeper room.

## Camera Solve

Solve camera and layout as coupled variables, but do not let them compensate for one another
without evidence.

1. Group stable line families from floors, walls, ceilings, columns, rails, and door frames.
2. Estimate vanishing directions, horizon, vertical convergence, roll, crop, and lens distortion.
3. Record a lens/projection range rather than one asserted focal length.
4. Create a minimal spatial blockout.
5. Mark the camera `provisional` while testing projection and region layout.
6. Adjust geometry with the camera temporarily held.
7. Reopen the camera only when multiple stable lines or anchors show a projection error.
8. Lock the camera only after camera view and cross-view spatial checks pass.

Moving a locked camera invalidates downstream comparison evidence and requires a new camera
revision. Never move the camera only to hide incorrect architecture.

## Scale

Choose one or more scale anchors such as a person, door, stair riser, railing, tile, fixture,
vehicle, or pipe. Record a plausible range, its depth region, and confidence.

Derive scale as:

```text
anchor range -> relative ratios -> depth correction -> blockout dimensions -> camera-view review
```

Do not compare near and far objects by raw pixel size. Do not claim exact dimensions from a single
image unless calibrated evidence exists.

## Representation Routing

Classify each important observation before building it:

- `geometry`: changes silhouette, occlusion, contact, shadow, reflection, or spatial connection;
- `material`: color, roughness, normal, coating, contamination, or microdamage on a real receiver;
- `lighting`: source, projected pattern, bounce, or illumination region;
- `atmosphere`: fog, aerial perspective, smoke, or volumetric beam;
- `post`: vignette, grain, glow, chromatic aberration, or lens distortion;
- `spatial_region`: empty or hidden volume explained by boundaries and connections.

Negative space is not a fabricated mesh. Architectural negative space must be explained by the
surrounding geometry and a spatial region. Presentation mattes may remain visual-only.

## Blockout

The first blockout may contain only:

- coordinate frame and scale anchors;
- camera;
- floors, walls, ceilings, and major boundaries;
- major portals and elevation changes;
- primary masses that change silhouette or occlusion;
- support geometry required for hidden space.

Do not add hero materials, surface damage, small props, decorative modules, or final lighting.

For an environment, produce unique camera, top, front, and side views. The camera view validates
projection; orthographic views validate continuity, depth, support, and portal connections. Hidden
geometry is not expected to match an unseen reference view, but it must form a coherent spatial
hypothesis and support the visible frame.

Before Gate R1 passes, map the hypothesis to the Blender scene:

- each non-deferred region lists `object_names` and a non-degenerate `bounds_object`;
- the camera region's bounds contain the active camera;
- every opening, stair, ramp, platform, corridor, or off-frame continuation lists real
  `depth_object_names`;
- helper bounds may be hidden from render, but depth objects must be real support or boundary
  geometry rather than validation-only visible proxies.

## Spatial Invariants

Declare invariants before detailed modeling. Typical examples:

- a stair terminates on a platform rather than inside a wall;
- a doorway has wall thickness and a connected region behind it;
- a column reaches or intentionally stops before its support surface;
- a railing follows a traversable edge;
- every stair records lower and upper landing ownership and an unambiguous ascent direction;
- every curved railing records an ordered support path, bend side, and stable up axis;
- a corridor continues far enough to support visible shadows and reflections;
- a pipe has a connected source and destination;
- the camera is not embedded in visible geometry;
- no region becomes disconnected merely to match one screen-space silhouette.

## Failure Signs

- Screen bounds match while top/side views reveal impossible depth.
- Camera and architecture are alternately moved without identifying which variable is wrong.
- Every reference task is classified as a fixed shot.
- Dark openings are replaced by black planes.
- Stairs, platforms, doors, and corridors look adjacent but are not connected.
- A visible region has no path from the camera region or no declared boundary.
- P0 labels force lighting, atmosphere, or negative space into fake mesh objects.
- Added texture and fog conceal a failed blockout.
- Stair flights, platforms, and handrails were built independently and no longer share endpoints.
- A curved railing is repaired post-by-post although its source path or local frame is wrong.

Return to the spatial hypothesis whenever one of these appears.
