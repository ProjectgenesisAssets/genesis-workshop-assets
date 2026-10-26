# Project Genesis — Workshop Assets (PlayCanvas/WebGL)

Temporary **public** GitHub Actions workspace. Reusable source generators are versioned; heavy Blender outputs are short-lived workflow artifacts and are **not** canonical assets.

## Current production jobs

| Asset | Source generator | Workflow | Status |
| --- | --- | --- | --- |
| Iron workshop door (original reconstruction) | `scripts/puerta_herreria_art_001.py` | `puerta-herreria-art-master-v001.yml` | Visual candidate; requires quality score ≥8/10 and user approval |
| Wooden worktable | `scripts/generar_utileria_taller_v001.py mesa` | `herreria-lote-paralelo.yml` | **REJECTED ART DIRECTION**: simple geometry / flat colors |
| Workshop shelves | `scripts/generar_utileria_taller_v001.py estanteria` | `herreria-lote-paralelo.yml` | **REJECTED ART DIRECTION**: simple geometry / flat colors |
| Wall-mounted tool holder | `scripts/generar_utileria_taller_v001.py soporte_herramientas` | `herreria-lote-paralelo.yml` | **REJECTED ART DIRECTION**: simple geometry / flat colors |
| Coal storage box | `scripts/generar_utileria_taller_v001.py carbonera` | `herreria-lote-paralelo.yml` | **REJECTED ART DIRECTION**: simple geometry / flat colors |

**Quality gate:** do not promote any model lacking believable wear, bevels, silhouette, realistic PBR microstructure, and multi-angle visual review. Technical CI pass is NOT artistic approval. Rejected prototypes must not be used in PlayCanvas.\n\nEach work item produces a GLB, editable Blend, QA JSON and preview PNGs when successful. The independent utility models run in parallel. Results are reviewed **before** anything is promoted to the private canonical project.

## Realistic hero asset quality review (26 October 2026)

| Candidate | QA images/workflow | Editorial status |
| --- | --- | --- |
| Door V001 (`puerta_herreria_art_001.py`) | Four views at `previews/door_v001/` | **REJECTED** (severely misaligned leaf and trim) |
| Door V002 (`puerta_herreria_art_002.py`) | Four views at `previews/door_v002/` | **REJECTED** (body still shifted at animation parent pivot) |
| Door V003 (`puerta_herreria_art_003.py`) | `puerta-herreria-art-master-v003.yml` | Running; verifies transform invariance before QA render |
| Anvil V001 | Four views at `previews/heroes/anvil/` | **REJECTED** at initial visual QA ~5.5/10: checkerboard iron texture |
| Forge V001 | Four views at `previews/heroes/forge/` | **REJECTED** at initial visual QA ~5.5/10: boxy hood, weak heat |
| Bellows V001 | Four views at `previews/heroes/bellows/` | **REJECTED** at initial visual QA ~6/10: flat folds and texture |
| Anvil, forge and bellows V002 | `genesis-hero-trio-v002.yml` | Running 3 parallel Blender processes; smooth value-noise PBR; slimmer QA artifacts |

A GitHub Actions job can be green even when the sculpt/material fails the art direction. The only promotion condition is four-view visual QA and explicit Gabriel approval at 8/10 or higher. The 1536px PBR experiments stay reproducible from the scripts; V002 CI stores only review PNGs to avoid filling public GitHub artifact storage. The original private master assets (V175 ingot, mineral 55k/1536, sword V023 and existing approved objects) remain untouched.

## Operational rules

- Blender runs **only on GitHub Actions**, not on the local ChatGPT or user computer.
- Prefer official Blender **4.5.13 LTS** to avoid missing Cycles denoising dependencies.
- Artifacts expire after **2 days** to control GitHub Free storage usage.
- Do not add credentials, private masters or unapproved proprietary source to this public repository.
- Do not publish this repository's experimental candidates as finished game assets.
