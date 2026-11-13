+++
id = "SEC-24"
titulo = "Quitar el valor por defecto de la cabecera de tenant en la dependencia común"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-03", "SEC-15"]
propiedad = ["api/dependencies.py", "tests/test_sec24_sin_tenant_por_defecto.py"]
crea = ["tests/test_sec24_sin_tenant_por_defecto.py"]
arbitro = "pytest tests/test_sec24_sin_tenant_por_defecto.py + suite completa; mutación documentada"
rastros = ["¤seguridad-tenant"]
+++

# SEC-24 · Quitar el valor por defecto de la cabecera de tenant en la dependencia común

Mejora menor del CTO (2026-11-13), de prioridad baja. `obtener_tenant_id_actual` (`api/dependencies.py:17`) declara `default="tenant-default"`. Ese valor solo aplica en modo `headers`, que SEC-15 prohíbe fuera de local; en oidc no cambia nada. Se quita para que no confunda a quien lea la función.

**Prueba:** la firma no tiene valor por defecto y, en modo `headers` sin cabecera, responde 400. **Mutación:** volver a poner el valor por defecto → falla.
