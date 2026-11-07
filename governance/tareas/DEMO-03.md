+++
id = "DEMO-03"
titulo = "Plantilla «Cooperativa Demo»: cuatro personas ficticias y clonación aditiva en la sala organización"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["DEMO-00"]
propiedad = ["features/organizacion/services/clon_plantilla_engine.py", "features/organizacion/organizacion_service.py#DEMO-03", "data/demo/cooperativa_demo.json", "scripts/demo/sembrar_plantilla.py", "tests/test_demo_plantilla.py"]
arbitro = "pytest tests/test_demo_plantilla.py contra una rama Neon de prueba: siembra idempotente, clon con cuatro personas que cumple la segregación + suite de organización existente en verde"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-03 · Plantilla «Cooperativa Demo»: cuatro personas ficticias y clonación aditiva en la sala organización

**Por qué.** Cada entrada recibe su propia organización, copiada de una plantilla que parece una cooperativa real y permite mostrar el ciclo desde cualquier punto sin romper la segregación de funciones.

## Entrega
- **`organizacion_service.py#DEMO-03`:** **una sola** función pública nueva, `clonar_organizacion_plantilla(origen, marcar_demo=True)`, implementada en `services/clon_plantilla_engine.py`. Cambio aditivo: no se modifica ninguna firma existente (condición del CTO). Se niega a funcionar sin `DEMO_MODE=1` y solo acepta como origen un tenant `es_demo` marcado como plantilla. Copia el tenant con sus cuatro personas y sus roles, y marca el nuevo `es_demo = true`.
- **`data/demo/cooperativa_demo.json`:** «Cooperativa Demo» (RUC ficticio que no corresponde a ninguna entidad), estructura orgánica mínima, cuatro personas con un solo rol cada una (administrador, coordinador, implementador y DPO), diagnóstico **a medio llenar** (respondido por el DPO, sin sellar) y algunos documentos de Biblioteca en borrador.
- **Personas:** nombres terminados en «(ficticia)» o «(ficticio)», una descripción de una línea por rol (la valida el propietario) y correo con el dominio reservado `.invalid` (RFC 2606).
- **`scripts/demo/sembrar_plantilla.py`:** siembra idempotente; aborta si `apunta_a_produccion()` es verdadero. Se carga solo en la rama Neon `demo` (la siembra en la nube la hace una persona, DEMO-07).

## Pruebas (`tests/test_demo_plantilla.py`)
- Sembrar dos veces deja una sola plantilla.
- Clonar crea un tenant nuevo `es_demo` con cuatro personas de un rol cada una; el trigger del DPO lo acepta sin cambios.
- Sin `DEMO_MODE`, o con un origen que no es plantilla, `clonar_organizacion_plantilla` lanza error.
- Con la URL de producción la siembra aborta antes de escribir.
- Ningún correo fuera de `.invalid`; nombres y RUC en una lista de ficticios de la propia prueba.

## Límites
- No toca `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS, `api/rbac.py` ni `main.py`.
- Ninguna otra ficha de organización va en su tanda (condición del CTO). Sin migraciones: usa `tenants.es_demo` de DEMO-00.
- No toca `features/demo/`: la sala demo llamará a esta función solo por `organizacion_service`.
- Sin datos de clientes reales, nunca.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
