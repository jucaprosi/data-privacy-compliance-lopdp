# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de CAPA-04 (Auditoría con grilla de verificación y acta por área).

Contrato: governance/especificaciones/CAPA-04.md §2.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("crear_auditoria", "POST", "/api/v1/auditoria-capa/auditorias", {"implementador", "coordinador"}),
    ("listar_auditorias", "GET", "/api/v1/auditoria-capa/auditorias", {"implementador", "coordinador", "auditor"}),
    ("obtener_auditoria", "GET", "/api/v1/auditoria-capa/auditorias/{id}", {"implementador", "coordinador", "auditor"}),
    ("actualizar_fila_auditoria", "PUT", "/api/v1/auditoria-capa/auditorias/{id}/filas/{control_ref}", {"auditor"}),
    ("levantar_acta_auditoria", "POST", "/api/v1/auditoria-capa/auditorias/{id}/areas/{area_id}/acta", {"auditor"}),
    ("obtener_acta_auditoria", "GET", "/api/v1/auditoria-capa/auditorias/{id}/areas/{area_id}/acta", {"auditor", "dpo", "admin_organizacion"}),
    ("verificar_cierre_hallazgo", "POST", "/api/v1/auditoria-capa/hallazgos/{hallazgo_id}/verificar-cierre", {"auditor"}),
    ("listar_cierres_pendientes", "GET", "/api/v1/auditoria-capa/cierres-pendientes", {"auditor"}),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
