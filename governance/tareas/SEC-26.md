+++
id = "SEC-26"
titulo = "Matriz del operador de la plataforma: ninguna ruta de organización le responde con datos"
ola = "D"
estado = "pendiente"
tanda = 129
sala = "organizacion"
depende_de = []
propiedad = ["tests/matriz/roles/operador_plataforma.py", "tests/test_matriz_permisos.py"]
crea = ["tests/matriz/roles/operador_plataforma.py"]
arbitro = "pytest tests/test_matriz_permisos.py contra PostgreSQL 16; mutaciones m1 a m3."
rastros = ["¤rbac-tenant", "¤arbitro"]
+++

# SEC-26 · Matriz del operador de la plataforma: ninguna ruta de organización le responde con datos

**Contrato:** `governance/especificaciones/SEC-26.md` (manda sobre esta ficha).

**Origen.** Análisis de brechas de la tanda 129 (brief del CTO del 2026-11-28): criterio 3 del PRD e invariante 9 (`INV_LOPDP_OPERATOR_NO_TENANT_DATA`). Prioridad 3: riesgo legal.

## Entrega
- `tests/matriz/roles/operador_plataforma.py`, con cada `id_accion` decidida para `operador_plataforma` (R1).
- En `tests/test_matriz_permisos.py`, la identidad del operador para recorrer la matriz (R2).

## Límites
- En `tests/test_matriz_permisos.py` (sus otras fichas están hechas), solo la carga de roles (l. 458-480), el recorrido por roles (l. 573) y la sección `SEC-26`.
- Sin cambios de código de producción. Si una ruta responde con datos, el PR lo para y el Arquitecto abre la ficha que la arregla.
