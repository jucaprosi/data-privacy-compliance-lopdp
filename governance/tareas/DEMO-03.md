+++
id = "DEMO-03"
titulo = "Siembra de la plantilla «Cooperativa Demo» con seis personas ficticias"
ola = "D"
estado = "pendiente"
sala = "operaciones"
depende_de = ["DEMO-00", "EP-03"]
propiedad = ["scripts/demo/sembrar_plantilla.py", "data/demo/cooperativa_demo.json", "tests/test_demo_siembra.py"]
arbitro = "pytest tests/test_demo_siembra.py contra una base de prueba: siembra idempotente, seis personas de un solo rol que cumplen la segregación del DPO"
rastros = ["¤demo"]
+++

# DEMO-03 · Siembra de la plantilla «Cooperativa Demo» con seis personas ficticias

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `operaciones`. Tanda 54.

**Por qué.** La demo copia una plantilla fija. Esta ficha la siembra una vez, con datos ficticios, reutilizando el sembrador de EP-03. No clona nada: eso lo hace cada sala (DEMO-03a…03f).

## Entrega
- `data/demo/cooperativa_demo.json`: tenant plantilla con `es_demo = true`, dos unidades y seis personas `.invalid` de un solo rol: administrador de la organización, DPO, coordinador, implementador, responsable de área (con su unidad) y auditor. Cada persona trae `unidad` y `rol_etiqueta`.
- Datos de ciclo: diagnóstico a medio revisar, hallazgos y tareas, documentos de Biblioteca y evidencias como registro.
- `scripts/demo/sembrar_plantilla.py`: se niega a correr fuera de `APP_ENV=demo`; idempotente.
- Las líneas de rol del selector son de DEMO-04, no de la plantilla.

## Pruebas
- Dos siembras seguidas dejan el mismo estado.
- Ninguna persona tiene dos roles; el DPO no tiene rol operativo.
- Todos los correos terminan en `.invalid`.
- Fuera de `APP_ENV=demo` el script sale con error.

## Límites
- Contrato congelado: rutas, cuerpos y códigos de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, para y consulta a Tech Lead.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS ni `main.py`.
- En archivos con secciones `#ID` escribe solo dentro de tus marcas `# --- INICIO <ID> --- … # --- FIN <ID> ---`.
- Nunca uses la base ni el proyecto de producción; solo datos ficticios con correos `.invalid`.

## Fuentes
- `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` §5.6 (demo comercial) y §5.6.8 (corte confirmado por el Arquitecto ADPA y el CTO, 2026-11-07).
- `governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, invariantes 60 a 63.
- Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Interfaz: `governance/apoyo/UX_DEMO_EVYDENTIA.md` (lo que cambia) sobre `governance/apoyo/UX_DEMO_COMERCIAL.md`.
