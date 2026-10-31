# PROJECT GENESIS — Materiales de tutorial de Herrero
**Tablero de producción 3D · 31/10/2026**

**Estado de integración:** todos los modelos son candidatos de producción. Ninguno aprobado por el artista ni integrado al juego. La versión activa de Project Genesis no se modifica.

## Líneas de producción y versiones

| Asset | Rama propia | Última iteración | PBR fotográfico CC0 | Estado técnico / revisión |
|---|---|---|---|---|
| Madera seca de roble | [asset/tutorial-roble_seco](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-roble_seco) | **V004** | [Oak Veneer 03](https://polyhaven.com/a/oak_veneer_03) + [Jolcham Oak Bark 01](https://polyhaven.com/a/jolcham_oak_bark_01) | Construcción/QA en [Actions](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/workflows/tutorial-material-per-branch-v001.yml); revisión artística pendiente |
| Madera seca de fresno | [asset/tutorial-fresno_seco](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-fresno_seco) | **V004** | [Ash Veneer](https://polyhaven.com/a/ash_veneer) + [Bark Brown 02](https://polyhaven.com/a/bark_brown_02) | Construcción/QA en [Actions](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/workflows/tutorial-material-per-branch-v001.yml); corteza fotográfica no certificada específicamente como fresno |
| Cuero bovino curtido | [asset/tutorial-cuero_bovino](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-cuero_bovino) | **V003** | [Brown Leather](https://polyhaven.com/a/brown_leather) | GLB/PBR/5 vistas producidos; color, grano y canto pendientes de revisión artística |
| Cuero caprino curtido | [asset/tutorial-cuero_caprino](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-cuero_caprino) | **V003** | [Brown Leather](https://polyhaven.com/a/brown_leather) | GLB/PBR/5 vistas producidos; el escaneo de cuero no certifica procedencia caprina |
| Cordel de cáñamo | [asset/tutorial-cordel_canamo](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-cordel_canamo) | **V003** | [Hessian 380](https://polyhaven.com/a/hessian_380) | Tres cabos geométricamente helicoidales, textura fotográfica de yute análoga; evaluación artística pendiente |
| Hilo de lino | [asset/tutorial-hilo_lino](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/tree/asset/tutorial-hilo_lino) | **V003** | [Rough Linen](https://polyhaven.com/a/rough_linen) | Madeja de dos cabos; fuente fotográfica es tejido, no hilo tridimensional escaneado; revisión pendiente |

## Contrato artístico y de integridad

1. **Realismo y fracturas**: los leños deben mostrar fibras rotas longitudinales, corteza externa, grietas radiales del secado y anillos coherentes en el extremo. En los cueros las marcas proceden de arrugas de flexión y cortes reales, no fracturas pétreas. En fibras las separaciones deben corresponder a la torsión.
2. **Fuentes reales y permisos**: escaneos PBR descargados desde la API oficial de Poly Haven. CC0. La forma 3D es modelado específico en Blender; no es fotogrametría volumétrica del objeto.
3. **GLB auditable**: mapas reales de albedo, normales y rugosidad, malla UV, imagen PNG RGBA, master .blend editable y procedencia con hashes.
4. **Control de vista**: hero, lateral, superior, trasera, macro y poster de inventario + contact sheet. La calidad visual la evalúa una persona; el QA técnico no asigna 8/10 ni licencia para producción.
5. **Versionado**: V001 primer lote; V002 reparó rutas de escaneo faltantes y detecta fallback rosa; V003 mejoró las siluetas y la geometría de fibras. V004 trata exclusivamente las maderas, con mapas de caras partidas y anillos radiales. Cada versión permanece disponible en Git; no reemplazar referencias aprobadas del juego.
6. **Paralelismo**: cada rama activa un runner de Blender 4.5.13 independiente al publicar cambios. No se copian los modelos candidatos a la rama principal ni se altera PlayCanvas antes de validación artística.

### Dónde revisar por material
Dentro de cada rama, consultar `production/tutorial_materials/generated/<asset_id>/`: `hero.png`, `side.png`, `top.png`, `back.png`, `macro.png`, `inventory_poster_rgba.png`, `multi_view_contact_sheet.jpg`, `<asset_id>_vNNN_candidate.glb`, `<asset_id>_vNNN_master.blend`, `VNNN_AUDIT.json` y `source/provenance.json`. Si el workflow está en ejecución, consultar el artefacto de Actions y no asumir que el archivo nuevo ya está confirmado.

**Objetivo de aprobación:** calidad visual >=8/10 después de revisión real del render, sin simplificar ni relajar las pruebas técnicas.
