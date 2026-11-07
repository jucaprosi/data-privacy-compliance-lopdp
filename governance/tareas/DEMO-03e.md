+++
id = "DEMO-03e"
titulo = "Clonar desde plantilla en la sala evidencias"
ola = "D"
estado = "pendiente"
sala = "evidencias"
depende_de = ["DEMO-00", "ADPA-06", "EVI-01"]
propiedad = ["features/evidencias/services/clon_plantilla_engine.py", "features/evidencias/evidencias_service.py#DEMO-03e", "app_core/pasillo/evidencias.py#DEMO-03e", "tests/test_demo_clon_evidencias.py"]
arbitro = "pytest tests/test_demo_clon_evidencias.py contra una base de prueba + suite existente de evidencias en verde + linter ADPA sin cruces"
rastros = ["¤demo", "¤adpa"]
+++

# DEMO-03e · Clonar desde plantilla en la sala evidencias

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `evidencias`. Tanda 54.

**Por qué.** Ley 3 del §5.1: cada sala clona solo lo suyo. El orquestador de DEMO-02 llama a esta sección por el pasillo de `evidencias`.

## Entrega
- `clonar_desde_plantilla(session, origen, destino, mapa_ids)` en la sección `DEMO-03e` de `evidencias_service.py` y de `app_core/pasillo/evidencias.py`, con la firma que fija DEMO-00.
- Copia solo las filas de esta sala del tenant plantilla al tenant destino, traduciendo ids con `mapa_ids`; devuelve el mapa ampliado.
- Idempotente dentro de la transacción del orquestador; no hace commit.
- Copia también los objetos de los buckets de servidor a servidor, con prefijo por `tenant_id` del destino; si falla, los objetos copiados los borra la purga (DEMO-05).

## Pruebas
- Tras clonar, el destino tiene las mismas filas de la sala que la plantilla, con otro `tenant_id`.
- La plantilla queda intacta y ninguna fila apunta a ids de la plantilla.
- Con RLS forzada, el rol `lopdp_app` del destino no ve filas de la plantilla.

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
