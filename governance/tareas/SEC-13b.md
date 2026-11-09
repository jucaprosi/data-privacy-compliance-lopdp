+++
id = "SEC-13b"
titulo = "Alta idempotente del tope de IA por organización: fijar_tope en la compuerta de límites"
ola = "D"
estado = "en_curso"
sala = "pasillo_central"
depende_de = ["SEC-13a"]
propiedad = ["app_core/limites/tope_organizacion.py", "tests/test_sec13b_fijar_tope.py"]
crea = ["tests/test_sec13b_fijar_tope.py"]
arbitro = "pytest tests/test_sec13b_fijar_tope.py tests/test_sec13a_tope_ia_organizacion.py contra una base de prueba; mutación documentada"
rastros = ["¤seguridad-tenant"]
+++

# SEC-13b · fijar_tope

Diseño del Arquitecto ADPA (2026-11-09), pedido por DEMO-03. La compuerta `app_core/limites/tope_organizacion.py` (SEC-13a, hecha) solo tiene `consumir_generacion`. DEMO-03 necesita fijar el tope de la plantilla sin escribir directo en la tabla.

## Entrega
- `fijar_tope(session, tenant_id, tope)`: `INSERT … ON CONFLICT (tenant_id) DO UPDATE SET tope`, con RLS. `lopdp_app` ya tiene INSERT y UPDATE (migración 20261120). Sin migración nueva.

## Pruebas
- Dos llamadas dejan una sola fila.
- El tope se actualiza.
- Desde otro tenant la fila no se ve.
- Mutación: un INSERT sin ON CONFLICT deja en rojo la prueba de las dos llamadas.
