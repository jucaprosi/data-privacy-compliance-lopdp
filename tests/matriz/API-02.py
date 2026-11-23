# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de API-02 (claves de integración y techos de paquete).

Contrato: governance/tareas/API-02.md.
Escriben `admin_organizacion` y `coordinador`. El DPO solo consulta.
El rol `auditor` no tiene permisos sobre la API de integración (espera 403).
"""

_ESCRIBEN = {"admin_organizacion", "coordinador"}
_LECTORES = _ESCRIBEN | {"dpo"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("crear_clave_integracion", "POST", "/api/v1/integraciones/claves", _ESCRIBEN),
    ("listar_claves_integracion", "GET", "/api/v1/integraciones/claves", _LECTORES),
    ("rotar_clave_integracion", "POST", "/api/v1/integraciones/claves/{id}/rotar", _ESCRIBEN),
    ("revocar_clave_integracion", "POST", "/api/v1/integraciones/claves/{id}/revocar", _ESCRIBEN),
    ("consultar_techos_integracion", "GET", "/api/v1/integraciones/techos", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
