# Forge V012 — four-view artistic rejection, 27 Oct 2026

Actual Blender 4.5.13 run 40440350279 completed successfully and produced four Cycles PNGs, editable .blend, GLB and PBR maps. The render was inspected against V011 run 40440087705.

**Observed improvement:** metal-dominant industrial hood and cylindrical flue were replaced by real stone masonry, a square open chimney and a stone foundation. This is a genuine geometric change, not a coal-emission-only rerender.

**Remaining major defect:** the hood reads as a tiled house roof, the square flue as stacked regular planks, and the whole construction as a miniature brick barbecue rather than a historically plausible heavy blacksmith forge. Thin metal front rods remain visually flimsy; charcoal glows too uniformly orange. Stone PBR still lacks convincing photographic detail. Do not promote or assign 8/10.

**WebGL concern:** V012 GLB is approximately 79 MB, disproportionately heavy for one menu/workshop asset. The next candidate must share/reduce PBR maps rather than proliferate duplicate 1536px textures.

**Next branch:** `production/auto-forge-photostone-mass-v013`, which changes masonry scale, stone supports, CC0 quarry-stone photographic PBR and ember intensity. Only promote after actual render and GLB audit; retain V012 as an experiment and V011 as the previous technical checkpoint.
