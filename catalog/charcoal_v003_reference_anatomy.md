# Project Genesis | Carbón vegetal — dirección de arte V003

**Estado:** CANDIDATO, no aprobado. **Objeto:** carbón vegetal de madera maciza (no carbón mineral, no briqueta compactada).

## Observación anatómica

- El carbón conserva longitudinalmente las fibras, los vasos y parte de la estructura de la madera.
- Las grietas de contracción siguen en gran medida los radios de la madera y líneas anatómicas; las roturas principales deben poder seguirse del extremo al lateral.
- El corte transversal muestra estructura concéntrica de crecimiento y radios, con roturas oscuras que parten desde zonas próximas a la médula.
- El lateral muestra delaminaciones fibrosas, desprendimiento de escamas y astillas de longitud dominante axial.
- **Nunca** rayar con Voronoi aleatorio ni esculpir como una ico-sphere con fracturas de piedra.

## Referencias

1. Escaneo fotogramétrico CC0: **Burnt Log 01** (BlendKit): https://www.blendkit.com/asset-gallery-detail/17587d63-20b3-4bb4-a490-caa5725dbb68/ — referencia de forma; no se descargó ni copió la geometría.
2. Artículo de anatomía (Baraúna et al. 2021): https://bioresources.cnr.ncsu.edu/resources/the-effect-of-carbonization-on-the-wood-anatomy-of-sclerolobium-paniculatum-vogel/ — referencias de las fisuras radiales y tangenciales.
3. Microfotografía / anatomía comparada: https://www.scielo.cl/article_plus.php?lng=es&pid=S0717-92002021000100033&tlng=en
4. Foto macro: https://www.caryinstitute.org/news-insights/blog-translational-ecology/biochar-revisited — referencia de grietas / direcciones (no usada como textura; derechos conservados por la fuente).
5. Referencia multiángulo de distintas piezas para estudio visual, **no** textura incorporada: https://www.gettyimages.com/

## Pipeline automático

- Source: `scripts/charcoal_anatomic_master_v003.py` (Blender 4.5 LTS).
- La V003 tiene seis sectores anatómicos radiales desiguales con grietas que atraviesan el volumen, fisuras y astillas exteriores orientadas por la fibra.
- PBR real exportable a GLB: basecolor, normal y roughness (2 familias de mapas: pared longitudinal y testa).
- 5 vistas: tres cuartos, lateral, extremo frontal, extremo posterior, macro de fibras.
- Fuente editable y GLB se guardan en el artefacto de GitHub Actions; las previews publicadas NO son aprobación ni integración.

## Criterios de aceptación

1. Lectura evidente de **madera carbonizada** tanto a escala de ícono como en primer plano, sin parecer roca o madera fresca pintada.
2. Fracturas geométricamente coherentes entre tapa y costados, sin rebanadas demasiado regulares.
3. Interior negro profundo, exterior gris negruzco con brillo local tenue; no apariencia plástica ni roca sintética.
4. Sin partículas flotantes, UVs rotos ni seams antinaturales en caras iluminadas.
5. Revisión artística manual en las cinco vistas; score mínimo 8/10 para considerar integración.
6. Mantener fuera de `gburdesedev/Project-genesis/assets/playcanvas/approved/` hasta aprobación.

**Importante:** Los enlaces comerciales y científicos son **referencias visuales**, no recursos PBR importados. Las texturas actuales son originales procedurales y requieren validar su realismo en render.
