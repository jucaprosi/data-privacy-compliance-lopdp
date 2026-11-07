+++
id = "DEMO-03"
titulo = "Plantilla de datos «Cooperativa Demo» con cuatro personas ficticias"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-01"]
propiedad = ["data/demo/cooperativa_demo.json", "scripts/demo/sembrar_plantilla_demo.py", "tests/demo/test_plantilla_demo.py"]
arbitro = "pytest tests/demo/test_plantilla_demo.py contra una rama Neon de prueba: la plantilla se siembra dos veces sin duplicar y cumple la segregación"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-03 · Plantilla de datos «Cooperativa Demo» con cuatro personas ficticias

**Por qué.** Cada organización demo se copia de una plantilla. La plantilla tiene que parecer una cooperativa real, permitir mostrar el ciclo desde cualquier punto y cumplir la segregación de funciones.

## Entrega
- **`data/demo/cooperativa_demo.json`:** la organización «Cooperativa Demo» (datos ficticios, RUC ficticio que no corresponda a una entidad real), estructura orgánica mínima, cuatro personas con un solo rol cada una (administrador, coordinador, implementador y DPO), diagnóstico **a medio llenar** (respondido por el DPO pero sin sellar), algunos documentos de Biblioteca en borrador.
- **Personas:** nombre ficticio terminado en «(ficticia)» o «(ficticio)», una descripción de una línea por rol (la valida el propietario como experto LOPDP) y correo con el dominio reservado `.invalid` (RFC 2606). Los nombres se informan a UX/UI para validar los textos de DEMO-04.
- **`scripts/demo/sembrar_plantilla_demo.py`:** siembra la plantilla en la base indicada, idempotente, con `tenants.es_demo = true` y marcada como plantilla (no vence y no se purga). Aborta si `apunta_a_produccion()` es verdadero.

## Pruebas (`tests/demo/test_plantilla_demo.py`)
- Sembrar dos veces deja una sola plantilla.
- Cuatro personas, un rol cada una, ningún correo fuera de `.invalid`; el trigger del DPO acepta la siembra sin cambios.
- Con la URL de producción el script aborta antes de escribir.
- Ningún dato personal real: los nombres y el RUC están en una lista de ficticios de la propia prueba.

## Límites
- Sin migraciones: usa `tenants.es_demo` y las tablas que crea DEMO-01, por eso va en la tanda siguiente.
- No crea la copia por sesión (DEMO-02) ni toca código de salas.
- Sin datos de clientes reales, nunca.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y proyección ADPA del Arquitecto de soluciones: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; vencimiento a los 60 minutos sin actividad; tope de 20 demos activas; lista `DEMO_VENDEDORES` en Vercel; dirección `*.vercel.app`; una sola demo activa por vendedor (la nueva entrada vence la anterior, motivo `reemplazo`).
