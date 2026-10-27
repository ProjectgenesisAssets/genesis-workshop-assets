# Project Genesis — familias de espadas candidatas para Fabricación
Fecha: 27/10/2026. **No integrado ni aprobado**.

## Estado comprobado
Este repositorio de producción pública de assets no contiene el modelo propio de espada V023 ni archivos fuente de las espadas de Fab. No se puede auditar su malla o publicar un GLB sin esos archivos. No tocar el juego ni el repositorio privado de modelado.

## Familias visuales propuestas (no son nuevas recetas)
- **Espada larga / sobria**: referencia propia V023 (fuera de este repositorio), y candidato Fab FAB-05 (https://www.fab.com/listings/f25cf33e-596b-4899-9e20-202f26999b68). Comparar longitud, sección, pomo, guarda, PBR y presupuesto de triángulos.
- **Espada corta**: candidatos FAB-07 (https://www.fab.com/listings/554f19f8-a5fb-4895-9cec-ab5edb7cca70) y FAB-08 (https://www.fab.com/listings/03994681-c1ac-445b-b616-54bd57cc6f17). Son competidores de una misma familia, no dos recetas nuevas.
- **Espadón**: candidato FAB-04 (https://www.fab.com/listings/202054ca-4eda-45be-914a-8e2d66a699eb), sujeto a licencia, auditoría y correspondencia con las familias canónicas.
- **Espada ornamentada**: FAB-03 (https://www.fab.com/listings/a2a1c080-9d77-4ce7-bcb0-1a5c302f6ce5) solo referencia; la rareza nunca determina ornamentos.

## Contrato de integración
La Fabricación genera un objeto real y único, con rareza y propiedades calculadas por el sistema existente. La familia determina la geometría base; la rareza NO cambia su silueta. El resultado del minijuego y el inventario no deben depender de un SVG de demostración. El GLB debe poder verse en Fabricación, Inventario y Comparación sin duplicar recetas ni alterar los cálculos.

Antes de integrar: verificar permisos/licencia del modelo externo, disponibilidad de malla descargable, UV, PBR, escala métrica, pivote, normales, coste WebGL y silueta en cuatro vistas; generar GLB con Blender 4.5.13 en GitHub Actions y comparar contra V023. Sin GLB validado, mantener el visor provisional **explícitamente provisional**.

**Próximo paso bloqueado por fuente:** obtener las mallas autorizadas de V023/Fab dentro del circuito de assets permitido; solo después se podrá generar candidatos y proponer un cambio aislado de integración al repositorio del juego, sin pisar el trabajo simultáneo de menús.

## Auditoría binaria real de la espada propia V023 — 27/10, ~02:50 ART
Se recuperó **en modo lectura** el artefacto real del repositorio privado del autor `gburdesedev/genesis-blender-render`, run `39705385028` (22/10, finalizado correctamente), sin modificar ese repositorio. **Corrección del bloqueo anterior:** la malla V023 sí existe en el repositorio privado de modelado, aunque todavía NO fue transferida a este repositorio autorizado de producción ni integrada en PlayCanvas.

- ZIP de fuente: `Genesis-Espada-V023-Vector-Modular` (artifact ID `12394836071`, no expirado al inspeccionar). Contiene `Espada_Concept_Base_HD_V023.blend` (10.311.905 bytes), `Espada_Concept_Base_HD_V023.glb` (4.789.576 bytes) y auditoría JSON.
- Cuatro renders originales recuperados: `Genesis-Espada-V023-Vector-Renders` (artifact ID `12395475260`): frontal, tres cuartos, macro guarda y macro pomo. Son evidencia REAL, pero no cumplen todavía las cuatro vistas estándar frente/tres cuartos/reverso/detalle.
- Lectura directa del GLB, sin ejecutar Blender: **80 mallas, 80 nodos, 16 materiales, 1 imagen, 2 entradas de textura y 0 animaciones**. La hoja y la empuñadura son geometría real; no es un SVG sustituyendo al objeto.
- **Defecto de pomo cuantificado:** en las coordenadas Y del GLB (eje Z de Blender), el extremo inferior de la empuñadura está en `-0.47920 m` y el extremo superior del cuerpo del pomo en `-0.49826 m`. Hay aproximadamente **19,06 mm de separación**, visible en el render. No se puede declarar el pomo unido.
- En el repositorio privado existe el script `scripts/corregir_pomo_espada_v025.py` y su workflow V025: desplaza el conjunto del pomo y crea una raíz rígida compartida, preservando las 80 mallas. **No hay aquí una exportación V025 validada**, por lo que sigue pendiente ejecutarlo y verificar cuatro vistas con Blender 4.5.13 en GitHub Actions.
- **PBR WebGL pendiente:** sólo una imagen embebida en el GLB de 16 materiales; varias superficies dependen de nodos procedurales que no se exportan íntegramente a glTF. Hace falta hornear y auditar materiales PBR antes de declarar calidad final en PlayCanvas.
- La espada propia V023 puede servir como **candidato geométrico** para una familia sobria, pero la silueta, guarda y ornamentos no deben cambiar automáticamente con la rareza. Los candidatos Fab siguen sujetos a licencia, descarga y auditoría individual.

**Integración segura:** mantener `gburdesedev/Project-genesis` intacto hasta contar con un GLB corregido, cuatro vistas nuevas, QA de pivote/UV/texturas y revisión de la última versión publicada del juego. No copiar enlaces temporales firmados ni credenciales del repositorio privado a workflows públicos. La autorización actual permite trabajar en este repositorio de assets; no equivale a aprobar visualmente V023/V025.
