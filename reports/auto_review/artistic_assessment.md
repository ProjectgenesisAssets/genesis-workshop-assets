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

## Ronda ~02:55 ART — Fragua V018: QA técnica correcta, revisión artística RECHAZADA
- **Rama:** `production/auto-forge-open-throat-hood-bonded-rear-v018`; **run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40457244321.
- **Comparación realmente inspeccionada:** `reports/production_auto/forge-open-throat-hood-bonded-rear-v018/four_view_comparison.jpg` (fila superior V017; inferior V018).
- **QA:** 68.474 triángulos, 312 mallas, cinco materiales texturizados, 16 imágenes GLB, cuatro renders; diferencia RGB 0,00468–0,02128 respecto de V017; aprobación **técnica** únicamente.
- **Resultado artístico:** la apertura central del frente dejó una discontinuidad grande entre el conducto y los laterales. En tres cuartos se ve como una campana rota/incompleta, no como una solución artesanal funcional. El aparejo posterior de bloques grandes y pequeños sí rompe algo la repetición, pero introduce parches claros aislados. **No promover V018 sobre V017**; conservar V018 como prueba descartada.
- **Próxima intervención justificable:** rediseñar un frente de campana CONTINUO con captación real de humo, sin techo de parrilla ni abertura que parezca pieza faltante; mantener mampostería sin parches claros sueltos. No repetir V018 ni aprobar por el workflow.
- **Nota:** el fuelle V017 tuvo un primer fallo real de arrays `(1048576,)` vs `(1024,1024)` en run 40457252233. Se despachó corrección exacta de `fibres.reshape(-1)` en nueva rama `production/auto-bellows-oak-grain-gusset-array-fix-v017`, run 40457420163; pendiente QA/render y revisión artística.
- **Espada:** se recuperó el artefacto V023 original del repositorio privado de modelado, sin modificarlo. GLB real: 80 mallas, 16 materiales, 1 imagen; separación pomo–empuñadura ~19,06 mm. Ver auditoría ampliada en rama `production/sword-families-fabrication-candidates-20261027`. Sin integración en juego.

## Ronda ~02:56 ART — Fuelle V017: reparación técnica exitosa, sin aprobación artística
- **Rama de reparación:** `production/auto-bellows-oak-grain-gusset-array-fix-v017`; **run:** https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40457420163. El primer intento V017 falló por incompatibilidad de formas NumPy y se preservó su run fallido; la corrección exacta se verificó ejecutando Blender real.
- **Comparación inspeccionada:** `reports/production_auto/bellows-oak-grain-gusset-array-fix-v017/four_view_comparison.jpg`, fila superior V016 e inferior V017.
- **QA:** 19.152 triángulos, 37 mallas, cinco materiales, 12 imágenes GLB, cuatro vistas, GLB y BLEND disponibles en artefacto; diferencias RGB 0,00529–0,00823; validación técnica superada, silueta no medida por fondo opaco.
- **Juicio artístico:** las arrugas de cuero tienen cierta irregularidad longitudinal adicional, pero todavía parecen tres franjas gruesas en vez de un fuelle cosido y flexible. La tabla superior aparece **aún más gris/pálida** que en V016; el intento de reescalar el mapa fotográfico de roble no resolvió la lectura material. **No promover V017 ni retirar V012 provisional**. Requiere rehacer UV y relieve/veta visible del tablero, no otra variación numérica mínima de tinte.
- **Handoff confirmado:** run https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40457978744 publicó `reports/auto_review/latest.json` a las 05:54:39 UTC con 16 imágenes y referencias exactas a **fragua V018, fuelle V017, puerta V011, yunque V022**. Sigue siendo un paquete de evidencia, NO una aprobación.
