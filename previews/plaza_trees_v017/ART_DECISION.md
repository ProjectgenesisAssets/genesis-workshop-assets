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

## New decision — 2026-10-29 (Argentina)

**Gabriel Burdese approved ALL FOUR tree art masters for the Project Genesis PlayCanvas plaza.** This supersedes the pending status of the newer species versions, but does not retroactively approve obsolete V004 models.

- **APPROVED — oak V017:** `assets/plaza_trees_v017/oak/oak_easytree_v017.glb` (58,164 triangles).
- **APPROVED — ash / fresno V020:** `assets/plaza_trees_v020/ash/ash_easytree_v020.glb` (56,332 triangles).
- **APPROVED — linden / tilo V022:** `assets/plaza_trees_v022/linden/linden_easytree_v022.glb` (53,644 triangles). Includes the added thin, tapering under-canopy branches requested by Gabriel.
- **APPROVED — burgundy maple / arce V021:** `assets/plaza_trees_v021/maple/maple_easytree_v021.glb` (54,284 triangles). Burgundy/crimson leaf hue accepted.

**Meaning of approval:** final visual/art direction and these exact versioned source assets are approved. Keep these masters intact; any optimization must produce separately versioned derived GLBs and a visual comparison. The oak WebGL LOD1/LOD2 are **not approved** by this art decision: retain the independent condition of at most **1.5% visual fidelity loss** and provide same-angle renders/measurement before accepting them.

Do not automatically add these trees to the live plaza or edit the PlayCanvas game until Gabriel explicitly authorizes scene integration. Technical render/GLB assertions passed for the four masters, but interactive browser/GPU performance, texture overdraw, LOD transitions and collision quality still require validation.
