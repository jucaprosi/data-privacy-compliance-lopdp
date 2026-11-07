+++
id = "DEMO-05"
titulo = "Purga nocturna de las demos vencidas, fuera de la aplicación"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-00", "SEC-10", "SEC-15"]
propiedad = ["scripts/demo/purgar_demos.py", "tests/test_demo_purga.py"]
arbitro = "pytest tests/test_demo_purga.py contra una rama Neon de prueba; mutación documentada"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-05 · Purga nocturna de las demos vencidas, fuera de la aplicación

**Por qué.** La aplicación no puede borrar (SEC-10 e `INV_LOPDP_AUDIT_LOG_APPEND_ONLY`), así que el borrado va en dos tiempos: la app marca vencida y un proceso nocturno, con otra credencial, borra.

## Entrega
- **`scripts/demo/purgar_demos.py`:** borra todas las filas de las organizaciones demo vencidas, en todas las tablas con `tenant_id`, más sus filas de `users`, `user_tenant_roles` y `demo_sesiones`. Se niega a correr si `apunta_a_produccion()` es verdadero. Nunca toca la plantilla.
- **Parche del flujo nocturno en el informe:** `.github/workflows/purga-demo.yml` es gobernanza reservada; esta ficha entrega su contenido en el informe y lo aplica una persona (DEMO-07).

## Pruebas (`tests/test_demo_purga.py`)
- Tras purgar, ninguna tabla con `tenant_id` conserva filas del tenant purgado (la prueba recorre el catálogo, no una lista fija).
- La plantilla y las demos activas quedan intactas.
- Con la URL de producción aborta antes de borrar.
- Mutación documentada: quitar el filtro `es_demo` hace fallar «plantilla intacta».

## Límites
- No toca `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS, `api/rbac.py` ni `main.py`.
- No escribe en `.github/workflows/` ni en `features/`.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
