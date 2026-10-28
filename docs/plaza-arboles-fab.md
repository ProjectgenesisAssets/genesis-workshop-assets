# Project Genesis — árboles AAA para la plaza (PlayCanvas)

## Fuente y licencia

- **More Realistic Trees Free!** — **Nicholas 3D**.
- Fab: https://www.fab.com/listings/d9a40b15-46e7-41f9-ac46-99b487ddea60
- Licencia indicada por el autor en Fab: **CC BY 4.0**. Conservar la atribución cuando se use o distribuya el asset.
- Los originales (ZIP de Fab y conversión GLB) se preservan fuera de esta rama; aquí hay únicamente código reproducible y resultados temporales de Actions.

## Criterio de optimización de Gabriel

**El 8% NO es un límite de reducción de polígonos.** Podemos quitar incluso un millón de triángulos si el aspecto no se deteriora perceptiblemente. Hay que conservar silueta, volumen de copa, ramas visibles, materiales, texturas y UV.

Este pipeline compara cada candidato con la **misma fuente intacta** desde cinco cámaras ortográficas idénticas, incluida una vista de detalle de la copa. Prueba por defecto conservar 50%, 30% y 15% de los triángulos, y selecciona **la mayor reducción que supera todos los controles**. Estas son propuestas: ninguna se aprueba automáticamente.

Controles objetivos conservadores:

| Control | Umbral |
| --- | ---: |
| Solapamiento de silueta (IoU) en todas las vistas | >= 98% |
| Diferencia media de color del objeto (normalizada) | <= 8% |
| Similitud estructural SSIM de cada vista | >= 0,92 |
| Materiales, imágenes, texturas, UV y nodos de malla | Sin pérdidas detectadas |
| Fuente Fab real | Como mínimo 2 materiales y 5 imágenes al exportar |

**Importante:** ni SSIM ni una diferencia de color del 8% equivalen a medir exactamente un 8% de pérdida visual percibida. Son filtros automatizados. La aceptación definitiva exige revisión humana de Gabriel en PlayCanvas, incluyendo ramas y hojas en cámara de juego. El archivo `plaza_visual_qa.json` contiene cifras, rechazos y el candidato propuesto. `artist_approved` siempre permanece en `false`.

## Ejecución en GitHub

1. Crear/revisar la rama `feature/plaza-arboles-fab-8pct`. **Crear la rama no ejecuta Blender ni publica assets.**
2. Para ejecutar el modelo real, abrir **Actions → Plaza - Fab trees visual-preserving optimization → Run workflow** una vez incorporado el workflow a la rama predeterminada (GitHub exige esto para `workflow_dispatch`).
3. Indicar `asset_url`: un enlace de descarga **HTTPS** al ZIP original de Fab (admite ZIP anidado) o al GLB convertido. Opcionalmente, `sha256` para comprobar integridad.
4. `remaining_ratios`: por defecto `0.50,0.30,0.15`. Si falla el control visual, repetir con `0.90,0.80,0.70`; no hay límite fijo de reducción de polígonos.
5. Descargar el artefacto de Actions durante sus **2 días** de retención y revisar `baseline.glb`, `candidate_*.glb`, las imágenes en `views/` y `plaza_visual_qa.json`. El mejor candidato técnico, si existe, se copia como `plaza_arboles_candidate_playcanvas.glb`.

Los archivos de Fab **no están incorporados en GitHub**: el ZIP anterior está resguardado como archivo separado y todavía requiere una URL HTTPS descargable por Actions. No se modificó el repositorio principal de PlayCanvas ni se integró ningún árbol al mapa 13×13.

## Uso posterior en PlayCanvas

Una vez aprobado artísticamente el candidato, importar el GLB en PlayCanvas, configurar colisiones simples separadas del árbol y comprobar rendimiento, transparencia alfa de las hojas, iluminación, mipmaps y LOD en distancias de juego. La aprobación técnica de Actions **no** es autorización para publicarlo en el mapa.
