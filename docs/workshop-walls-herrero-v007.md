# Project Genesis — herrería V007 · paredes modulares

Estado: **candidata experimental; no aprobada ni integrada al juego**.

## Fuente
Se conserva la pared frontal **Herrero V006**. Script: `scripts/genesis_blacksmith_workshop_v007.py`.

## Alcance real de la V007
- Frente: aspecto V006 preservado, vano de entrada libre.
- Lateral izquierdo: mampostería irregular compacta, dos ventanas estrechas con hierro forjado, zócalo estructural y cadena superior de madera.
- Lateral derecho: misma familia material con distribución independiente de ventanas y piedras.
- Trasera: mampostería cerrada y reforzada, ventana alta de ventilación; zona central de servicio de fragua despejada, pendiente de dimensionar respecto a V038.
- Esquinas: pilares continuos, base sólida; evitar piedras flotantes y patrón repetitivo.
- Techo: se preserva el techo actual del juego; **todavía no se ha validado encaje**, no hay techo nuevo generado.
- Puertas: malla aprobada NO modificada; vanos/colisiones pendientes de verificación visual en motor.

## Sistema de coordenadas
Blender local: X=anchura, Y=profundidad hacia atrás, Z=altura.
Dimensiones de la muestra de muros: 7,875 × 6,890625 × 3,2 (ancho × profundidad × altura), con factor lateral a comprobar frente al shell PlayCanvas que mide 12 × 10,5 y se escala ×0,75 en X/Z. Las medidas son **de referencia técnica del montaje**, no una homologación de gameplay. El vano frontal de la V006 conserva 1,48 × 2,43 en el asset.

## Entregables exigidos
Archivo .blend, GLB de conjunto, GLB individual del frente y GLB de lateral izquierdo, derecho y trasero. Renders: frontal, tres cuartos, lateral derecho, trasera, vista superior sin techo y detalle. Auditoría de materiales/polígonos y procedencia Poly Haven CC0.

## Criterios de aceptación
1. Estructura con aspecto macizo, juntas cerradas, sin grietas falsas o esquinas endebles.
2. Las ventanas no perforan pilares ni comprometen la circulación de la fragua.
3. Las cuatro paredes se conectan físicamente sin costuras visibles importantes.
4. PBR realista, no stylized; exteriores con variación moderada, evitar ladrillos uniformes.
5. Comprobar el techo, la puerta y la fragua V038 **en PlayCanvas** antes de sustituir paredes antiguas o colisiones.
6. Optimizar las texturas y evaluar FPS antes de homologar.
7. Se exige revisión visual humana; workflow verde por sí solo no equivale a 8/10.

Los demás oficios permanecen sin cambios en esta iteración.
