# Plaza 13 x 13 — four original trees, PlayCanvas V001

**Status:** branch-only art candidates. This is **not** approval for game integration.

- Repo: `ProjectgenesisAssets/genesis-workshop-assets`
- Branch: `feature/plaza-cuatro-arboles-playcanvas`
- Generator: `scripts/generar_arboles_plaza_v001.py`
- Blender: official 4.5.13 LTS on GitHub-hosted Linux, no local workstation.
- Workflow: `.github/workflows/plaza-cuatro-arboles-v001.yml`
- Cost: no paid marketplace or generation providers.
- Geometry: original procedural trunks/branches and opaque individual leaf polygons (no alpha overdraw).
- Limit: **60,000 triangles maximum per tree**, checked in Blender and from final GLB index accessors.
- Exports: one `.glb` and editable `.blend` per tree; QA JSON, front/three-quarter/side/rear PNGs.
- CI strategy: four independent, parallel matrix jobs.
- Outputs: GitHub Actions artifacts, **expire in 2 days**. Do not commit large binaries to this public repo.
- License/provenance: original code-generated geometry, no third-party assets.
- Four variations: oak (roble, broad crown), ash (fresno, high airy crown), maple (arce, rusty-red foliage), linden (tilo, dense crown).

## Run and review

Go to [GitHub Actions](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/workflows/plaza-cuatro-arboles-v001.yml), select `feature/plaza-cuatro-arboles-playcanvas` and run the workflow. A branch push also requests a run. Download all four artifacts when the matrix finishes.

**Do not call these photoreal or AAA yet.** Review each of the four PNG views at full size. Inspect shapes, branch junctions, foliage gaps, shading and lack of flat/cheap-looking materials. Reject or refine until Gabriel rates each at least 8/10. The maximum **8% visual degradation** condition can only be quantified with a baseline, side-by-side comparisons and a selected screen-space metric; V001 is original geometry, not a decimation candidate.

## PlayCanvas integration notes

Load GLB as a PlayCanvas Render asset. Tree meshes contain four shared material slots (bark and three foliage shades). For production consider an albedo/normal atlas, modest draw-call count, culling/LOD and pooled vegetation instances. The exported GLB has no studio lights, ground or preview camera.

The four-tree plaza layout is provisional until scale and visual quality are approved. Avoid relying on triangle count alone for performance; inspect transparency, shader overdraw, draw calls, texture memory and shadows on representative devices.
