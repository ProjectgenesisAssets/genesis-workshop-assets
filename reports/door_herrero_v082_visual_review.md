# V082 — Herrero artwork comparison and recommendation (2026-11-01)

## Preserved approvals
- V079 warm-blackened iron hue remains approved and is unchanged across V082 A/B.
- SHA256 of the exact approved albedo PNG in both V082 variants: `f6fea7e90c4be11f439435c2563003324c4cbc09b288a2a0796bdb9c85e81654`.
- V011 door geometry and ornament positions/materials preserved.
- No modifications to main branch or accepted previous asset.

## Verified production
- GitHub Actions run ID: **41338642841** — completed successfully.
- Artifact: `blacksmith-door-v082-subtle-forged-facets` (artifact ID 13096631325).
- Published previews are under `previews/door_herrero_v082/`.
- Full and close-up comparison render in matching studio lighting.

## Surface findings
- V081-A introduced visible but exaggerated round impact craters.
- V082 avoids the crater look with shallow 5–8 edged irregular, rotated hammer impressions.
- Measured mean XY tangent-normal slope (512px sampled RGB normal PNG):
  - V079: 0.0167
  - V081-A: 0.0591
  - V081-B: 0.1161
  - V082-A: 0.0168
  - V082-B: 0.0232
- V082-A remains almost indistinguishable from V079.
- V082-B yields subtle visible refinement without large crater artifacts. **Recommended as art finishing candidate; needs user visual sign-off before final art status.**
- Color is pixel-identical across V082 A/B; shader reflects the existing warm V079 tint.

## Outstanding integration requirements (not art iteration)
- GLB not yet generated or checked in PlayCanvas.
- Existing evaluation is 38,112 triangles against 25,000 target: optimize with silhouette preserved.
- Check normal-map orientation, material response at in-game light levels, pivots and functional hinges.
- No claim of production-ready or final acceptance until completed tests and actual user sign-off.

## Design freeze recommendation
When user approves V082-B, freeze color, door mesh, ornaments, and subtle normal map. Do not create V083 without an explicit visual problem found in game QA.
