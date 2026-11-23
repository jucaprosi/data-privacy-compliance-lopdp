# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤roadmap ¤arbitro
"""Filas de la matriz de permisos de RM-25b (validación final de la evidencia). Formato en tests/matriz/__init__.py.

RM-25b no añade rutas: cambia los roles de `PATCH /api/v1/roadmaps/tasks/{task_id}/evidence/{evidence_id}`, cuya
fila (`validar_rechazar_evidencia`) vive en `tests/test_matriz_permisos.py` y pasa a `{coordinador, dpo, auditor}`.

La matriz da paso al `coordinador` por el rechazo, que sigue pudiendo hacerse en cualquiera de los dos pasos. El
motor (`features/roadmap/services/evidencia_engine.py`) le impide aprobar: responde 403 `ROL_SIN_VALIDACION_FINAL`,
porque la validación final es del `dpo` o del `auditor`. La matriz comprueba la dependencia de roles de la ruta,
no el cuerpo de la petición; lo que hace el motor lo prueba `tests/test_rm25b_validacion_final.py`.
"""

FILAS: list[tuple[str, str, str, set[str]]] = []
