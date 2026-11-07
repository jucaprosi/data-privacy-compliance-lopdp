+++
id = "DEMO-06"
titulo = "Prueba de que con APP_ENV=demo no sale ningún correo"
ola = "D"
estado = "pendiente"
sala = "pruebas"
depende_de = ["EP-08"]
propiedad = ["tests/test_demo_sin_correos.py"]
arbitro = "pytest tests/test_demo_sin_correos.py en verde"
rastros = ["¤demo"]
+++

# DEMO-06 · Prueba de que con APP_ENV=demo no sale ningún correo

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `pruebas`. Tanda 54.

**Por qué.** Invariante 62. La lógica de correos solo a permitidos es de EP-08; esta ficha solo lo prueba para la demo.

## Entrega
- Prueba que, con `APP_ENV=demo` y la lista de permitidos vacía, ninguna acción que notifica envía nada.

## Pruebas
- Ningún envío al adaptador con destinos `.invalid` ni reales.

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
