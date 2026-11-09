+++
id = "DEMO-02"
titulo = "Ciclo de sesión demo: entrar, tope, reemplazo, terminar, vencimiento y orquestador de la copia"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-00", "DEMO-08", "DEMO-03", "DEMO-03a", "DEMO-03b", "DEMO-03c", "DEMO-03d", "GCP-01"]
propiedad = ["features/demo/domain/vendedores.py", "features/demo/services/entrada_engine.py", "features/demo/services/cierre_engine.py", "api/routers/demo_sesion.py", "tests/test_demo_ciclo.py"]
arbitro = "pytest tests/test_demo_ciclo.py contra una base de prueba + linter ADPA sin cruces; mutación documentada"
rastros = ["¤demo"]
+++

# DEMO-02 · Ciclo de sesión demo: entrar, tope, reemplazo, terminar, vencimiento y orquestador de la copia

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `demo`. Tanda 55.

**Por qué.** Es el ciclo de vida de cada demo, y el único sitio que llama a las secciones `clonar_desde_plantilla` de las salas, por sus pasillos.

## Entrega
- `domain/vendedores.py`: lee y normaliza `DEMO_VENDEDORES` de Secret Manager.
- `entrada_engine.py`: lista autorizada (403), vencer inactivas y la demo previa del vendedor (motivo `reemplazo`), tope de 20 con bloqueo (409), orquestador de la copia por pasillos en una sola transacción, alta de la sesión como administrador y evento `DEMO_INICIADA`. Si la copia falla: 503 `DEMO_NO_DISPONIBLE` sin sesión ni organización a medias.
- `cierre_engine.py`: terminar (vencimiento lógico, motivo `terminar`) y estado.
- `api/routers/demo_sesion.py`: `POST /api/v1/demo/entrar`, `POST /api/v1/demo/terminar`, `GET /api/v1/demo/estado` con `personas[]` por la compuerta, con la forma de `domain/contrato.py`.

## Pruebas
- Correo fuera de la lista: 403 y nada creado.
- 21.ª entrada simultánea: 409.
- Segunda entrada del mismo vendedor: la primera vence con motivo `reemplazo` y no ocupa cupo.
- Falla simulada en una sala: 503 y ninguna fila nueva.
- Terminar marca vencida y la aplicación no borra nada.

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

## Salas sin clon registrado (CTO, 2026-11-09)
- El orquestador recorre `ORDEN_DE_SALAS`. Omite las salas que aún no tienen `clonar_desde_plantilla` registrado (hoy `evidencias` y `videovigilancia`, de DEMO-03e y 03f) y deja una línea en el evento de auditoría por cada sala omitida.
- Prueba: con una sala sin clon, la sesión se activa y el evento nombra la sala.
- Prueba: si falla el clon de una sala registrada, la sesión demo no se activa.
- Por eso DEMO-02 ya no depende de DEMO-03e.
