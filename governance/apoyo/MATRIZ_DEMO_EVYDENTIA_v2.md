# EVYDENTIA · Demo comercial: matriz flujo × archivo v2 (respuesta a Tech Lead)

Arquitecto ADPA · 2026-11-07. Base: PRD §5.6 (PR #435, commit 00ce687, con H1–H3 aceptados), `UX_DEMO_EVYDENTIA.md` y `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, al que esta versión sustituye en §2–§4. No hay choque con el §5.6.

## Respuestas a los tres puntos

### 1. `AvisoEntorno`: dueña única EP-02, que va antes que DEMO-04

- **EP-02 es la dueña de `AvisoEntorno`, de sus variantes «pruebas» y «demo» (texto y colores del UX §1), de su montaje en `app/layout.tsx` y de la llamada a `GET /api/v1/entorno`.** Ya lo fija el §5.5 (H3). No vale «quien llegue primero».
- Para que DEMO-04 no edite nada de EP-02, EP-02 deja en el aviso **dos ranuras vacías**:
  - `acciones`: el selector y «Terminar demo»;
  - `organizacion`: el nombre de la organización y, después, el cambio de organización.
- Las ranuras se llenan desde un **registro con secciones** (ley 4 del §5.1): `frontend/src/lib/entorno/ranuras.ts`, creado por EP-02 con la sección `# INICIO DEMO-04 … # FIN DEMO-04` vacía. DEMO-04 solo escribe su sección y sus componentes en `frontend/src/components/demo/*`. Ni `layout.tsx` ni `AvisoEntorno.tsx` tienen dos dueñas.
- Orden: EP-02 fusionada antes de que DEMO-04 entre (condición de entrada de la tanda 1, ya prevista). Si EP-02 se retrasa, DEMO-04 espera; no lo construye.
- Pido a Tech Lead que añada a la ficha EP-02 el archivo de ranuras y las dos ranuras vacías: es su alcance (§5.5, fila EP-02) y no cambia el PRD.

### 2. Seis personas con `unidad` y `rol_etiqueta`: sí cambia el contrato DEMO-00

DEMO-00 todavía no está escrita, así que solo cambia su contenido, no su orden ni su sala:
- `features/demo/domain/personas.py` (DEMO-00): `PersonaDemo(usuario_id, nombre, rol, rol_etiqueta, unidad: str | None)`; el orden fijo de los seis roles del UX §2 (admin_organizacion, dpo, coordinador, implementador, responsable_area, auditor); la etiqueta de cada rol; `ROL_INICIAL = admin_organizacion`.
- La forma de `GET /api/v1/demo/estado` y de la respuesta de `entrar` se congela en DEMO-00 (`domain/contrato.py`), con `personas[]` de seis elementos y `unidad` solo en el Responsable de área.
- **Quién llena los datos:**
  - **DEMO-03** (siembra, sala `operaciones`): crea las seis personas `.invalid` y asigna el Responsable de área a una de las dos unidades.
  - **DEMO-03a** (sala `organizacion`): las copia con sus roles y su unidad, y devuelve el mapa de ids.
  - **DEMO-01** (sala `demo`): `persona_engine.listar_personas()` arma `personas[]` leyendo usuarios, roles y unidades por `app_core/pasillo/organizacion.py`, con funciones que ya existen (`listar_usuarios`, `listar_roles_de_usuario`, `listar_areas`), y aplica el orden y las etiquetas de DEMO-00.
  - **DEMO-02** (`cierre_engine.estado`) llama a `demo_service.listar_personas` (compuerta, solo lectura) para componer el estado.

### 3. Dueñas del 503 y de `GET /api/v1/entorno`

| Pieza | Dueña | Quién la usa |
|---|---|---|
| Código `DEMO_NO_DISPONIBLE` (503) en `features/demo/domain/errores.py` | DEMO-00 | — |
| Lanzar el 503 cuando falla la copia de la plantilla (servidor) | DEMO-02 (`entrada_engine`, orquestador) | — |
| Mostrar el 503, el corte a los 60 s y el aviso tras tres fallos (cliente, UX §4) | DEMO-04 | — |
| `GET /api/v1/entorno` y `X-Entorno` | **EP-01** (sala `pasillo_central`), no es de la demo | EP-02 (lo llama el aviso), DEMO-04 y DEMO-05 (solo lectura) |
| `GET /api/v1/demo/estado` | DEMO-02 (`api/routers/demo_sesion.py`) | DEMO-04 |

## Matriz flujo × archivo v2

E = dueña · S = solo su propia sección `#ID` · L = lectura · vacío = no lo toca

| Archivo | EP-01 | EP-02 | 00 | 08 | 01 | 02 | 03 | 03a–f | 04 | 05 | 06 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `GET /api/v1/entorno`, `X-Entorno`, guardias | E | L | | L | | | | | L | L | |
| `frontend/.../AvisoEntorno.tsx`, `app/layout.tsx` (montaje del aviso) | | E | | | | | | | L | | |
| `frontend/src/lib/entorno/ranuras.ts` | | E | | | | | | | S | | |
| `features/demo/demo_service.py`, `domain/*` (sesión, errores con 503, eventos, personas, contrato), `repo/sesiones_repo.py`, `app_core/pasillo/demo.py`, migración | | | E | | L | L | | | | L (migración) | |
| `app_core/security.py` (gancho) | | | | S | L | L | | | | | |
| `features/demo/services/resolutor_engine.py`, `persona_engine.py`, `api/routers/demo_persona.py` | | | | | E | | | | | | |
| `features/demo/domain/vendedores.py`, `services/entrada_engine.py`, `cierre_engine.py`, `api/routers/demo_sesion.py` | | | | | | E | | | | | |
| `app_core/pasillo/organizacion.py` | | | | | L | L | | S (03a) | | | |
| pasillos y compuertas de diagnostico, roadmap, biblioteca, evidencias, videovigilancia | | | | | | L | | S (una por sala) | | | |
| `features/<sala>/services/clon_plantilla_engine.py` | | | | | | | | E | | | |
| `scripts/demo/sembrar_plantilla.py` | | | | | | | E | | | | |
| `frontend/src/components/demo/*`, `frontend/src/lib/demo/*` | | | | | | | | | E | | |
| `jobs/purga_demo/*` | | | | | | | | | | E | |
| `tests/test_demo_<ficha>.py`, `frontend/tests/demo/*` | | | E | E | E | E | E | E | E | E | E |

DEMO-07 (personas) es dueña de `governance/operaciones/entornos/demo/*` y `DEMO_COMERCIAL.md`. `main.py` no se toca.

Nota para DEMO-03d: `app_core/pasillo/biblioteca.py` no existe. Si ADPA-06 ya lo tiene asignado, DEMO-03d espera a ADPA-06 y escribe solo su sección. Si no tiene dueña, DEMO-03d lo crea con la cabecera del pasillo y su sección, y queda como dueña del archivo. Lo decide Tech Lead.

## Tandas v2

| Tanda | Fichas | Condición de entrada |
|---|---|---|
| Previa (ya planificada en el §5.5) | EP-01, EP-02 (con las ranuras), EP-08 | — |
| 0 | DEMO-00 | EP-01 fusionada |
| 1, en paralelo | DEMO-08, DEMO-03, DEMO-03a, 03b, 03c, 03d*, 03e, DEMO-04, DEMO-05, DEMO-06 | DEMO-00 fusionada; DEMO-04 con EP-02 fusionada; DEMO-06 con EP-08 fusionada; *03d según la nota de `pasillo/biblioteca.py` |
| 2, en paralelo | DEMO-01, DEMO-02 | DEMO-08 y DEMO-03a–e fusionadas; sin dobles |
| Después | DEMO-03f | sala `videovigilancia` creada |
| Fuera de tanda | DEMO-07 (personas) | GCP-01, GCP-03, GCP-04 y DEMO-05 |

Seguridad revisa DEMO-00, DEMO-08 y DEMO-01 antes del reparto.
