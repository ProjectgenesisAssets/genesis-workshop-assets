# Bellows V013 — qualitative art review, 27 October 2026

Source: actual Blender 4.5.13 GitHub Actions render from run 40440701246, four views, compared against V012 from run 40440084011. Both GLBs and their preview PNGs were inspected. No local Blender execution.

## Technical
- Build succeeded, GLB 22,576 triangles, 37 meshes, 5 materials, 12 embedded images; objective QA passed against V011 baseline.
- V012 GLB was inspected directly: `bellows_creased_dark_oxblood_leather` binds `bellows_oxblood_leather_baked_albedo_V012` as baseColorTexture; `bellows_aged_oak_long_grain` binds `bellows_aged_oak_baked_albedo_V012`.
- V013 vs V012 three-quarter image: mean RGB change only 0.00180 overall; oak top region 0.00833; folds region 0.00982 (normalized 0–1).
- Old QA's silhouette IoU 1.0 was not meaningful because the render background is opaque. Main QA has since been corrected for future runs.

## Artistic conclusion — DO NOT PROMOTE
The top board still reads pale grey, stone-like rather than convincing warm oak. Leather pleats still look overly uniform and stacked; the modest phase variation is not visibly sufficient. The model remains provisionally usable, as the user said, but not approved and not 8/10. V013 does not solve the art-direction issue. **Preserve V012 as the provisional baseline** until a real scanned timber material and stronger leather construction are evaluated. Do not loop on numeric tint multipliers alone.
