# Project Genesis — Plaza trees: distance-aware WebGL LOD V003 (2026-10-29)

Gabriel Burdese approved **up to 8% image difference for medium-distance LOD1** and **up to 15% for far-distance LOD2**. The original full-detail masters remain visually approved and unmodified. All optimization here is a separate derivative; no PlayCanvas map integration has been made.

The rendering proxy is 720x720 RGBA in Blender Cycles with matching camera and lighting per LOD. LOD1 renders use orthographic scale 2.7 x subject span, LOD2 scale 5.2 x span. The acceptance gate requires both the premultiplied-color mean absolute pixel difference and the binary silhouette XOR / union to remain within each cap, in both front and three-quarter views. The percentages are **image proxies, not rigorous perceptual-quality or runtime performance certification**.

| Tree master | Master tris | LOD1 tris | Reduction LOD1 | Max color / silhouette LOD1 | LOD2 tris | Reduction LOD2 | Max color / silhouette LOD2 |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Oak V017 | 58,164 | 37,702 | 35.18% | 6.59% / 6.84% | 28,364 | 51.23% | 8.66% / 12.30% |
| Ash V020 | 56,332 | 40,984 | 27.25% | 4.99% / 7.03% | 30,510 | 45.84% | 6.99% / 13.57% |
| Linden V022 | 53,644 | 37,910 | 29.33% | 7.33% / 5.69% | 24,862 | 53.65% | 11.77% / 14.71% |
| Burgundy maple V021 | 54,284 | 34,610 | 36.24% | 6.08% / 7.49% | 25,566 | 52.90% | 8.77% / 13.03% |

All eight derivative GLB files passed the static artifact and image-proxy gates, and all four GH Actions jobs completed successfully. **Each LOD2 now has strictly fewer triangles than its LOD1.**

GLBs: `assets/tree_webgl_v003/{oak,ash,linden,maple}/lod{1,2}.glb`.
PNG front/three-quarter image comparisons: `previews/tree_webgl_v003/{species}/{master_lod1,master_lod2,lod1,lod2}_{front,three_quarter}.png`; detailed machine audits `audit.json` in the same directories.

Not yet tested: actual browser frame times, alpha overdraw, draw calls, VRAM use, PlayCanvas model import, appearance during LOD transition, distance thresholds/hysteresis, downloadable file compression. No integration or final deployment approval is implied. Keep approved art masters unchanged.
