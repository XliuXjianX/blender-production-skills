# Reference Audit

## Contents

1. Observation ledger
2. Spatial hypothesis
3. Camera evidence
4. Visual hierarchy
5. Uncertainty
6. Simplification

## Observation Ledger

Create one entry for each important observed entity, region, boundary, aperture, surface state, or
light effect. Use semantic IDs that describe evidence, not a guessed object name. Record:

- priority: `P0`, `P1`, or `P2`;
- normalized bounds `[x, y, width, height]` from the image top-left;
- visible evidence and silhouette landmarks;
- overlap order and physical contacts;
- estimated scale range;
- object-category hypotheses and confidence;
- construction cues such as rolled sheet edge, injection-molded rib, welded joint, folded cloth, or cast body;
- required visible cues and allowed simplification.
- production domain: `geometry`, `material`, `lighting`, `atmosphere`, `post`, `presentation`, or
  `spatial_region`;
- receiver ID when a material or light effect belongs to another buildable surface.

`P0` entities define the shot's identity. Their bounds, silhouette, material class, and contacts must be measurable. A large dark region, doorway, or reflected surface may be `P0` even when it is not a conventional object.

P0 is an importance level, not a command to create a mesh. Only `production_domain: geometry`
requires a same-ID construction part. Architectural negative space maps to a spatial region and its
boundaries; lighting, atmosphere, and post effects retain their own production domains.

## Spatial Hypothesis

Before final object naming, fill `spatial_hypothesis.json`. Record:

- the region containing the camera and whether it is inside, outside, or at a threshold;
- depth, lateral, vertical, and diagonal axes;
- foreground, middle, background, occluded, and off-frame regions;
- portals, stairs, ramps, platforms, supports, and continuation paths;
- occlusion order and visible contacts;
- scale anchors with depth-aware plausible ranges;
- hidden support space required for shadows, reflections, apertures, and traversal;
- competing hypotheses and the view or measurement that can reject each one.

The spatial graph answers where things exist and connect. The observation ledger answers what is
visible. Do not merge the two into an object list.

## Camera Evidence

Do not guess focal length alone. Record:

- image aspect ratio and crop;
- horizon or confidence that it is outside the frame;
- vertical convergence and roll;
- two or more vanishing-direction observations when available;
- camera-height evidence from doors, fixtures, furniture, and eye-level surfaces;
- at least three normalized anchor points or rectangles;
- negative-space ratios on the left, right, top, and bottom;
- occlusion order from camera to background;
- lens and projection range, not only one preferred number.

Match the camera with a neutral gray blockout. Keep it provisional while testing the region graph.
Compare silhouettes and anchor errors in camera view, then inspect top/front/side structural views
before locking it. Reopen a locked camera only with new projective evidence and invalidate stale
downstream comparisons when its revision changes.

## Visual Hierarchy

Describe the viewing sequence at thumbnail size. Record:

- first, second, and third attention anchors;
- practical lights and brightest speculars;
- largest dark masses and whether they retain detail;
- dominant warm/cool relationship;
- depth layers and atmosphere;
- texture frequency by foreground, subject, and background.

If the hierarchy differs, added detail will not repair the reconstruction.

## Uncertainty

Every uncertain fact needs:

- the competing hypotheses;
- evidence for and against each;
- impact if wrong: `low`, `medium`, or `blocking`;
- disposition: `resolve`, `test_variants`, `request_reference`, or `defer_off_camera`.

Examples include water versus wet metal, plastic versus painted wood, transparent glass versus dirty acrylic, and a structural seam versus an occlusion line. Never encode an unresolved hypothesis as a definitive object or material name.

## Simplification

Shot-only simplification is allowed only when it cannot change visible silhouette, contact, shadow, reflection, transmission, or secondary bounce. Record each simplification and the evidence that keeps it outside the visible result.
