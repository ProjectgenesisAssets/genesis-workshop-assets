# Door Herrero V080 – Art direction based on actual V079 QA (2026-11-01)

Status update 2026-11-01: **V079 nearly functional, user approves overall look and specifically the existing color.** V080 must preserve the hue and increase apparent physical roughness/microrelief plus moderate metallic response. New render/GLB must still be verified before final approval.

## Inputs inspected
- Successful V079 run: https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/41330078898
- V079 artifact ID 13093625089, 32 contents including A/B/C/D renders and PBR QA.
- Baseline V011 geometry, V068-C ornaments, retained Curtidor V073 branch.

## Actual visible outcome (superseded by user's later approval of V079's color)
- Candidate B (warm blackened iron at studio power 40%) is preferred starting point over A/C.
- Door reads as dark iron, but large panel surfaces are too matte, even and gray.
- Patina must not resemble leather, marble or cloud camouflage.
- Hardware is preserved and still readable.
- Candidate C at 25% appears too dim; changing studio power alone is not a material fix.

## Technical blockers
- DESIGN_AUDIT reports 38,112 evaluated triangles vs 25,000 target.
- V079_VISUAL_QA says GLB not generated.
- V079_METAL_VS_LEATHER_QA says WebGL optimization not validated.
- V079_MATERIAL_TEST says artist approval PENDING.
- Avoid asserting an 8+/10 score until real renders and game integration are reviewed.

## Next V080 render experiment (non-destructive)
1. Preserve full V079 baseline and geometry V011. Do not revise ornaments.
2. Begin with B warm-blackened iron, preserve black oxide in recesses.
3. Make the actual exposed iron catch broad coherent metallic highlights: adjust correlated metalness / roughness (not just brighten base color).
4. Keep roughness heterogeneous at plausible scale: polished ridges and handle contact wear, dark rough untouched recesses. No high-frequency scratches repeated uniformly.
5. Introduce physically shallow, sparsely distributed broad hammer dents with matched normal and roughness; reject leatherlike stretched mottling.
6. Use identical studio/HDRI, view angles and exposure for baseline vs test. Add a midtone close-up of main panel and a 3/4 side view.
7. Measure triangles; produce optimized mesh only after art succeeds, preserving silhouette and pierce-through peephole.
8. Export actual GLB and validate materials, file size, normals, UVs and PlayCanvas result before any integration.
9. Save baseline + comparison PNGs, QA JSON and measured data in workflow artifacts. Do not overwrite production-approved assets.

## Acceptance gates
- Realism >=8/10 after direct visual review.
- Metal clearly reads as forged iron and bronze/copper ornamentation stays distinctive.
- No conspicuous marble/stone/leather effect.
- Reproducible Blender run completes; no missing PNG/GLB.
- WebGL QA completed separately.

## V080 production work
- Python script: `scripts/puerta_herreria_art_080.py`
- Workflow: `.github/workflows/door-herrero-v080-preview.yml`
- Render variants: A medium texture/metallicity and B stronger texture/metallicity. Both are required to have bit-identical albedo maps from the approved warm V079 color.
- User did NOT request integrating to PlayCanvas yet; retain V079 until the new V080 renders are reviewed.
