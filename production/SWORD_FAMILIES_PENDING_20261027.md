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
