+++
id = "DEMO-03"
titulo = "Siembra de la plantilla «Cooperativa Demo» con cinco personas ficticias (el auditor lo añade ORG-22)"
ola = "D"
estado = "en_curso"
sala = "operaciones"
depende_de = ["DEMO-00", "EP-03", "SEC-13a", "SEC-13b"]
propiedad = ["scripts/demo/sembrar_plantilla.py", "data/demo/cooperativa_demo.json", "tests/test_demo_siembra.py", "features/demo/domain/plantilla.py", "app_core/pasillo/demo.py"]
arbitro = "pytest tests/test_demo_siembra.py contra una base de prueba: siembra idempotente, cinco personas de un solo rol que cumplen la segregación del DPO (la sexta, auditor, la siembra ORG-22)"
rastros = ["¤demo"]
+++

# DEMO-03 · Siembra de la plantilla «Cooperativa Demo» con cinco personas ficticias (el auditor lo añade ORG-22)

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `operaciones`. Tanda 54.

**Por qué.** La demo copia una plantilla fija. Esta ficha la siembra una vez, con datos ficticios, reutilizando el sembrador de EP-03. No clona nada: eso lo hace cada sala (DEMO-03a…03f).

## Entrega
- `data/demo/cooperativa_demo.json`: tenant plantilla con `es_demo = true`, dos unidades y cinco personas `.invalid` de un solo rol: administrador de la organización, DPO, coordinador, implementador y responsable de área (con su unidad). El auditor no figura en el JSON, ni siquiera con otro rol: lo añade ORG-22 (CTO, 2026-11-09). Cada persona trae `unidad` y `rol_etiqueta`.
- Datos de ciclo: diagnóstico a medio revisar, hallazgos y tareas, documentos de Biblioteca y evidencias como registro.
- `scripts/demo/sembrar_plantilla.py`: se niega a correr fuera de `APP_ENV=demo`; idempotente.
- Fija en la plantilla el tope de IA de la organización en 5 (`ia_tope_organizacion.tope = 5`, decisión del propietario, PRD §5.6.7). La tabla y el conteo son de SEC-13a; DEMO-03a copia la fila al tenant clonado.
- Las líneas de rol del selector son de DEMO-04, no de la plantilla.

## Pruebas
- Dos siembras seguidas dejan el mismo estado.
- Ninguna persona tiene dos roles; el DPO no tiene rol operativo.
- Todos los correos terminan en `.invalid`.
- La plantilla tiene `ia_tope_organizacion.tope = 5`.
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

## Ajustes del Arquitecto ADPA (2026-11-09)
1. **Datos de ciclo:** el JSON los declara por sala. El script llama a `sembrar_en_plantilla(session, plantilla_id, datos)` de cada sala, por su pasillo y en el orden de `ORDEN_DE_SALAS`. Esa función es de DEMO-03a a 03f. Si una sala aún no la tiene, el script la nombra como faltante y sigue. DEMO-03 no escribe en tablas de otras salas.
   - Prueba: cada bloque del JSON corresponde a una sala de `ORDEN_DE_SALAS`; un bloque sin sala hace fallar la prueba.
2. **Id de la plantilla:** `PLANTILLA_TENANT_ID = "demo-plantilla-cooperativa"` en `features/demo/domain/plantilla.py`. DEMO-03 asume ese archivo entero, porque DEMO-00 está hecha. DEMO-05 y DEMO-03a a 03f lo leen de ahí.
   - Prueba: el literal solo aparece en `plantilla.py` y en `data/demo/cooperativa_demo.json`.
   - Mutación: repetirlo en el script hace fallar la prueba.
3. **Tope de IA:** se fija con `fijar_tope` de SEC-13b, sin escribir directo en la tabla.
4. **Auditor:** el rol no existe en `roles.py` ni en `ck_utr_role`. DEMO-03 siembra cinco personas y el auditor no figura en el JSON (CTO, 2026-11-09). Lo añade ORG-22.
5. **`ORDEN_DE_SALAS`** (decisión de producto del CTO, 2026-11-09, opción 1) queda en `plantilla.py` como `(organizacion, diagnostico, roadmap, biblioteca, evidencias, videovigilancia)`, sin `rat`. La base es H1 y la tabla de FLUJOS; el §5.6.1.4 del PRD tampoco pide RAT. Si algún día se quiere RAT en la demo, hace falta otra decisión de producto y un cambio en el PRD.

## Pasillo de la demo (Arquitecto ADPA, 2026-11-09)
- DEMO-03 asume `app_core/pasillo/demo.py` entero (su dueña, DEMO-00, está hecha; sin secciones).
- `scripts/demo/sembrar_plantilla.py` importa `PLANTILLA_TENANT_ID` y `ORDEN_DE_SALAS` solo de `app_core.pasillo.demo`; nunca de `features.demo.domain`.
- El pasillo solo reexporta: no lleva lógica. `features/demo/demo_service.py` no se toca.
- Prueba: `sembrar_plantilla.py` no importa `features.demo.domain`. Mutación: reponer ese import pone en rojo la guardia ADPA de imports cruzados.
