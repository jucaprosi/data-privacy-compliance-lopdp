# Briefs por bloque de trabajo — Hoja de Ruta Inteligente
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento:** 14 tasks abiertas (de 41; las otras 27 ya están hechas) = 13 en 13 bloques + 1 sin agente · 5 tandas · 13 cruces de archivos entre tasks (más las secciones reservadas).

## Preámbulo común (aplica a todos los bloques)

- Lee primero `governance/tareas/<ID>.md` de cada task de tu bloque (es la fuente de verdad), el PRD Módulo 5 (`governance/artefactos/PRD.md`, §7.1 catálogo de salas) y `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`.
- **Escribe solo en tu sala** y solo los archivos de la lista «Escribe» de tu bloque. Fuera de esa lista, no edites nada.
- **Cruza salas solo por compuertas** (`<sala>_service.py`): sin imports directos entre salas. Si tu sala no tiene compuerta, créala.
- **No edites** el índice generado de `governance/artefactos/TASKS.md` (lo produce `scripts/generar_indice_tareas.py --escribir`), `FUENTES_Y_BIBLIOGRAFIA.md` ni `APORTES_INEDITOS.md`. Los aportes los registra el coordinador.
- **Archivos de gobernanza reservada** (`.github/workflows/`, `verificadores/`, `ejecutar_arnes_*.bat`, `AGENTS.md`, `.claude/`, hooks, `scripts/entorno.bat`, `governance/artefactos/data/`): no los edites. Si tu task lo exigiera, prepara el parche y su prueba y entrégalos en el informe; el propietario los aplica. Con este reparto ninguna task de agente los toca (comprobado contra la `propiedad` de cada task); solo GOB-01, que va en «Sin agente».
- **Propiedad, no git:** el aislamiento es que cada archivo tenga un solo dueño (la `propiedad` de su task). Un archivo que no es tuyo no lo modificas, ni lo reviertes ni lo «limpias»: si el árbol aparece sucio con archivos ajenos es lo esperado, ignóralos; si algo ajeno te impide avanzar, PARA y repórtalo. No hace falta prohibir comandos de git: basta con no tener nada que revertir fuera de lo propio. Un árbol de trabajo propio (`git worktree`) es una comodidad, no la frontera.
- **Pruebas mínimas pero decisivas:** una prueba que falle si el comportamiento falta; no añadas pruebas ni tasks para alcanzar un número. Cada prueba nueva debe matar una mutación que ninguna otra mata: la que pasa aunque la función devuelva siempre verdadero no cuenta. Lo que entregues debe estar **conectado** a un árbitro que se ejecute (un verificador que nadie invoca no cuenta como entregado). Las exenciones de un verificador son datos declarados con su motivo, nunca exclusiones por directorio dentro del código.
- **El estado documentado no supera al verificado:** lo que no comprobaste con la salida de un árbitro lo marcas «no verificado»; no escribas «verificado» ni «integrado» sin ella. No copies a un documento lo que ya dice la task: referencia su ID.
- **El avance se mide por el diff, no por el mensaje del commit.** El mensaje declara solo lo que el diff contiene. Antes de integrar una rama, el coordinador ejecuta `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5: todo archivo del diff cabe en «Escribe»); si sobra uno, la rama no se integra.
- **El éxito lo decide un árbitro exógeno**, no tu opinión: el comando de «Hecho si» con código de salida 0. En Windows con Git Bash lanza el arnés con `cmd //c ".\ejecutar_arnes_tres_pilares.bat"` (o ruta absoluta) y acéptalo **solo** si la salida contiene `[ARNES] Los tres pilares pasaron exitosamente.` (`cmd /c` con una sola barra devuelve 0 sin ejecutar nada; ver Aporte 106). El intérprete lo resuelve `scripts\entorno.bat`; ver `governance/operaciones/ENTORNO_LOCAL.md`.
- **Rama y commit:** una rama por task (`feat/<id-de-la-task>`), desde `main` actualizado y en el orden del bloque; un PR por task (regla 8 de `governance/tareas/README.md`, que manda sobre este documento). Añade siempre los archivos por su ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`. Antes de cada commit comprueba la rama con `git branch --show-current`. No empujes ni abras PR sin que el coordinador lo pida.
- **Rastros `¤`:** búscalos con `git grep --untracked -F "<rastro>"` antes de buscar en lenguaje natural. No inventes rastros; si el de tu bloque no existe, tu primera task crea `¦tag` y lo indexa.
- **Los tokens `¤` no van en la interfaz de usuario** (solo en metadatos y código de gobernanza).

### Informe final (formato fijo)

```
BLOQUE: BL-xx <nombre>
RAMA / COMMITS: <rama> · <sha> por task
TASKS: <ID>: hecha | parcial | bloqueada — una línea
ÁRBITRO: <comando> → <código de salida>; arnés: <línea final vista sí/no>
ARCHIVOS ESCRITOS: <lista; debe estar incluida en «Escribe»>
PARCHES PARA EL PROPIETARIO: <ninguno | archivo y motivo>
NO VERIFICADO: <lo que no pudiste comprobar>
```

## Cruces y cómo se resuelve cada uno

Una task nunca escribe un archivo que otra task de la misma tanda también escribe; cuando dos tasks comparten archivo, una depende de la otra y el orden lo impone `depende_de`.

| # | Archivo(s) | Tasks | Resolución |
| :-- | :-- | :-- | :-- |
| C1 | `api/routers/arco_router.py`, `api/routers/terceros_router.py`, `features/derechos_arco/**`, `features/terceros/**`, `features/transferencias/**` | `ADPA-01` · `RM-02` | `RM-02` antes que `ADPA-01` (depende_de) |
| C2 | `features/roadmap/**` | `RM-01` · `RM-07` | `RM-01` antes que `RM-07` (depende_de) |
| C3 | `features/roadmap/**` | `RM-01` · `RM-08` | `RM-01` antes que `RM-08` (depende_de) |
| C4 | `features/roadmap/**` | `RM-01` · `RM-09` | `RM-01` antes que `RM-09` (depende_de) |
| C5 | `features/organizacion/**` | `RM-01` · `RM-10` | `RM-01` antes que `RM-10` (depende_de) |
| C6 | `features/roadmap/**` | `RM-01` · `RM-12` | `RM-01` antes que `RM-12` (depende_de) |
| C7 | `api/routers/roadmaps.py`, `features/roadmap/**` | `RM-01` · `RM-13` | `RM-01` antes que `RM-13` (depende_de) |
| C8 | `features/organizacion/**`, `tests/test_organizacion_*.py` | `RM-01` · `RM-15` | `RM-01` antes que `RM-15` (depende_de) |
| C9 | `features/organizacion/**` | `RM-01` · `RM-16` | `RM-01` antes que `RM-16` (depende_de) |
| C10 | `api/rbac.py` | `RM-01` · `SEC-03` | `RM-01` antes que `SEC-03` (depende_de) |
| C11 | `app_core/models_base.py` | `RM-02` · `RM-15` | `RM-02` antes que `RM-15` (depende_de) |
| C12 | `main.py` | `RM-00` · `ENT-02` | `RM-00` antes que `ENT-02` (depende_de) |
| C13 | `api/routers/roadmaps.py` | `SEC-04` · `SEC-05` | `SEC-04` antes que `SEC-05` (depende_de) |
| S | `features/organizacion/organizacion_service.py` (secciones `#ID`) | `RM-10` · `RM-15` · `RM-16` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |
| S | `features/roadmap/roadmap_service.py` (secciones `#ID`) | `RM-07` · `RM-08` · `RM-09` · `RM-12` · `RM-13` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |

Archivos que solo edita un bloque por diseño: `main.py` (BL-03) y `vercel.json` (BL-11).

## Tandas de lanzamiento

Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques son independientes. Los bloques estructurales (BL-01, BL-02) van **solos**, con los demás en pausa.

| Tanda | Bloques | Nota |
| :-- | :-- | :-- |
| 0 | — | BL-01 (RM-01, estructural) ya está hecha: sin bloque pendiente. |
| 1 | — | BL-02 (RM-02, estructural) ya está hecha: sin bloque pendiente. |
| 2 | BL-18, BL-27, BL-31, BL-33, BL-36 | Documentales y de archivos disjuntos; no dependen de nada pendiente. |
| 3 | BL-13, BL-15, BL-32 | Migraciones (RM-16 y SEC-03) se integran de una en una; BL-32 sigue a BL-31. |
| 4 | BL-14, BL-34 | BL-14 requiere RM-16; BL-34 requiere SEC-03. |
| 5 | BL-26, BL-35 | Auditoría (requiere RM-10, RM-13, SEC-03 y SEC-04 a SEC-06) y tamaño único (requiere FE-07). |
| 6 | BL-25 | Cierra el plan: requiere todo lo anterior. |

## Briefs

### BL-13 · organizacion-regla-encargado  (tanda 3)

**Contexto.** Sala(s): `organizacion`. Depende de: `RM-00` (BL-03), `RM-01` (BL-01). Especificaciones: `governance/tareas/RM-16.md`.

**Objetivo** (en este orden):

1. `RM-16` — Regla del encargado con rol de responsable según el tamaño

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 12 coincidencias en 5 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_encargado_responsable_trigger.py`
  - `features/organizacion/services/regla_tamano_engine.py`
  - `tests/test_encargado_responsable_tamano.py`
  - `features/organizacion/organizacion_service.py#RM-16`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-16`: pytest tests/test_encargado_responsable_tamano.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-14 · organizacion-alta-responsables  (tanda 4)

**Contexto.** Sala(s): `organizacion`. Depende de: `RM-01` (BL-01), `RM-14` (BL-04), `RM-16` (BL-13). Especificaciones: `governance/tareas/RM-10.md`.

**Objetivo** (en este orden):

1. `RM-10` — Flujo de alta de responsables de área

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤dpo-independencia`: 9 coincidencias en 5 archivos.
- `¤rbac-tenant`: 12 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_responsable_requests.py`
  - `features/organizacion/services/solicitud_responsable_engine.py`
  - `api/routers/areas_responsable_requests.py`
  - `tests/test_responsable_requests.py`
  - `features/organizacion/organizacion_service.py#RM-10`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-10`: pytest tests/test_responsable_requests.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-15 · autenticacion-google  (tanda 3)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `RM-00` (BL-03), `RM-01` (BL-01), `ENT-01`, `RM-02`. Especificaciones: `governance/tareas/SEC-03.md`.

**Objetivo** (en este orden):

1. `SEC-03` — Autenticación verificable con Google (OIDC)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 12 coincidencias en 5 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `api/rbac.py`
  - `api/dependencies.py`
  - `app_core/security.py`
  - `requirements.txt`
  - `alembic/versions/*_users_google_sub.py`
  - `tests/test_autenticacion.py`
  - `tests/test_ai_copilot.py`
  - `tests/conftest.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No crees el cliente OAuth ni cargues secretos: es del propietario (ver «Sin agente»). Usa tokens simulados en las pruebas.

**Hecho si** (árbitro exógeno):

- `SEC-03`: pytest tests/test_autenticacion.py (tokens simulados) + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-18 · firma-electronica-boceto  (tanda 2)

**Contexto.** Sala(s): `firma_electronica`. Depende de: nada. Especificaciones: `governance/tareas/FIRMA-01.md`.

**Objetivo** (en este orden):

1. `FIRMA-01` — Firma electrónica con ANF (boceto)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤firma-electronica`: **no existe**; la primera task crea `¦firma-electronica` y lo indexa.

**Escribe** (lista exclusiva):

  - `features/firma_electronica/**`
  - `governance/arquitectura/FIRMA_ELECTRONICA_BOCETO.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Es un boceto: no integres ningún proveedor real ni cargues credenciales.

**Hecho si** (árbitro exógeno):

- `FIRMA-01`: boceto aprobado por el usuario.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

### BL-25 · pruebas-e2e-por-rol  (tanda 6)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-06` (BL-24), `RM-07` (BL-07), `RM-08` (BL-08), `RM-09` (BL-09), `RM-10` (BL-14), `RM-13` (BL-11), `SEC-03` (BL-15). Especificaciones: `governance/tareas/QA-01.md`.

**Objetivo** (en este orden):

1. `QA-01` — Pruebas de punta a punta por rol

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤arbitro`: 42 coincidencias en 5 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `frontend/tests/roadmap/e2e/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `QA-01`: frontend/tests/roadmap/e2e (Playwright).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-26 · auditoria-de-seguridad  (tanda 5)

**Contexto.** Sala(s): `gobernanza`. Depende de: `RM-10` (BL-14), `RM-13` (BL-11), `SEC-03` (BL-15). Especificaciones: `governance/tareas/SEC-02.md`.

**Objetivo** (en este orden):

1. `SEC-02` — Auditoría de seguridad previa a producción

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `governance/AUDITORIA_SEGURIDAD_HOJA_DE_RUTA.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No corrijas hallazgos en el código: regístralos en el informe y propón la task.

**Hecho si** (árbitro exógeno):

- `SEC-02`: informe sin hallazgos críticos abiertos.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

### BL-27 · operaciones-documentos  (tanda 2)

**Contexto.** Sala(s): `operaciones`. Depende de: nada. Especificaciones: `governance/tareas/CI-01.md`.

**Objetivo** (en este orden):

1. `CI-01` — Exigir ramas al día en main (solo cuando haga falta)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤ci-cd`: 20 coincidencias en 5 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `governance/operaciones/PROTECCION_MAIN.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Redactas los documentos; no cargues variables, no crees ramas de Neon ni cambies la protección de `main` (acciones del propietario).

**Hecho si** (árbitro exógeno):

- `CI-01`: `gh api repos/<repo>/branches/main/protection` muestra `required_status_checks.strict = true`.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

### BL-31 · evidencia-filtrada-por-rol  (tanda 2)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-13` (BL-11). Especificaciones: `governance/tareas/SEC-04.md`.

**Objetivo** (en este orden):

1. `SEC-04` — Evidencia filtrada por rol en la API

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 50 coincidencias en 18 archivos.
- `¤rbac-tenant`: 23 coincidencias en 13 archivos.
- `¤evidencias`: 27 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/evidencia_engine.py`
  - `api/routers/roadmaps.py`
  - `tests/test_evidencia_filtro_rol.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-04`: pytest tests/test_evidencia_filtro_rol.py tests/test_matriz_permisos.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-32 · validacion-evidencia-servidor  (tanda 3)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `SEC-04` (BL-31), `RM-00`. Especificaciones: `governance/tareas/SEC-05.md`.

**Objetivo** (en este orden):

1. `SEC-05` — Validación de evidencia en el servidor y diseño del antivirus

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 50 coincidencias en 18 archivos.
- `¤evidencias`: 27 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `app_core/storage/r2.py`
  - `app_core/errors.py`
  - `api/routers/roadmaps.py`
  - `tests/test_evidencia_validacion_servidor.py`
  - `governance/arquitectura/ANTIVIRUS_EVIDENCIA_BOCETO.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-05`: pytest tests/test_evidencia_validacion_servidor.py + suite completa; el boceto lo aprueba el propietario.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-33 · cabeceras-http-seguridad  (tanda 2)

**Contexto.** Sala(s): `pasillo_central`, `frontend`. Depende de: `RM-13` (BL-11). Especificaciones: `governance/tareas/SEC-06.md`.

**Objetivo** (en este orden):

1. `SEC-06` — Cabeceras HTTP de seguridad

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 50 coincidencias en 18 archivos.
- `¤ci-cd`: 32 coincidencias en 11 archivos.

**Escribe** (lista exclusiva):

  - `frontend/next.config.ts`
  - `vercel.json`
  - `tests/test_cabeceras_seguridad.py`
  - `frontend/tests/seguridad/cabeceras.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-06`: pytest tests/test_cabeceras_seguridad.py + Playwright de frontend/tests/seguridad + next build; la comprobación en el despliegue la hace el propietario con curl -I.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-34 · frontend-inicio-sesion  (tanda 4)

**Contexto.** Sala(s): `frontend`. Depende de: `SEC-03` (BL-15), `FE-06` (BL-24). Especificaciones: `governance/tareas/FE-07.md`.

**Objetivo** (en este orden):

1. `FE-07` — Inicio de sesión con Google en el frontend

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 50 coincidencias en 18 archivos.
- `¤frontend-ide`: 35 coincidencias en 8 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/auth/**`
  - `frontend/src/app/login/**`
  - `frontend/src/lib/roadmap/cliente.ts`
  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/tests/auth/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-07`: tsc --noEmit y next build (Pilares 2 y 3) + Playwright de frontend/tests/auth con Google simulado; el inicio de sesión real lo prueba el propietario.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-35 · tamano-fuente-unica  (tanda 5)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-07` (BL-34), `FE-05` (BL-23), `RM-15` (BL-12). Especificaciones: `governance/tareas/FE-08.md`.

**Objetivo** (en este orden):

1. `FE-08` — Una sola fuente del tamaño de la organización: ficha y backend

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤rbac-tenant`: 23 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/tamanoOrganizacion.ts`
  - `frontend/src/lib/bancoPreguntas/tipos.ts`
  - `frontend/src/components/ProjectConfig.tsx`
  - `frontend/src/components/modules/roadmap/admin/configuracion.ts`
  - `frontend/tests/tamano/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-08`: Prueba unitaria del mapeo + Playwright de frontend/tests/tamano + tsc --noEmit y next build.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-36 · arnes-playwright  (tanda 2)

**Contexto.** Sala(s): `pruebas`. Depende de: nada. Especificaciones: `governance/tareas/TEST-02.md`.

**Objetivo** (en este orden):

1. `TEST-02` — Reparar el arnés de Playwright de la raíz y valorar ejecutarlo en el CI

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤arbitro`: 61 coincidencias en 15 archivos.
- `¤frontend-ide`: 35 coincidencias en 8 archivos.

**Escribe** (lista exclusiva):

  - `frontend/tests/utiles.ts`
  - `frontend/tests/fixtures.ts`
  - `frontend/tests/assessmentDashboard.spec.ts`
  - `frontend/tests/commandPalette.spec.ts`
  - `frontend/tests/exampleWithAudit.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `TEST-02`: npx playwright test tests/assessmentDashboard.spec.ts tests/commandPalette.spec.ts tests/exampleWithAudit.spec.ts y npx playwright test tests/roadmap, con código 0.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

## Sin agente (solo el propietario)

- `GOB-01` — promover rastros nuevos al VPA: escribe `governance/artefactos/data/CANDIDATOS_VPA.json`, estado del servidor MCP; ningún agente de desarrollo lo toca. Árbitro: los rastros aparecen en el VPA servido por el MCP.
- Crear el cliente OAuth de Google y cargar sus secretos (SEC-03, BL-15).
- Cargar las variables en Vercel y revisar la lista (OPS-01, BL-27); medir una generación completa dentro de 300 s (OPS-02, BL-29).
- Verificar el dominio en Resend (NOTIF-01, BL-17).
- Crear las ramas de Neon por agente de desarrollo (OPS-04, BL-27).
- Aplicar la protección de `main` que decida (CI-01, BL-27) y cualquier parche a archivos de gobernanza reservada que un bloque entregue.
- Aprobar los bocetos de firma electrónica y notificaciones (BL-17, BL-18).
- Decidir el antivirus de la evidencia, tras leer el boceto (SEC-05, BL-32), y pasar la CSP de modo informe a modo obligatorio cuando haya observado los informes (SEC-06, BL-33).
- Crear el cliente OAuth de Google, registrar sus orígenes y cargar NEXT_PUBLIC_GOOGLE_CLIENT_ID (FE-07, BL-34).
- Aplicar el job de Playwright al workflow del CI, que es de gobernanza reservada (TEST-02, BL-36).
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
