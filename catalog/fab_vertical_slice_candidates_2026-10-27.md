# Project Genesis — catálogo de candidatos externos para PlayCanvas

Actualizado: 2026-10-27 (hora argentina). Catálogo de evaluación; **ningún asset externo está integrado ni aprobado**. No copiar archivos privados o maestros al repositorio público.

## Fab: candidatos y función jugable

| ID | Fab | Precio observado | Uso propuesto | Prioridad | Pendiente |
|---|---|---|---|---|---|
| FAB-01 | [Medieval Assets / dimension Dazzle](https://www.fab.com/listings/5c03f0c6-2665-477a-aeef-916eed78de1a) | Gratis en ficha | Herramientas y props secundarios de herrería, decoración del taller | Alta | Inventariar piezas reales, licencia específica, mallas, PBR y GLB |
| FAB-02 | [Strong Medieval Anvil / Incg5764](https://www.fab.com/listings/d91e6544-a475-4ec2-8353-029e68ce947d) | Gratis en ficha | Competidor directo del yunque Genesis V022 | Alta | Comparación visual 4 vistas, triángulos, PBR 2K y licencia |
| FAB-03 | [Very Cool Medieval Sword / Incg5764](https://www.fab.com/listings/a2a1c080-9d77-4ce7-bcb0-1a5c302f6ce5) | Gratis en ficha | Referencia de acabado y familia de espada con ornamentación propia | Media | Triángulos, materiales PBR 4K, encaje en familias aprobadas |
| FAB-04 | [Ashen Oath Greatsword / NexVara](https://www.fab.com/listings/202054ca-4eda-45be-914a-8e2d66a699eb) | Captura del usuario muestra Personal gratis; verificar la opción vigente | Familia de espada distinta, exhibición de inventario/comparación si corresponde | Media | Confirmar licencia y acceso; FBX/Blend a GLB, PBR; ficha declara 5.790 triángulos |
| FAB-05 | [Sword / Gerardo Justel](https://www.fab.com/listings/f25cf33e-596b-4899-9e20-202f26999b68) | Gratis en ficha | Candidata para espada sobria del tutorial; comparar con Genesis V023 | Muy alta | Inspección de geometría, PBR, licencia y exportación GLB |
| FAB-06 | [Vintage Wooden Treasure Chest / dimension Dazzle](https://www.fab.com/listings/83aff177-a1d7-4ac6-8ecb-aeec05f27b1a) | Gratis en ficha | Cofre de tutorial Q1 llave/cofre, apertura y acceso a contenido | Muy alta | Licencia, tapa interior separable, pivote de bisagra, cerradura, colisiones y animación en GitHub Actions |

## Reglas de diseño y adopción

- Las **familias** determinan el diseño físico de las espadas. La rareza no agrega ornamentación ni crea nuevas formas.
- Un asset gratuito no se integra hasta verificar su licencia exacta, fuente original, geometría, materiales, tamaño de descarga y desempeño WebGL.
- Descargar, auditar, optimizar y animar **mediante GitHub Actions y Blender 4.5.13**, nunca mediante Blender local. No tocar el repositorio privado original ni el juego hasta autorización de integración.
- El cofre es candidato de gran impacto jugable; antes de prometer animación, verificar que tapa/candado puedan separarse y que exista interior útil.
- El yunque de Fab puede sustituir al nuestro sólo después de comparar V022 con el mismo encuadre e iluminación.
- Mantener únicamente los mejores checkpoints; **no adjudicar una puntuación artística automática**.

## Estado de nuestros modelos (snapshot nocturno)

| Asset | Último render completado técnicamente conocido | Observaciones artísticas |
|---|---|---|
| Puerta | [V011](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40435141349) | Optimización de geometría; aún sin aprobación |
| Yunque | [V022](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40430776892) | Comparar con FAB-02; sin aprobación |
| Fragua | [V012](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40440350279) | Usuario rechaza dirección demasiado stylized; revisión realista prioritaria. [V013 falló](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40441126043) |
| Fuelle | [V013](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/40440701246) | Usuario acepta sólo provisionalmente; inspeccionar diferencia madera/cuero |

Los enlaces de Actions acreditan ejecución, **no calidad final**. Para auditoría artística conservar PNG de 4 vistas y comparación con candidato anterior. La integración en PlayCanvas es una fase posterior.

## Orden de pruebas recomendado

1. FAB-06 cofre: validar malla, bisagras, colisiones y producir prueba de animación sin integrar al juego.
2. FAB-05 espada sobria: enfrentarla a V023 en catálogo idéntico.
3. FAB-02 yunque: enfrentarla a V022.
4. FAB-01: inventariar piezas individuales, licencias y costos WebGL.
5. FAB-03 y FAB-04: referencias de familias alternativas, sin dependencia con rareza.
