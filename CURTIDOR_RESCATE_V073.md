# Curtidor — rescate del concepto V073-B

Estado: **RESCATADO COMO CONCEPTO VISUAL; NO APROBADO NI INTEGRADO EN JUEGO**.

El usuario detectó que el aspecto orgánico, poroso y marrón oscuro del render original **V073-B** evoca cuero curtido, aunque fue creado como una prueba del Herrero. Se conserva intacto para iterar como posible puerta del Curtidor sin perder el trabajo previo ni modificar la rama del Herrero.

## Identidad visual conservada
- Render seleccionado: `previews/door_herrero_v073/B_full_metal_copper.png`
- Primer plano: `previews/door_herrero_v073/D_full_metal_copper_closeup.png`
- Fuente Blender reproducible: `scripts/puerta_herreria_art_073.py`
- Workflow reproducible: `.github/workflows/door-herrero-v073-preview.yml`
- Producción fuente: run 41246626704, resultado exitoso.
- Geometría ornamental V011 inalterada; ornamentos, bisagras, remaches y herrajes conservados.

## Qué es y qué no es
- Es un **concepto de cuero**, no un PBR físico de cuero aún.
- El shader V073-B emplea metalness alto, por lo que **no debe exportarse ni etiquetarse como cuero final**, aunque visualmente se le parezca.
- Para convertirlo a puerta funcional de curtidor: conservar lectura orgánica y paleta; usar **metallic=0 en la hoja de cuero**, roughness de cuero aceitado real, normales de grano/arrugas, subestructura física razonable; mantener herrajes metálicos.
- No modificar la puerta del Herrero para aplicar mejoras del Curtidor: ramas separadas.
- No eliminar ninguna referencia V073-B hasta que exista reemplazo aceptado.

## Referencias
- Render B: https://github.com/ProjectgenesisAssets/genesis-workshop-assets/blob/production/door-curtidor-v073-rescue/previews/door_herrero_v073/B_full_metal_copper.png
- Primer plano: https://github.com/ProjectgenesisAssets/genesis-workshop-assets/blob/production/door-curtidor-v073-rescue/previews/door_herrero_v073/D_full_metal_copper_closeup.png
- Prototipo actual: solo Blender/render; **GLB de esta variante aún no se exportó**, por lo tanto no está lista para PlayCanvas.

Fecha de rescate: 2026-10-31.
