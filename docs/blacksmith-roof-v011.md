# Project Genesis — Herrería, cubierta V011 (Blender)

**Estado:** candidato experimental, aún sin aprobación visual ni integración en PlayCanvas.

La herrería V010 tenía cuatro paredes, pero carecía de un techo concebido específicamente para esas dimensiones. La V011 añade la cubierta sin sustituir los modelos aprobados dentro del juego.

## Arquitectura y dimensiones de referencia

- Ancho del cuerpo: 7,875 m; fondo 6,890625 m, muros hasta 3,20 m en coordenadas Blender.
- Techo a dos aguas, cumbrera paralela al eje de profundidad (Y).
- Alero 3,29 m; cumbrera 4,87 m; vuelo lateral 0,39 m.
- Tejas/pizarras partidas irregulares, oscurecidas por hollín; textura escaneada PBR CC0 con normal y rugosidad.
- Armadura de madera vieja: cabios, tirantes, viga de cumbrera y dos frontones con ventilación. El tejado se separa del interior para cámara y jugabilidad.
- Chimenea **candidata**, en la mitad trasera izquierda: recorte físico de la cubierta y remate de hierro; la chimenea es una pieza independiente que puede recolocarse cuando se compruebe la alineación con la fragua V038.

## Entregables

`genesis_blacksmith_roof_v011.glb`, `genesis_blacksmith_chimney_candidate_v011.glb`, `genesis_blacksmith_roof_and_chimney_v011.glb` y escena Blender completa, además de los GLB de paredes individuales.

Ocho renders: frente, tres cuartos, techo cenital, frontón, lateral, trasera, vista del interior sin techo y detalle de chimenea.

## No modificar ni aprobar todavía

La V011 NO cambia la puerta aprobada, la fragua, las colisiones, los puestos de trabajo ni el techo original del juego. La chimenea aún no está conectada funcionalmente con la fragua. Antes de homologar hay que comprobar en el motor PlayCanvas las dimensiones finales y las coincidencias reales de coordenadas, el interior sin colisiones extra, la perspectiva del techo, los materiales y FPS.

**Criterio visual:** realista PBR, no stylized, nada de copias perfectas, muros sólidos, unión de piedra y madera y techumbre que resulte plausible sobre el taller.
