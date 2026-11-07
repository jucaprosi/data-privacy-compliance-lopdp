+++
id = "DEMO-04"
titulo = "Interfaz demo: «Ver como» con seis personas, «Terminar demo» y pantallas de error"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["EP-02", "FE-10", "FE-19", "BIB-115"]
propiedad = ["frontend/src/lib/demo/", "frontend/src/components/demo/", "frontend/src/lib/auth/cabeceras.ts#DEMO-04", "frontend/src/lib/auth/fetchAutenticado.ts#DEMO-04", "frontend/src/lib/entorno/ranuras.ts#DEMO-04", "frontend/src/app/login/page.tsx#DEMO-04", "frontend/tests/demo/"]
arbitro = "cd frontend; npx playwright test tests/demo; npx tsc --noEmit; npm run lint; los 7 criterios de UX_DEMO_EVYDENTIA.md"
rastros = ["¤demo", "¤interfaz"]
+++

# DEMO-04 · Interfaz demo: «Ver como» con seis personas, «Terminar demo» y pantallas de error

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `frontend`. Tanda 54.

**Por qué.** El vendedor necesita cambiar de persona y cerrar la demo desde cualquier pantalla. La franja es el aviso de EP-02 con su variante `demo`: esta ficha no lo edita; llena las ranuras `acciones` y `organizacion` de EP-02 desde su sección de `frontend/src/lib/entorno/ranuras.ts`.

## Entrega
- Selector «Ver como» con las seis personas en el orden fijo de UX_DEMO_EVYDENTIA.md, su `rol_etiqueta` y esta línea por rol (validadas por el propietario el 2026-11-07, texto literal):
-   - Administrador de la organización: «Configura la organización y sus unidades, designa al DPO y al coordinador y asigna los dominios.»
-   - DPO: «Supervisa con independencia: reúne el soporte del diagnóstico, lo sella y valida la evidencia.»
-   - Coordinador: «Reparte las tareas a las áreas y hace la primera validación de la evidencia.»
-   - Implementador: «Acompaña el RAT, la Biblioteca y el plan de acción.»
-   - Responsable de área · Unidad: «Responde los dominios de su unidad, ejecuta sus tareas y carga la evidencia.»
-   - Auditor: «Audita por dominio, levanta actas por área y verifica las acciones correctivas.»
- Recorrido sugerido «Responsable de área → Coordinador → DPO → Auditor»: al pulsarlo, cambia a Responsable de área.
- «Terminar demo» con el aviso «La demo se cerró y sus datos se eliminan esta noche».
- Pantallas de error 401, 403, 409 y 503 `DEMO_NO_DISPONIBLE` (con reintentar; también si la espera pasa de 60 s) y la pantalla de carga de cinco pasos.
- Ranura `organizacion` registrada y sin pintar; selector y «Terminar demo» en la ranura `acciones`.
- `X-Role` = rol de la persona activa. Solo se monta si `GET /api/v1/entorno` dice `demo`.
- Trabaja contra el contrato congelado con la API simulada.

## Pruebas
- Los 7 criterios de Playwright de UX_DEMO_EVYDENTIA.md.
- Fuera de `demo` no aparece ni el selector ni el botón.
- Dos pestañas: al entrar en la segunda, la primera ve `DEMO_VENCIDA`.

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
