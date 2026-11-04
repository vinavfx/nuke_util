# Reglas del ordenador de nodos

Base anterior a los cambios del 29 de octubre de 2026. Excluye la prioridad del input 0, la compactación ampliada y el cálculo de separación
por columnas incorporados ese día. No autoriza revertir esos cambios: cualquier discrepancia con el código debe señalarse antes de editar.

## Alcance y seguridad

- Ordenado determinista, sin IA ni azar.
- Ordenar solo los nodos indicados; desde el menú, la selección o, si está vacía, el contexto actual.
- Conservar las conexiones lógicas. Eliminar los Dots incluidos reconectando sus extremos y crear únicamente los Dots necesarios. No crear
  nodos de proceso.
- No modificar nodos fuera del alcance solicitado. La operación del menú debe poder deshacerse en un único paso de Undo.

## Disposición

- Unificar el tamaño de fuente de los nodos ordenados, Dots nuevos y Viewers a 11; mantener los backdrops a 20.
- Mantener un tronco vertical, con la salida abajo y ramas equilibradas a ambos lados. La rama no máscara con mayor peso continúa por el
  tronco; esta base no impone prioridad al input 0.
- Favorecer conexiones a 90°. Ocultar las conexiones compartidas que no puedan quedar limpias; usar un Dot oculto junto al destino cuando
  tenga varias entradas. Los Dots ocultos verticales deben quedar a 78 px del centro del destino cuando haya espacio, sin heredar el
  estiramiento de las filas del árbol ni modificar los Dots de enrutado.
- Compactar cadenas simples por input 0 únicamente si el origen no tiene otras salidas, ambos nodos cumplen las condiciones de cadena y su
  altura lo permite. Unidad vertical: 26 px; separación mínima: 6 px.
- Mantener las ramas cerca del tronco: ante conflictos, extender el tronco hacia arriba antes que alejar las ramas. Reservar unos 150 px
  entre bloques cuando sea necesario.
- Con cuatro o más entradas, colocar dos ramas pequeñas a los lados y las restantes en una fila superior, con las ramas grandes hacia el
  centro y altura proporcional al ancho.

## Backdrops

- Registrar sus miembros antes de mover nodos. Después ajustar cada backdrop al mayor conjunto próximo de miembros originales; eliminarlo si
  quedan menos de dos. Distancia de agrupación: 150 px.
- Respetar los anidados y apartar nodos ajenos cuando sea posible, desplazando sectores (unidos por enlaces visibles o virtuales) sin romper
  las alineaciones.
- Unificar etiquetas al formato de la skill `workflow-to-gizmo` (título `size=4` y descripción opcional `size=1` en cursiva, Bitstream Vera
  Sans), fuente 20, margen interior de 40 px más una línea de cabecera por línea de etiqueta y separación exterior de 30 px.

## Relaciones y nodos sueltos

- Mantener juntos los gizmos ComfyUI y sus Reads relacionados mediante enlaces virtuales, sin modificar conexiones reales ni crear ciclos.
- Colocar Backups y Restored a la derecha: máximo diez por fila, 100 px en horizontal y alto del Read más 20 px en vertical.
- Relacionar Write y Read por archivo, normalizando secuencias. Admitir Writes del primer nivel interior de Groups y gizmos.
- Agrupar cadenas aisladas de hasta tres nodos: Inputs para Reads unidos por input 0; Trash para otras cadenas con una sola entrada
  conectada por nodo, en cualquier índice. Excluir relaciones externas por conexiones, expresiones o Link_Knob y los Reads relacionados.
- Identificar el árbol principal con el mismo criterio que el output del Viewer: mayor número de nodos aguas arriba; desempatar por posición
  vertical de la salida y nombre. Situarlo debajo de los demás árboles.
- Colocar Inputs y Trash justo encima del principal, alineando el borde izquierdo del conjunto con el del árbol. Reservar el ancho de ambos
  backdrops y situar los árboles secundarios a su derecha, con sus salidas en una misma línea junto a la base de los backdrops. No usar las
  filas adicionales de Backups y Restored para alinear las salidas. Máximo diez cadenas por fila; 20 px entre columnas, 10 px entre nodos y
  40 px entre filas. Las cadenas mayores permanecen como workflows independientes.

## Casos de ordenado

- Guardar los casos en `arrange_nodes_cases/`, como archivos `.nk` con un índice correlativo: `case_001.nk`, `case_002.nk`, etc. Usar el
  siguiente índice disponible, sin sobrescribir casos existentes.
- Cuando el usuario pegue un grupo de nodos y pida guardarlo como caso, usar `save_arrange_case.py` para aligerarlo y guardarlo; no
  ordenarlo todavía. El script acepta un archivo `.nk` o `-` para leer la entrada estándar, asigna el siguiente índice y no sobrescribe
  casos. No requiere Nuke ni ejecuta los callbacks o las expresiones del flujo.
- Conservar los nodos del nivel principal, sus posiciones y conexiones, para reproducir el caso de ordenado.
- Vaciar el interior de todos los Groups, conservando únicamente sus nodos Input. Mantener los knobs de cada Group, incluidos los
  personalizados, y las conexiones externas a sus entradas.
- Vaciar el knob `file` de todos los Reads que se conserven para evitar errores por rutas a archivos no disponibles.
- Estos `.nk` son únicamente casos de ordenado: no necesitan procesar imágenes ni conservar el funcionamiento interno de los Groups.

Desde este directorio: `python3 save_arrange_case.py /ruta/al/flujo.nk`. Para elegir otra carpeta de destino, usar `--output-dir`.

## Viewer e importación

- Reemplazar los Viewers solo al ordenar sin selección: crear uno debajo del output estimado del árbol principal. No reemplazarlos desde el
  importador.
- Al importar workflows, conservar la disposición original como punto de partida, ordenar cada subgraph y después el root, únicamente sobre
  lo importado. Si se añaden nodos dentro del gizmo, volver a ordenar su contenido.
