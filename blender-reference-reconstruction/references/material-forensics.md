# Material Forensics

## Layer Model

Describe every important surface as:

1. substrate: metal, ceramic, glass, plastic, wood, concrete, fabric, liquid, or composite;
2. manufacturing cues: rolled, cast, welded, injection-molded, glazed, woven, brushed, or painted;
3. coating and finish;
4. damage and edge behavior;
5. contamination and aging cause;
6. dry, damp, wet, submerged, or condensing state;
7. expected diffuse, specular, transmission, volume, and normal response.

Before Gate R2, record `selected_hypothesis`, its confidence, and `validation_requirements`.
Copy those requirements into the same entity ID in `construction_graph.json`. A liquid normally
requires `single_component`, `closed_volume`, `material_class: liquid`, a minimum volume ratio,
and volume absorption; a visible curved manufactured surface normally requires smooth-face
coverage and connected-component checks.

Color alone never establishes material identity.

## Common Failure Checks

### Metal

Require believable thickness, rolled or manufactured edges, softened but controlled highlights, oxidation that reduces metallic response locally, and rust organized around seams, scratches, water paths, and exposed substrate.

### Injection-Molded Plastic

Require wall thickness, ribs, molded radii, draft or parting cues when visible, broad dielectric highlights, worn edges, and contamination. Do not replace a molded crate with beveled wooden panels.

### Wired Or Dirty Glass

Separate embedded wire, glass transmission, roughness variation, scratches, deposits, and condensation. The wire pattern must remain subordinate when the reference is dominated by grime or fogging.

### Fabric

Require gravity, attachment, thickness, compression, absorbency, and fold scale. Wet fabric hangs heavier and has localized darkening; a rectangular or symmetric ribbon silhouette is a failure sign.

### Tile And Wet Concrete

Require tile module, grout depth, edge wear, localized mineral deposits, and causal wet/dry boundaries. Avoid one uniform noise field across tile, grout, and floor.

### Water

First decide whether water is actually supported by the image. When it is:

- use a closed, non-zero-volume mesh conforming to its container;
- keep the waterline below the rim and document contact or meniscus treatment;
- use a physically plausible IOR and surface roughness;
- provide volume absorption for visible thickness;
- use Wave, Dynamic Paint, or Fluid when visible interaction requires it;
- do not call a plane or thin beveled slab a water volume.

For an ambiguous basin interior, keep alternatives such as empty metal, wet metal, shallow water, and dark reflection until evidence or a variant render resolves them.

## Causal Aging

Map each effect to a cause:

- gravity: downward streaks and settling;
- water flow: mineral paths, rust runs, wet boundaries;
- contact: polished or dirty handles, rims, and floor supports;
- cavities: accumulated dust, mold, and darkened grout;
- oxidation: exposed metal and coating failure;
- sunlight or chemicals: fading and discoloration.

Reject identical noise scale, contrast, and direction on unrelated materials.
