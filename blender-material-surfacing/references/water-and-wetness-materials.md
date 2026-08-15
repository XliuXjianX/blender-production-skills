# Water And Wetness Material Workflow

## 1. Decide What Exists

Classify the requested surface:

- thin damp film on a substrate;
- shallow puddle with visible boundary and depth;
- static contained liquid;
- moving liquid surface supplied by a simulation;
- open ocean surface;
- mist, spray, foam, bubbles, or suspended sediment.

Do not use one transparent plane for all categories.

## 2. Thin Wetness Layer

Use a shader layer when water thickness is visually negligible:

- slightly darken/shift the substrate where absorption is supported;
- narrow roughness and increase reflection continuity;
- preserve microrelief under the film at reduced strength;
- mask from cavities, upward-facing areas, splash zones, drainage, and painted data;
- break the edge with physically plausible runoff and evaporation patterns.

No volume absorption is required for a truly negligible film.

## 3. Puddles And Contained Water

Use closed, non-zero-thickness geometry conforming to the container or depression:

- waterline below the rim;
- no coplanar overlap with the container floor;
- sensible contact boundary and meniscus policy for the shot scale;
- surface normal primarily upward unless motion provides another shape;
- IOR near physical water, high transmission, and low but nonzero roughness;
- volume absorption calibrated in world units when thickness affects color;
- small normal waves separated from large surface shape.

Validate the liquid volume from side/top views, not reflection alone.

## 4. Dynamic Or Simulated Water

The simulation owns the large moving surface. The material owns reflection, refraction,
transmission, absorption, micro-normal breakup, and foam/sediment appearance. Do not add a second
large procedural displacement that contradicts the cached fluid mesh.

Use velocity, foam, wet maps, or generated attributes only when their data actually exists and is
stable through cache/render.

## 5. Ocean Surface

- Use Ocean displacement/geometry for macro and mid-scale waves.
- Use shader normals for smaller capillary detail.
- Route Ocean foam data into a separate dielectric foam response.
- Reduce transmission and increase diffuse/rough response in foam.
- Keep horizon displacement, repetition, and wave scale coherent with scene units and wind.

## 6. Engine Review

Cycles and Eevee require different transparency/refraction settings. Probe the active Blender
version and engine instead of copying an obsolete material-settings recipe. In both engines test:

- a dark object below the surface;
- a bright reflection at grazing angle;
- shallow and deep thickness;
- contact with the container;
- motion blur and denoising for animated water;
- final sample/noise cost.

## 7. Failure Diagnosis

- Glass slab look: no waterline/contact logic, excessive roughness uniformity, or wrong volume shape.
- Black water: absorption too strong for world scale, insufficient transmission bounces, or exposure issue.
- Invisible water: no useful reflection environment, no thickness/color cue, or overly perfect surface.
- Milky water: roughness/volume scattering too strong or denoising destroys fine transmission.
- Floating puddle: coplanar gap, no contact shadow/meniscus, or puddle boundary ignores surface slope.
- Double waves: simulation displacement and shader displacement both carry the same scale.

## 8. Validation

Require geometry class, IOR/transmission/roughness evidence, absorption scale when visible, contact
policy, large-versus-small wave ownership, foam ownership, and unique review renders.

Official basis:

- Principled BSDF: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html
- Volume Absorption: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/volume_absorption.html
- Ocean: https://docs.blender.org/manual/en/5.2/modeling/modifiers/physics/ocean.html
