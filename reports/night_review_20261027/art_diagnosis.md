# Project Genesis — revisión cualitativa de cuatro assets (26/27 octubre 2026)

**Fuente visual:** `previews/night_review_20261027/all_four_contact_sheet.jpg` — dieciséis imágenes reales de Cycles obtenidas de ramas aisladas de GitHub Actions, reducidas únicamente para inspección. No se ejecutó Blender fuera de GitHub.

## Puerta medieval
- Candidato inspeccionado: V010; V011 geométrica en `production/door-v011-triangle-budget` pendiente de nueva comparación.
- Silueta de arco, bisagras, aro y cerrojo legibles; vista lateral confirma espesor físico.
- Reverso presenta refuerzo en X y placa. No declarar aprobación antes de comprobar que la optimización de ~68.028 triángulos no altera silueta ni herrajes.
- Corrección técnica ejecutada: reparar el workflow V011 para usar el generador, salidas y GLB V011, en lugar de volver a generar V010.

## Fuelle
- Candidato inspeccionado: V011 `production/bellows-v011-baked-oak`.
- Defecto artístico concreto: los pliegues laterales de cuero se confunden cromáticamente con tablillas de madera; aspecto excesivamente laminado, poca diferenciación de materiales.
- Corrección programada, no aprobada: `production/auto-bellows-leather-pbr-contrast-v012`, desde la cola, genera un albedo fotográfico de cuero oscurecido/oxblood y lo vincula directamente al material PBR del GLB. Comprobar GLB y cuatro renders antes de aceptar.

## Fragua
- Candidato inspeccionado: V010 `production/forge-v010-rear-mortar`.
- Construcción de ladrillo y campana trapezoidal legibles; base, boca y conducto identificables. Mortero posterior y apoyos parecen físicamente coherentes.
- Defecto artístico concreto: el lecho de carbón se ve mayormente apagado; no comunica una fragua activa.
- Corrección programada, no aprobada: `production/auto-forge-ember-fracture-readability-v011`, aumentar moderadamente la emisión de microfisuras del propio carbón y la iluminación indirecta; sin esferas de brillo desprendidas.

## Yunque
- Candidato inspeccionado: V022 `production/yunque-v022-forged-horn`.
- Cuerno, cara de trabajo, talón con agujero cuadrado y base distinguibles; metal cepillado en cara superior y hierro más oscuro en cuerpo.
- No se identificó con suficiente certeza un defecto que justifique modificar el generador sin pruebas adicionales. Conservar V022 y su catálogo de 16 vistas como mejor candidato técnico; **sin aprobación artística automática**.

## Reglas de promoción
La existencia de renders, un GLB válido o una comparación de píxeles positiva no demuestra calidad 8/10. La promoción final requiere inspección de las cuatro vistas y aceptación del usuario. No tocar versiones aprobadas ni repositorios privados. Los cambios se aplican en ramas separadas y la fecha límite es el 27/10/2026 a las 09:00 ART.
