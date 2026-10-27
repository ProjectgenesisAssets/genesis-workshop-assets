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


## Ronda ~03:50 ART — correcciones estructurales V019/V018 en ejecución
- **Evidencia visual inspeccionada:** se abrieron los JPG reales `forge-open-throat-hood-bonded-rear-v018/four_view_comparison.jpg`, `bellows-oak-grain-gusset-array-fix-v017/four_view_comparison.jpg` y el contacto de 16 vistas de `reports/auto_review/latest_contact_sheet.jpg`. La fragua V018 tiene un hueco frontal de metal ausente y barra recta flotante; la V017 tenía una superficie frontal continua pero demasiado parecida a techo de parrilla. El fuelle V017 tiene tablero aún gris y tres pliegues demasiado uniformes. No se calificaron automáticamente.
- **Fragua V019, modificación de malla real:** `production/auto-forge-arched-smoke-capture-v019`, run https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40463461577. Sustituye las dos mejillas sueltas y el pequeño baffle por un solo faldón de hierro curvo y continuo, con arco inferior funcional; cambia la barra recta por un labio metálico que sigue el arco. Se preservan V017/V018. **Pendiente resultado Blender, QA y comparación V018→V019.**
- **Fuelle V018, modificación de albedo y pliegues:** `production/auto-bellows-oak-pigment-warped-fibres-v018`, run https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40463469162. Mantiene la muestra fotográfica CC0, centra luminancia, crea veta longitudinal deformada y usa pigmentos marrones cálidos; reduce amplitud de pliegues rígidos y varía fase local. Se preserva V012 provisional y V017. **Pendiente resultado Blender, QA y comparación V017→V018.**
- **Despacho real confirmado:** commit en `main` `98217c48351e10f2d5e99c936b0d2a136f08f38c` agregó dos tareas exactas (11 históricas en total) a `production/correction_queue.json`. Ejecutor GitHub Actions https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40463409414 finalizó correctamente y despachó ambas ramas. Los dos trabajos superaron validación del generador e instalación oficial Blender 4.5.13 y entraron a render Cycles. No son versiones terminadas ni aprobadas hasta comprobar artefactos y las cuatro vistas.
- **Puerta V011 / Yunque V022:** inspeccionados en el contacto de 16 vistas; no se inventaron defectos ni se lanzaron clones. La puerta conserva herrajes por revisar; el yunque necesita comparación V021 a igual encuadre. **Espadas:** auditoría V023 existente; sin cambio del repositorio del juego.


## Ronda 05:05–05:10 ART — revisión real V019/V018, nuevas iteraciones en Actions
- **Evidencia inspeccionada:** `reports/auto_review/latest_contact_sheet.jpg` (16 vistas) y comparaciones de dos filas `reports/production_auto/forge-arched-smoke-capture-v019/four_view_comparison.jpg` y `reports/production_auto/bellows-oak-pigment-warped-fibres-v018/four_view_comparison.jpg`. Las comparaciones son **V018→V019 fragua** y **V017→V018 fuelle**, no evaluaciones de puntaje.
- **Fragua V019:** el frente curvado y continuo corrige la discontinuidad de V018. Sin embargo, la campana de hierro todavía tiene un borde frontal negro muy ancho y lectura lateral de techo de parrilla; los remaches del labio estaban en línea recta mientras el labio es curvo. QA objetiva correcta (68.658 triángulos, cuatro renders, GLB/BLEND), **no aprobada artísticamente**.
- **Fuelle V018:** la madera pasó de gris fotográfico a **salmón/rosado con rayas paralelas sintéticas**, una regresión evidente. Los pliegues laterales aún parecen bandas de caucho. QA objetiva correcta (19.012 triángulos, cuatro renders, GLB/BLEND), pero **NO promover V018 sobre V012 provisional**.
- **Fragua V020:** corrección exacta `raised-smoke-arch-v020` en cola. Se elevó 7,5 cm la corona del arco de captación y se alinearon labio y remaches con la misma curva; rama aislada `production/auto-forge-raised-smoke-arch-v020`, [run 40471553016](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40471553016). **En render al registrar este informe; sin QA ni aprobación aún.**
- **Fuelle V019:** corrección exacta `umber-oak-natural-pores-v019`: reducción de amplitud de líneas sinusoidales de veta, mayor protagonismo de poros reales CC0 y albedo roble pardo umber menos rojizo; rama aislada `production/auto-bellows-umber-oak-natural-pores-v019`, [run 40471482266](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40471482266). **En render al registrar este informe; sin QA ni aprobación aún.**
- **Incidencia del ejecutor:** el [run 40471369792](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40471369792) terminó en verde, pero su recibo registra **HTTP 502** al despachar fragua y **HTTP 500** al despachar fuelle; verde no significa que los despachos funcionaran. Se recuperó creando commits verificables con generador corregido, recibo y activación por cambio del workflow en cada rama; ambas ejecuciones de Blender quedaron efectivamente iniciadas. No se corrieron modelos idénticos ni Blender local.
- **Yunque V021→V022:** comparación real de `previews/yunque_v021/hero.png` y `previews/yunque_v022/hero.png`: V022 presenta cuerno más delgado y puntiagudo; materiales y base similares. No hay defecto adicional suficiente para iterar sin propósito. **Puerta V011** sin cambios ni aprobación.
- **Espadas:** auditoría V023 y pomo separado ~19,06 mm documentados; sin GLB corregido/validado, sin integración ni modificación del repositorio del juego.
- **Regla de la ronda:** no hay aprobaciones >=8/10, no se promueven versiones por ejecución exitosa. Conservar V012 fuelle y todas las versiones anteriores como checkpoints.


### Verificación posterior — fuelle V019 (05:15 ART)
- [Run 40471482266](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40471482266) **finalizado correctamente**. QA: 19.012 triángulos, 37 mallas, cinco materiales, 12 imágenes GLB, cuatro renders y GLB/BLEND en artefacto; comparación directa V018→V019 con diferencias RGB 0,00504–0,00923.
- **Inspección de la comparación real:** desaparecen las rayas sintéticas rosas exageradas de V018 y reaparecen poros fotográficos; el tablero queda, sin embargo, beige/grisáceo y poco parecido a roble envejecido. El cuero sigue leyendo como bandas paralelas rígidas. **Mejora parcial del albedo respecto de V018, no mejora global demostrada ni aprobación. V012 continúa siendo referencia provisional.**
- [Handoff 40472113977](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40472113977) actualizó `latest.json` a las 08:14:28 UTC con 16 imágenes, incluyendo fuelle V019 y fragua V019 (V020 todavía en render). `art_review_completed=false` permanece correcto.
