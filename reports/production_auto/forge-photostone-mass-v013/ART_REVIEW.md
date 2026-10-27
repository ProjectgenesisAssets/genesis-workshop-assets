# Forge V013 — visual and technical audit, 27 Oct 2026

**Run:** 40441267800, successful real Blender 4.5.13 in GitHub Actions. Four Cycles views, GLB, editable .blend and PBR maps preserved. First V013 run 40441126043 failed only because an audit variable was out of scope; source was corrected before this successful run.

## Confirmed progress
- Actual CC0 Poly Haven **Quarry Wall** stone albedo/normal/roughness bound in Blender; `AUDIT.json` explicitly records `quarry_wall_cc0_scan_bound: true`.
- V013 GLB approximately **49 MB**, down from V012 approximately **79 MB** (about 37% smaller), while retaining the firebox and visible stonework. Still large for PlayCanvas/WebGL.
- 70,840 evaluated GLB triangles, 345 meshes, 5 materials, 16 embedded images. QA compared four actual views to V010; pixel differences are substantial.
- Heavy front masonry piers replace thin industrial rods. Larger courses and photographic stone improve material readability.

## Artistic decision — NOT APPROVED
Actual three-quarter render still resembles a **small roofed masonry barbecue** rather than a convincing working medieval blacksmith forge. The sloped hood still reads as a tiled roof, the square chimney as a short stack, and the working hearth as a neat decorative box. PBR improvement alone is insufficient.

**Do not promote to 8/10 or final.** Preserve V013 as the strongest technical/material experiment, V012 as geometry comparison, and V011 as earlier reference. The next iteration should rethink the underlying forge architecture, opening/working height, flue-to-hearth proportions and authentic blacksmithing workflow, rather than repeatedly adjusting stone tint, roof-tile counts or ember brightness. Obtain reference imagery of a real historic masonry smithy before redesign. Only the user can approve final artistic direction.
