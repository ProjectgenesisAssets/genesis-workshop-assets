# Project Genesis — Política obligatoria de optimización de assets aprobados

**Fecha:** 2026-11-04 · **Alcance:** assets 3D para PlayCanvas/WebGL; primer caso, puerta Herrero V082-B.

## Límite visual vinculante
- **Pérdida visual máxima admitida: 2,5 %.**
- **Objetivo conservador: ≤1,5 %** y, siempre que sea posible, cero pérdida visual.
- Nunca tratar reducción de megabytes como aprobación artística.
- Prohibida la integración automática de candidatos; el usuario decide después de ver renders comparativos reales.
- El original aprobado siempre permanece intacto, con SHA/versión registrado.

## Protocolo de comparación
1. Medir origen y candidato: tamaños reales, triángulos, materiales PBR, draw calls, texturas, CPU/GPU.
2. Aplicar primero compresión **sin pérdida** con igualdad exacta de píxeles (incluido canal alfa) y geometría.
3. Sólo si no alcanza el peso deseado, evaluar una variante con pérdidas mínima bajo techo de 2,5%; ninguna métrica técnica individual equivale por sí sola al porcentaje de calidad visual.
4. Renderizar original/candidato en **Blender 4.5.13 LTS, Cycles**, mismo HDRI EXR/RGBE de 32 bits, cámara, exposición y PBR. Mostrar frontal, trasera, lateral, tres cuartos y acercamientos a bisagras/remaches.
5. Verificar importación y materiales del GLB en PlayCanvas real, PC y móvil, sin alterar geometría aprobada.
6. Si no se puede establecer que la degradación visual permanece dentro del límite, **rechazar la candidata** aunque descargue más rápido.

## Estado actual
- Original V082-B: **15.887.816 bytes**, SHA Git `eef69d28dd8d53b5934442279a8b027bdfbfa157`.
- Auditados: 25.720 triángulos; 5 materiales; 15 texturas, que ocupan el 93,99% del GLB.
- Primer candidato experimental lossless WebP: **13.428.744 bytes** (−15,48 %) con 5 texturas sustituidas, píxeles equivalentes, geometría sin cambios.
- **No aprobado ni integrado.** Candidatas siguientes y pruebas PlayCanvas/Cycles pendientes de evidencia.

**V018:** no usar ningún modelo optimizado hasta completar los seis pasos y recibir aprobación explícita.
