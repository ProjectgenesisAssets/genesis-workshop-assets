# Project Genesis — Plaza oak art review (2026-10-28)

Status: **No candidate approved for the game map.** All assets are experimental, PlayCanvas-oriented GLB exports. Target: <=60,000 triangles/tree; human art approval >=8/10; keep originals reversible.

| Candidate | GLB triangles | Outcome |
|---|---:|---|
| V007 | 44,700 | Rejected: fragmented / visibly holed trunk and sparse synthetic foliage. |
| V008 | 50,800 | Technically valid: rebuilt closed lower trunk and roots; synthetic foliage still flat, preview crown clipped. |
| V009 | 53,000 | Watertight trunk; full-tree camera; foliage still synthetic and crown too tall. |
| V010 | 53,000 | **Best visual starting point** so far. CC0 photo-scanned leaves, full-tree framing and closed trunk. Still below art threshold; crown too narrow/tall. |
| V011 | 53,000 | **Rejected visually**: silhouette-scoring chose seed 27941 but produced unnatural exposed downward branches. Numerical crown scores are not a substitute for art QA. |

## Source and license

- Blender official Sapling addon used only to create source geometry.
- V010/V011 leaf texture: [ambientCG LeafSet016](https://ambientcg.com/view?id=LeafSet016), 1K JPG color + opacity, CC0 1.0. Photogrammetry-based.
- Generated bark is original procedural color texture.
- All original source Python scripts and GitHub workflows remain in branch `feature/plaza-cuatro-arboles-playcanvas`.

## Verified artifacts

- [V010 renders](../plaza_trees_v010/oak) (see `three_quarter.png`, `front.png`, `side.png`, `skeleton_three_quarter.png`).
- [V010 GLB](../../assets/plaza_trees_v010/oak/oak_sapling_v010.glb).
- [V011 renders](./oak), preserved for review as a failed design experiment.
- V010 and V011 passed official Blender 4.5.13 generation and GLB static triangle/material checks. No mobile performance measurement or PlayCanvas rendering benchmark has yet been run.

## Next art approach

Stop tuning crown shape by numerical spread alone. Explore a different free/open-source procedural branching generator (e.g., [Modular Tree](https://github.com/GoodPie/modular_tree) or [Easy Tree](https://github.com/jacobcjohnston/Easy-Tree)) and inspect license/API suitability first. Preserve CC0 leaf atlas, trunk closure checks, GLB alpha MASK, and <=60k triangle budget. Aim for a convincing broad oak canopy with layered branch taper and realistic clumps. Do not merge to the live map without Gabriel's approval.
