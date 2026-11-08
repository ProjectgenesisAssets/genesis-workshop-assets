# Resultado de fabricación V4 — datos dinámicos (experimental)
Se conserva el arte V2/V3 elegido, sin alterar imágenes ni ORA. Este módulo es un **adaptador de datos** para conectar el resultado final de fabricar() con la UI; no implementa por sí solo el renderizador PlayCanvas.

**Entrada:** un registro definitivo por objeto: id, recetaId, nombre, rareza, asset.glb, asset.animationClips, canales [{id,nombre,valor,ordenObtencion,tecnicas}], visualFx [{canalId,intensity,animationClip,materialPreset}], descripcionNGE, createdAt.

**Salida:** título del objeto, insignia de rareza, filas en orden de adquisición (no alfabetizadas ni ordenadas por valor), subefectos bajo su canal padre, GLB original, clips y efectos, rotación 360°.

**Reglas:** no recalcular al abrir pantalla; persistir snapshot junto con el objeto del inventario; no inventar canales ni modificar valores; no agregar ornamentación por rareza; usar VFX/materiales de canales reales sobre el mismo modelo base; permitir colapsar/desplegar técnicas por canal; descripción fija y panel de canales desplazable; GLB no cargado -> error controlado, sin reemplazar el asset; no tocar main.

**Validación actual:** pruebas locales Node del módulo equivalente realizadas el 7 de noviembre de 2026. **No verificado** como pantalla integrada, carga GLB real, animaciones, ni giro 360° en PlayCanvas. La integración debe hacerse en rama experimental del juego al identificar los nombres reales de sus eventos y registros.
