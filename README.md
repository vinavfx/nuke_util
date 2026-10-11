# Utilidades de Nuke

Biblioteca compartida organizada por responsabilidad. Importa las funciones directamente desde su módulo; `__init__.py` no carga módulos ni
Qt automáticamente.

## Módulos

| Módulo               | Responsabilidad                                                           |
| -------------------- | ------------------------------------------------------------------------- |
| `graph.py`           | Recorrido de nodos, resolución de entradas, conexiones y caché de salidas |
| `node_operations.py` | Portapapeles, duplicación, clonación, transferencia de knobs y animación  |
| `selection.py`       | Grupo activo y selección de uno o varios nodos                            |
| `colors.py`          | Colores RGB empaquetados, HSV y hexadecimal                               |
| `paths.py`           | Rutas de usuario, proyecto, herramientas y plugins                        |
| `media_names.py`     | Nombres, extensiones y versiones de archivos                              |
| `sequences.py`       | Padding y búsqueda de archivos de secuencias                              |
| `collect_files.py`   | Recopilación de recursos externos del proyecto                            |
| `dag.py`             | Widgets del gráfico de nodos y posición del cursor                        |
| `pyside.py`          | Compatibilidad entre PySide2 y PySide6                                    |
| `panels.py`          | Paneles acoplados y flotantes                                             |
| `python_util.py`     | Archivos de texto, JSON, codificación Base64 y comandos                   |

## Convenciones de uso

- `get_input_connections` y `get_output_connections` devuelven pares de índice de entrada y nodo.
- `resolve_input_node` atraviesa Dot y, según sus opciones, nodos desactivados y Switch.
- `get_upstream_nodes` recorre las conexiones de entrada; `get_first_input_chain_root` sigue únicamente la entrada cero.
- `get_output_connection_map(force)` permite reutilizar la caché con `force=False` o reconstruirla con `force=True`.
- `get_selected_node` exige una única selección; `get_selected_nodes` devuelve la selección del grupo activo.
- Los nombres terminados en `_hsv` usan tono, saturación y valor; `set_tile_color_hex` recibe un color hexadecimal.
- `get_sequence_stem` conserva la versión y excluye el padding y la extensión.
- `has_frame_padding` detecta marcadores de secuencia; `list_sequence_files` busca sus archivos existentes.
- `encode_json_base64` y `decode_json_base64` convierten datos JSON a texto Base64 y viceversa.

## Verificación

Desde la raíz de `comfyui-code`, ejecuta `bash testing/unit.sh --on-error continue`. Los paneles, el portapapeles y la posición del cursor
requieren también revisión interactiva.
