# Project Genesis — Four-tree WebGL LOD visual gate (V002, 2026-10-29)

Approved source masters: oak V017, ash V020, linden V022, burgundy maple V021.
The four masters remain unchanged in `assets/plaza_trees_v*/`.

All four species completed Blender 4.5.13 GitHub Actions with same-angle 720x720 baseline vs candidates. The comparison threshold is <=1.5% foreground premultiplied color MAE and <=1.5% alpha silhouette XOR/union, on both front and three-quarter cameras. **This is a quantitative image proxy, not a perceptual 1.5% guarantee and not device performance validation.**

| Tree | Master tris | Best V002 LOD1 tris | Reduction | Worst color MAE | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Oak V017 | 58,164 | 55,712 | 4.22% | 1.1220% | passes image proxy |
| Ash V020 | 56,332 | 53,092 | 5.75% | 1.3639% | passes image proxy |
| Linden V022 | 53,644 | 52,188 | 2.71% | 1.1124% | passes image proxy |
| Burgundy maple V021 | 54,284 | 50,860 | 6.31% | 1.3601% | passes image proxy |

**Important:** The automatic V002 naming of LOD2 is not meaningful for three species: oak's LOD2 has *more* triangles than LOD1; ash/maple LOD2 match LOD1 exactly. Only the linden has an actual deeper LOD2 (51,800 tris; max MAE 1.3159%). Do **not** ship or load V002 LOD2 for oak, ash or maple as distinct distance levels. Fix LOD hierarchy and test greater viewing distance before treating those files as valid.

Compression and performance still pending: PlayCanvas Editor mesh compression (and associated runtime modules, if necessary), Basis texture compression, material alpha overdraw, memory footprint, actual WebGL 2 frame rate on target devices, distance transitions, collisions and instancing. Browser-level testing is mandatory before shipping.

**No game integration approved or executed.** Keep all source masters intact.
