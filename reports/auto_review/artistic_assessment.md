# Project Genesis — revisión artística de candidatos PlayCanvas/WebGL
**Fecha:** 27/10/2026, ~01:55 ART. **Estado:** evidencia visual revisada; ninguna aprobación artística ni nota numérica.  
**Ámbito:** assets aislados; no Unreal Engine ni cambios al repositorio del juego.

## Fragua V017 — candidato, no promovido
- **Rama:** `production/auto-forge-open-hearth-glow-v017`.
- **Run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40451788071
- **Comparación real:** `reports/production_auto/forge-open-hearth-glow-v017/four_view_comparison.jpg` (primera fila V016, segunda V017).
- **Modificación real:** elevación de borde de campana 6,5 cm; séptima hilada en pilares; más iluminación local y emisión en grietas del carbón.
- **QA:** 68.562 triángulos, 16 imágenes GLB, cuatro vistas, comparación con **V016** correcta, variación RGB 0,00415–0,01903; validación técnica aprobada.
- **Juicio artístico:** el acceso frontal mejora ligeramente y el fuego se distingue algo más, pero el gran volumen trapezoidal negro continúa dominando la silueta y la estructura todavía se parece a una pequeña estufa/parrilla. Los cursos de mampostería siguen demasiado regulares. **No declarar mejora sustancial ni 8/10**. Preservar V016 y V017; próxima intervención debe replantear físicamente campana/silueta o aparejo, no sólo elevar brillo.

## Fuelle V016 — candidato, no promovido
- **Rama:** `production/auto-bellows-grain-hide-drift-v016`.
- **Run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40451717414
- **Comparación real:** `reports/production_auto/bellows-grain-hide-drift-v016/four_view_comparison.jpg` (primera fila V015, segunda V016).
- **Modificación real:** tinte más cálido en madera fotografiada, contraste de cuero marrón y fase de pliegues con variación espacial.
- **QA:** 18.540 triángulos, 12 imágenes GLB, cuatro vistas, comparación con **V015** correcta, variación RGB 0,00320–0,00496; validación técnica aprobada.
- **Juicio artístico:** el tono mejora poco; la tabla superior continúa pálida/grisácea, sin lectura clara de veta longitudinal de roble. Los pliegues laterales siguen pareciendo bandas rígidas de caucho o madera en vez de cuero flexible cosido. **No promover sobre V012 provisional por mera ejecución**. Próxima corrección requiere resolver la lectura material/UV de la tapa y la geometría de cuero, no repetir variaciones mínimas de color.

## Puerta V011 — sin nueva iteración
- **Run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40435141349
- **Comparación V010→V011:** 68.028→38.768 triángulos evaluados (−43,01%), similitud de silueta >0,998 en las cuatro vistas.
- **Juicio artístico:** el frente y la vista lateral están disponibles; la conexión física de pomo, bisagras y cerrojo y el acabado metálico siguen pendientes de inspección cercana. No hay defecto nuevo confirmado suficiente para disparar un clon. Sin aprobación.

## Yunque V022 — sin nueva iteración
- **Run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40430776892
- **Juicio artístico:** la vista tres cuartos del panel actual permite reconocer un yunque con cuerno y cara de trabajo, pero falta contraste directo V021→V022 a igual encuadre para atribuir mejoras o defectos geométricos. No modificar por suposición. Sin aprobación.

## Espadas — no integradas
- **Auditoría documental:** `production/sword-families-fabrication-candidates-20261027`, `production/SWORD_FAMILIES_PENDING_20261027.md`.
- **Bloqueo real:** este repositorio no contiene el archivo fuente propio V023 ni las mallas de Fab; no hay GLB de espada validado. No sustituir por SVG ni editar menús concurrentes del repositorio `gburdesedev/Project-genesis`.
- **Regla:** las familias determinan geometría, la rareza no crea siluetas ni ornamentación extra.

## Estado de la cadena
- `scripts/prepare_art_review.py` en main actualizado: ordena candidatos por finalización real y rechaza vistas heredadas de otra versión.
- El paquete de 16 vistas anterior se generó correctamente a las 04:46 UTC con V016 de fragua y V015 de fuelle; la siguiente ronda de handoff debe incorporar V017/V016.
- La QA de **estos dos nuevos candidatos** ya compara con la versión inmediatamente anterior; las QA de versiones anteriores usaron referencias antiguas, por lo que no deben citarse como prueba de progreso incremental.
- **Aprobación final:** sólo Gabriel; nunca asignar puntuación automática ni declarar assets definitivos.
