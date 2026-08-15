---
name: blender-npr-cycles
description: Build and validate Blender 5.2 Cycles 3D-to-2D materials using four camera-plane-offset Shader Raycast tests to derive an editable silhouette mask, combined with Cycles-compatible toon or flat shading. Use when a Cycles render needs an in-material outline without Shader to RGB.
---

# Blender NPR Cycles

Create a Cycles-compatible object-outline mask with Blender 5.2's Shader Raycast node.
This is a shader workflow, not Geometry Nodes.

## Suite Authority

Follow `../blender-production-router/references/production-protocol.md` and
`../blender-production-router/references/native-component-contract.md`. The Router owns route,
stage, budgets, rollback, and pauses. This skill owns Cycles raycast shading and outline evidence
only; it cannot reroute, restart analysis, or use NPR to conceal geometry defects.

## System Choice And Asset Boundary

Read `../blender-production-router/references/system-choice-contract.md`. A requested stylized,
shader, or compositor candidate may be discovered by `blender-local-asset-library`, but this Skill
owns whether it is compatible with Cycles and the four-raycast outline method. Do not import an
Eevee-only Shader to RGB graph or a Geometry Nodes outline merely because it comes from a local
asset library.

Require passed formal topology, Structural Forms, Transition Forms, connection, silhouette, and
real-bevel gates first. Raycast outlines may stylize an accepted surface; they are not evidence of
a valid contour, welded shell, manufactured radius, or clean intersection.

## Availability Gate

- Require Blender 5.2 or newer.
- Require Cycles and `ShaderNodeRaycast`.
- Never substitute Eevee-only `Shader to RGB`.
- If the Blender version lacks Shader Raycast, route to inverted hull, Line Art,
  Freestyle, or compositor line extraction and record the fallback.

## Raycast Method

For each camera-plane offset `+X`, `-X`, `+Y`, and `-Y`:

1. Transform the offset vector from Camera space to World space.
2. Scale it by the requested outline width.
3. Add it to Geometry Position to create the ray origin.
4. Multiply Geometry Incoming by `-1` to point toward the camera.
5. Run Shader Raycast with a bounded ray length.
6. Read `Is Hit`.

Multiply the four hit masks. A point that remains covered in all four shifted tests is
interior; a point that fails at least one test becomes outline. Use the result to mix a
dark outline shader with a Cycles-compatible base shader.

Use `scripts/build_cycles_npr.py` to build:

- one reusable ray-sample shader group;
- one four-direction outline-and-toon shader group;
- one owned material on explicitly selected mesh objects.

The script defaults to local-object ray tests so nearby objects do not contaminate the
silhouette. Scene-aware ray tests must be an intentional choice.

## Hard Rules

- Do not reset the scene or World.
- Do not replace an existing user material without explicit approval.
- Do not use Shader to RGB in Cycles.
- Do not implement this method as Geometry Nodes.
- Do not use unlimited ray distance or an unbounded width.
- Do not assume world-space width is screen-space constant. Test near and far cameras.
- Do not silently enable scene-aware ray tests; neighboring geometry can create false
  outlines.
- Account for four additional shader-ray queries per shaded point when setting render
  samples, subdivision, and resolution.
- Disable the outline and verify neutral clay plus wireframe before accepting the NPR result.

## Validation Gate

Check all of the following:

- Cycles is active and Blender is at least 5.2.
- The sample group contains Camera-to-World vector transform, scaled offset, shifted
  position, reversed Incoming direction, and Shader Raycast.
- The look group contains exactly four ray-sample instances with `+X/-X/+Y/-Y` offsets.
- Three multiply operations combine all four `Is Hit` values.
- Local-only behavior matches the requested interaction policy.
- Front, profile, three-quarter, near, and far renders show a coherent outline.
- Neighboring-object, concavity, thin-part, transparency, displacement, and animation
  tests have been reviewed.
- Render cost and unique review-image paths are reported.

Read `references/cycles-raycast-outline.md` for the reconstructed graph, limitations,
fallbacks, and official Blender documentation.
