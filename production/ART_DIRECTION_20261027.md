# Project Genesis — artistic direction and production checkpoint, 27 Oct 2026

Scope: **PlayCanvas/WebGL workshop assets only**. No changes to the game or the separate Blender repository. All rendering uses official Blender 4.5.13 in GitHub Actions.

## Binding artistic feedback
- **Forge:** user explicitly rejected the V010/V011 overall appearance as too **stylized**. Increasing coal emission alone is not an artistic solution. Prioritize a functional, heavy, believable medieval forge: irregular hand-laid refractory stone, realistic mortar and soot, stone or brick smoke capture geometry, and a structurally plausible hollow chimney. Do not auto-approve.
- **Bellows:** user considers the design provisionally usable but not convincing/approved. Preserve functional construction and best geometry; improve leather/wood distinction and aged PBR without arbitrary redesign.
- **Door and anvil:** retain current best candidates unless a specific defect is verified. Never force meaningless versions to keep the queue busy.

## Verified builds and work
- Door V011: run 40435141349 completed successfully; 68,028 to 38,768 evaluated triangles (-43.0%) with reported four-view IoU 0.9982–0.99948. This is a technical candidate only; still above 25k target and not approved.
- Anvil V022: run 40430776892 successful; no new justified defect established.
- Forge V011 coal-fracture revision: run 40440087705 successful after fixing invalid artifact names; GLB 57,668 triangles, 5 textured materials, 16 embedded images. **Artistic direction still rejected**.
- Bellows V012 leather PBR: original build rendered and objective QA passed, but artifact upload failed due a slash in the artifact name. Packaging was repaired and run 40440084011 was started to retain GLB/master/renders.
- Forge V012: new independent generator `scripts/genesis_hero_assets_v012.py` in `production/auto-forge-handlaid-masonry-v012`, run 40440350279 launched. It replaces the stylized metal-dominant hood with physically modeled bonded stone canopy and square hollow masonry flue, desaturates stone PBR, perturbs brick geometry and adds a rubble foundation. Await actual four-view/GLB QA; do not call this an improvement before visual inspection.

## QA integrity
- Old generic QA reported silhouette IoU=1.0 on opaque studio images because every alpha pixel was 255. **This was not a valid silhouette measurement.** Main `scripts/production_asset_qa.py` now reports silhouette unavailable on opaque renders instead of inventing 1.0.
- The same QA update now requires the V012 leather task's GLB material to bind its oxblood baseColorTexture.
- Worker artifact names no longer contain a slash. The worker now preserves GLB, editable .blend, PBR maps, four render PNGs and QA reports.
- No candidate is automatically artist-approved. Only the user may approve.

## Automation caveat
The ten-minute GitHub cron is present in `.github/workflows/overnight-10min-watch.yml` with a 09:00 ART hard cutoff, but **no `schedule`-event run had appeared by 02:47 UTC**. Push-triggered executions and the corrected worker have run. Do not claim the cron has been verified until a genuine scheduled run appears. If the cron continues not firing, diagnose the scheduler separately; do not relaunch identical renders merely to create activity.
