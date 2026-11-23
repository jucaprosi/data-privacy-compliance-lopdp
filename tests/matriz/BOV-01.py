# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de BOV-01 (suscripción de la bóveda cloud).

Formato documentado en tests/matriz/__init__.py. La consulta es de los roles de gestión del tenant; el alta
de la suscripción es del operador de la plataforma y se prueba con su propia guarda (ORG-09).
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "consultar_suscripcion_boveda",
        "GET",
        "/api/v1/boveda-cloud/suscripcion",
        {"admin_organizacion", "dpo", "coordinador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {
    ("POST", "/api/v1/boveda-cloud/suscripcion"): (
        "Alta de suscripción reservada al operador de la plataforma (ORG-09); "
        "no la ejerce ningún rol de organización."
    ),
}
