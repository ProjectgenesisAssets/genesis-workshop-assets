# Project Genesis — Cuero caprino V020 | Revisión artística

Fecha: 2026-11-04
Estado: **CANDIDATO RECOMENDADO, PENDIENTE DE APROBACIÓN DEL PROPIETARIO**

## Alcance
- Base: `V019_distinct_candidate` sin reemplazar ni modificar.
- Nuevo: `V020_roughness_only`.
- Cambio único: canal verde del mapa PBR metallicRoughness +15/255, con saturación; se conservan malla, UV, normales, albedo y silueta.
- Se generaron GLB web y maestro de prueba; **ninguno integrado a PlayCanvas**.
- Iluminación: `studio_small_09_2k.hdr` genuino, HDR/RGBE de Poly Haven, intensidad 0.82.
- Blender: **4.5.13 LTS**, Cycles, cinco vistas en PNG y EXR de 32 bits/canal.
- V019 y V020 se renderizaron en el mismo workflow, con cámaras idénticas.

## Evidencia
- GitHub Actions: https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/41838383975
- Artefacto: `genesis-caprino-v020-hdri32-visual-QA`
- QA automático de GLB/PNG/EXR: **success**
- Tamaño GLB web V020: 6,057,508 bytes.
- SHA-256 V020 GLB web: `5aaeb196738d9b70cbce32102aad9ef4562b4da88550e08a2aea03ca061dca37`.

## Evaluación visual del asistente (no aprobación de usuario)
**8.2/10.** El cambio de rugosidad reduce discretamente los reflejos y conserva el grano característico y la forma natural del rollo y la solapa. Persiste un reflejo algo marcado en la cavidad interior, pero no justifica otra iteración a esta escala: preferible revisar el GLB en el visor de PlayCanvas cuando se integre, antes de introducir alteraciones adicionales.

**Decisión:** recomendar V020 para la revisión final del propietario. No promover ni marcar como aprobada hasta que la evalúe expresamente.
