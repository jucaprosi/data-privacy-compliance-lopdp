# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos, un archivo por tarea (`tests/matriz/<ID>.py`).

`tests/test_matriz_permisos.py` descubre aquí cada `*.py` (salvo este) y suma sus filas a la matriz:
no hay índice que editar. Cada tarea posee solo su archivo de filas; nadie más edita la matriz.

Formato de un archivo de filas (ejemplo vivo: `tests/matriz/RM-21.py`):

- `FILAS: list[tuple[str, str, str, set[str]]]` — obligatoria. Cada fila es
  `(id_accion, metodo_http, ruta_plantilla, roles_permitidos)`, por ejemplo
  `("listar_hallazgos", "GET", "/api/v1/roadmaps/hallazgos", {"dpo", "implementador"})`.
  `id_accion` es único en toda la matriz; la ruta es la plantilla registrada en FastAPI, con `/api/v1`;
  los roles son valores de `Role`.
- `FUERA_DE_MATRIZ: dict[tuple[str, str], str]` — opcional. Rutas bajo los prefijos de la matriz que no
  se controlan por rol, con la justificación como valor: `{("GET", "/api/v1/roadmaps/x"): "motivo"}`.

El nombre del archivo es el id de la tarea (`RM-21.py`): no se importa como módulo, se carga por ruta.
"""
