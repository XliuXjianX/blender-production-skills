# Metal Material Workflow

## 1. Classify The Metal

Choose one primary state:

- bare polished, machined, brushed, rolled, cast, galvanized, oxidized, corroded;
- painted or powder-coated metal;
- clear-coated metal;
- mixed exposed substrate and damaged coating.

Record the metal family only when evidence matters to color and oxidation. Do not label every
gray reflective surface "steel" without structural or reference evidence.

## 2. Build The Geometry Response First

Metal realism depends strongly on edge radii, surface flatness, dents, and normals. Verify:

- manufactured edges have scale-appropriate bevels;
- large panels are not mathematically perfect when the reference shows warping or stamping;
- smooth shading does not round designed planar faces;
- welds, seams, fasteners, and panel gaps are geometry when they affect silhouette or shadows.

Do not use a noisy normal map to hide invalid hard-surface shading.

## 3. Bare Metal Substrate

- Use the metallic material model for the exposed conductor.
- Derive color from the metal reference, not from a generic medium gray.
- Set roughness from manufacturing state: polished gives narrow continuous reflections; cast,
  bead-blasted, or oxidized surfaces broaden and break them.
- Add anisotropy only for a directional process and provide the correct tangent direction.
- Separate broad waviness, machining/brushing direction, fine scratches, and microscopic roughness.

Do not use perfectly black Base Color as a shortcut for dark metal. Reflection environment and
roughness must carry the form.

## 4. Brushed And Machined Metal

1. Align UV/tangent with the real brushing or tool path.
2. Add elongated fine roughness variation along the tangent.
3. Add sparse cross-scratches only when supported by wear history.
4. Keep anisotropy and scratch direction coherent across a manufactured sheet.
5. Break continuity at separate panels, welds, or differently machined parts.
6. Validate by rotating a long area light; the elongated highlight must follow the process direction.

Random isotropic Noise plus Metallic 1 is not brushed metal.

## 5. Coated And Painted Metal

Treat paint as a dielectric layer over metal:

- intact paint is not metallic;
- exposed chips reveal metallic substrate;
- clear coat is used only when a clear top layer exists;
- chips require thickness/edge logic at hero distance;
- edge wear follows contact and abrasion, not every convex edge equally;
- rust begins where coating fails and moisture/oxygen can persist.

Use separate masks for chipped paint, rust, dirt, and wetness. A rust-colored noise mask alone is
not corrosion.

## 6. Rust, Oxide, Welds, And Dirt

- Rust is dielectric, rough, porous, and often has height variation.
- Use broad corrosion zones, medium flaking, and fine granular roughness at distinct scales.
- Prefer cavities, water traps, damaged coating, horizontal pooling, and drainage paths.
- Preserve recent bare scratches as metal when they have not oxidized.
- Weld beads need intentional geometry/profile and heat tint only where the manufacturing process supports it.
- Dirt changes both color and roughness; oil may darken while narrowing roughness.

## 7. Validation

Require:

- plausible conductor/dielectric separation;
- material-specific roughness under grazing reflection;
- tangent-aligned anisotropy when present;
- no identical scratch pattern across unrelated parts;
- coating damage connected to physical causes;
- readable edges and panel form under neutral reflective review;
- final engine render with no firefly/noise masking of roughness response.

Official basis: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html
