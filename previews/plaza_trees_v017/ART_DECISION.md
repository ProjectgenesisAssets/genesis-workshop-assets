# Project Genesis — Plaza tree art decision (2026-10-28, Argentina)

Human review by Gabriel Burdese:

- **ACCEPTED — oak, V017**. The visible model/overall visual direction is retained. It is the chosen oak asset; keep its source, two render angles, and GLB immutable unless Gabriel requests a change.
- **REJECTED — ash, V004**. Old visual is not acceptable; rebuild separately with a genuine ash habit and bark, not as a color swap of the oak.
- **REJECTED — linden, V004**. Old visual is not acceptable; rebuild separately with its own round/heart-shaped crown structure, unique trunk, and leaves.
- **REJECTED — maple, V004**. Old visual is not acceptable; rebuild separately with maple-specific branches, bark and leaf silhouettes.

## Technical scope

- Oak V017: **58,164 triangles**, official Blender 4.5.13 / GitHub Actions completed successfully, GLB indices and alpha cutout validated.
- The limit is 60,000 triangles per tree. Distinct species must not be duplicate geometry with only different colors.
- The art selection does **not** constitute a browser/device performance certification. Real WebGL/PlayCanvas performance, texture memory, foliage overdraw, LODs and collisions remain untested.
- **No integration into the game map** without a separate integration decision. The accepted GLB remains in `assets/plaza_trees_v017/oak/oak_easytree_v017.glb`.

The original V004 renders and assets are preserved for historical comparison but are not accepted for production.
