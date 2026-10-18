# Briefs por bloque de trabajo — Hoja de Ruta Inteligente
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento:** 15 tasks abiertas (de 50; las otras 35 ya están hechas) = 14 en 14 bloques + 1 sin agente · 6 tandas · 12 cruces de archivos entre tasks (más las secciones reservadas).

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
| C11 | `app_core/models_base.py` | `RM-02` · `RM-15` | `RM-02` antes que `RM-15` (depende_de) |
| C12 | `main.py` | `RM-00` · `ENT-02` | `RM-00` antes que `ENT-02` (depende_de) |
| C14 | `features/organizacion/domain/roles.py`, `features/organizacion/services/sod_engine.py`, `tests/test_rbac_rules.py`, `tests/test_organizacion_api.py` | `RM-01` · `ORG-00` · `ORG-01` · `ORG-05` | `RM-01` → `ORG-00` → `ORG-01` → `ORG-02` → `ORG-05` (depende_de) |
| C15 | `features/organizacion/services/regla_tamano_engine.py` | `RM-16` · `ORG-00` · `ORG-02` | `ORG-00` antes que `ORG-02` (depende_de) |
| S | `features/organizacion/organizacion_service.py` (secciones `#ID`) | `RM-10` · `ORG-01` · `ORG-02` · `ORG-05` · `ORG-06` · `ORG-07` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |
| S | `features/roadmap/roadmap_service.py` (secciones `#ID`) | `RM-07` · `RM-08` · `RM-09` · `RM-12` · `RM-13` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |

Archivos que solo edita un bloque por diseño: `main.py` (BL-03) y `vercel.json` (BL-11).

## Tandas de lanzamiento

Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques son independientes. Los bloques estructurales (BL-01, BL-02) van **solos**, con los demás en pausa.

| Tanda | Bloques | Nota |
| :-- | :-- | :-- |
| 0 | — | BL-01 (RM-01, estructural) ya está hecha: sin bloque pendiente. |
| 1 | — | BL-02 (RM-02, estructural) ya está hecha: sin bloque pendiente. |
| 2 | BL-18, BL-27 | Documentales y de archivos disjuntos; no dependen de nada pendiente. |
| 3 | — | BL-13, BL-15 y BL-32 ya están hechas: sin bloque pendiente. |
| 4 | BL-14 | Alta de responsables de área (requiere RM-16, ya hecha). |
| 5 | BL-26, BL-37, BL-44, BL-45 | Retirada del token simulado (requiere SEC-03, FE-07 y RM-02, ya hechas); auditoría (requiere RM-10, RM-13, SEC-03 y SEC-04 a SEC-06); renombrado del rol `coordinador` (requiere RM-10); citas normativas de la interfaz (independiente). |
| 6 | BL-25, BL-38, BL-39 | Cierra el plan (requiere todo lo anterior); matriz de incompatibilidades y estructura orgánica (ambas requieren BL-37). |
| 7 | BL-40, BL-41, BL-42 | Excepciones de separación de funciones y designaciones formales (requieren BL-38) y pantalla de la estructura (requiere BL-39). |
| 8 | BL-43 | Alta única de roles (requiere BL-40). |

## Briefs

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

### BL-37 · rol-coordinador  (tanda 5)

**Contexto.** Sala(s): `organizacion`. Depende de: `RM-00`, `RM-01`, `RM-03`, `RM-07`, `RM-08`, `RM-09`, `RM-10` (BL-14), `RM-13`, `RM-16`, `SEC-04`, `SEC-05`, `TEST-01`, `FE-01`, `FE-02`, `FE-03`, `FE-04`, `FE-05`, `FE-06`, `FE-07`, `FE-08`. Especificaciones: `governance/tareas/ORG-00.md`.

**Objetivo** (en este orden):

1. `ORG-00` — Renombrar el rol «encargado» a «coordinador» (clave, datos, API e interfaz)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.
- `¤frontend-ide`: 35 coincidencias en 8 archivos.

**Escribe** (lista exclusiva):

  - `api/rbac.py`
  - `api/routers/roadmaps.py`
  - `api/routers/roadmaps_asignacion.py`
  - `api/routers/roadmaps_auditoria.py`
  - `features/organizacion/domain/roles.py`
  - `features/organizacion/services/regla_tamano_engine.py`
  - `features/organizacion/services/sod_engine.py`
  - `features/organizacion/services/solicitud_responsable_engine.py`
  - `api/routers/areas_responsable_requests.py`
  - `alembic/versions/*_rol_coordinador.py`
  - `governance/contratos/hoja_de_ruta.openapi.json`
  - `governance/artefactos/PRD.md`
  - `tests/test_rol_coordinador.py`
  - `tests/test_encargado_responsable_tamano.py`
  - `tests/test_evidencia_filtro_rol.py`
  - `tests/test_evidencia_http.py`
  - `tests/test_matriz_permisos.py`
  - `tests/test_organizacion_api.py`
  - `tests/test_rbac_rules.py`
  - `tests/test_roadmap_auditoria_consulta.py`
  - `tests/test_roadmap_schema.py`
  - `tests/test_roadmap_tarea_asignacion.py`
  - `tests/test_roadmap_tarea_edicion.py`
  - `tests/test_responsable_requests.py`
  - `frontend/src/types/roadmap.ts`
  - `frontend/src/lib/roadmap/mockServer.ts`
  - `frontend/src/lib/roadmap/cliente.mock.test.ts`
  - `frontend/src/components/modules/roadmap/admin/RolesTab.tsx`
  - `frontend/src/components/modules/roadmap/admin/ConfiguracionTab.tsx`
  - `frontend/src/components/modules/roadmap/admin/errores.ts`
  - `frontend/src/components/modules/roadmap/evidencia/EvidenciaPanel.tsx`
  - `frontend/src/components/modules/roadmap/evidencia/reglas.ts`
  - `frontend/src/components/modules/roadmap/olas/permisos.ts`
  - `frontend/src/app/harness-roadmap/admin/HarnessAdmin.tsx`
  - `frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx`
  - `frontend/src/app/harness-roadmap/evidencia/page.tsx`
  - `frontend/src/app/harness-roadmap/olas/HarnessOlas.tsx`
  - `frontend/src/app/harness-roadmap/planeacion/HarnessPlaneacion.tsx`
  - `frontend/tests/auth/identidad.spec.ts`
  - `frontend/tests/roadmap/admin.spec.ts`
  - `frontend/tests/roadmap/evidencia.spec.ts`
  - `frontend/tests/roadmap/integracion.spec.ts`
  - `frontend/tests/roadmap/olas.spec.ts`
  - `frontend/tests/roadmap/planeacion.spec.ts`
  - `frontend/tests/tamano/ficha.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-00`: pytest tests/test_rol_coordinador.py tests/test_matriz_permisos.py + suite completa; Playwright de frontend/tests/roadmap, tests/auth y tests/tamano; tsc --noEmit y next build.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-38 · matriz-incompatibilidades  (tanda 6)

**Contexto.** Sala(s): `organizacion`. Depende de: `ORG-00` (BL-37), `RM-01`, `RM-10` (BL-14), `RM-16`. Especificaciones: `governance/tareas/ORG-01.md`.

**Objetivo** (en este orden):

1. `ORG-01` — Una sola matriz de incompatibilidades de roles, con su base legal; el DPO sin roles operativos

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.
- `¤seguridad`: 55 coincidencias en 25 archivos.

**Escribe** (lista exclusiva):

  - `governance/artefactos/PRD.md`
  - `features/organizacion/domain/roles.py`
  - `features/organizacion/services/sod_engine.py`
  - `alembic/versions/*_dpo_sin_roles_operativos.py`
  - `tests/test_rbac_rules.py`
  - `tests/test_matriz_incompatibilidades.py`
  - `features/organizacion/organizacion_service.py#ORG-01`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-01`: pytest tests/test_matriz_incompatibilidades.py tests/test_rbac_rules.py + suite completa; el cambio del PRD lo aprueba el propietario.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-39 · estructura-organica  (tanda 6)

**Contexto.** Sala(s): `organizacion`. Depende de: `ORG-00` (BL-37), `RM-01`, `RM-10` (BL-14). Especificaciones: `governance/tareas/ORG-07.md`.

**Objetivo** (en este orden):

1. `ORG-07` — Estructura orgánica: unidades, cargos y jefaturas como base de los responsables de área

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_estructura_organica.py`
  - `features/organizacion/services/estructura_engine.py`
  - `api/routers/organizacion_estructura.py`
  - `tests/test_estructura_organica.py`
  - `features/organizacion/organizacion_service.py#ORG-07`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-07`: pytest tests/test_estructura_organica.py tests/test_matriz_permisos.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-40 · excepciones-sod  (tanda 7)

**Contexto.** Sala(s): `organizacion`. Depende de: `ORG-01` (BL-38), `RM-10` (BL-14), `RM-16`. Especificaciones: `governance/tareas/ORG-02.md`.

**Objetivo** (en este orden):

1. `ORG-02` — Excepciones de separación de funciones, explícitas y con fin, en lugar de «permitido por tamaño»

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.
- `¤seguridad`: 55 coincidencias en 25 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_sod_exceptions.py`
  - `features/organizacion/services/excepcion_sod_engine.py`
  - `features/organizacion/services/regla_tamano_engine.py`
  - `api/routers/organizacion_excepciones_sod.py`
  - `tests/test_excepciones_sod.py`
  - `features/organizacion/organizacion_service.py#ORG-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-02`: pytest tests/test_excepciones_sod.py tests/test_encargado_responsable_tamano.py tests/test_matriz_permisos.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-41 · designaciones-formales  (tanda 7)

**Contexto.** Sala(s): `organizacion`. Depende de: `ORG-01` (BL-38), `ORG-07` (BL-39), `RM-10` (BL-14). Especificaciones: `governance/tareas/ORG-06.md`.

**Objetivo** (en este orden):

1. `ORG-06` — Designaciones formales: delegado de protección de datos (con inscripción y declaración) y mandato de la alta dirección al coordinador

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.
- `¤seguridad`: 55 coincidencias en 25 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_designaciones_formales.py`
  - `features/organizacion/services/designacion_engine.py`
  - `api/routers/organizacion_designaciones.py`
  - `tests/test_designaciones_formales.py`
  - `features/organizacion/organizacion_service.py#ORG-06`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-06`: pytest tests/test_designaciones_formales.py tests/test_matriz_permisos.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-42 · pantalla-estructura  (tanda 7)

**Contexto.** Sala(s): `frontend`. Depende de: `ORG-07` (BL-39), `ORG-00` (BL-37), `FE-05`. Especificaciones: `governance/tareas/FE-09.md`.

**Objetivo** (en este orden):

1. `FE-09` — Pestaña «Estructura» de la administración: unidades, cargos, jefaturas y vacantes

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤rbac-tenant`: 25 coincidencias en 17 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/admin/EstructuraTab.tsx`
  - `frontend/src/components/modules/roadmap/admin/estructura.ts`
  - `frontend/src/components/modules/roadmap/admin/AdminPanel.tsx`
  - `frontend/src/components/modules/roadmap/admin/index.ts`
  - `frontend/tests/estructura/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-09`: Playwright de frontend/tests/estructura con la API simulada + tsc --noEmit y next build.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-43 · alta-unica-roles  (tanda 8)

**Contexto.** Sala(s): `organizacion`. Depende de: `ORG-02` (BL-40), `RM-01`, `RM-10` (BL-14), `SEC-03`. Especificaciones: `governance/tareas/ORG-05.md`.

**Objetivo** (en este orden):

1. `ORG-05` — Un único camino de altas de roles; sin concesión a uno mismo

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 25 coincidencias en 17 archivos.
- `¤seguridad`: 55 coincidencias en 25 archivos.

**Escribe** (lista exclusiva):

  - `features/organizacion/services/roles_engine.py`
  - `api/routers/organizacion.py`
  - `tests/test_alta_unica_roles.py`
  - `features/organizacion/organizacion_service.py#ORG-05`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-05`: pytest tests/test_alta_unica_roles.py tests/test_organizacion_api.py tests/test_matriz_permisos.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-44 · citas-normativas  (tanda 5)

**Contexto.** Sala(s): `frontend`. Depende de: nada. Especificaciones: `governance/tareas/LEG-01.md`.

**Objetivo** (en este orden):

1. `LEG-01` — Citas normativas de la interfaz coherentes con la LOPDP

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤arbitro`: 64 coincidencias en 18 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/DpoCockpitModule.tsx`
  - `frontend/src/components/modules/MtgeRelacionalModule.tsx`
  - `frontend/tests/legal/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `LEG-01`: npx playwright test tests/legal + tsc --noEmit y next build.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-45 · retirar-token-simulado  (tanda 5)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `SEC-03`, `FE-07`, `RM-02`. Especificaciones: `governance/tareas/SEC-07.md`.

**Objetivo** (en este orden):

1. `SEC-07` — Retirar la compatibilidad del token simulado en el modo headers

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 55 coincidencias en 25 archivos.
- `¤rbac-tenant`: 25 coincidencias en 17 archivos.

**Escribe** (lista exclusiva):

  - `app_core/security.py`
  - `tests/test_autenticacion.py`
  - `tests/test_api_integracion.py`
  - `tests/test_e2e_flujo_completo.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-07`: pytest tests/test_autenticacion.py tests/test_api_integracion.py tests/test_e2e_flujo_completo.py tests/test_ai_copilot.py + suite completa; Playwright de frontend/tests/auth.
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
- Antes de aplicar la migración de ORG-00, volver a medir cuántas personas tienen el rol `encargado` en producción (el 2026-10-18 eran 0); si hubiera alguna, se aplica en un momento sin uso.
- Las decisiones de diseño de ORG-01, ORG-02, ORG-06 y ORG-07 se asumieron con su base legal (véase «Decisiones asumidas» de cada especificación) y se revisan si la Superintendencia emite normativa adicional, que la propia norma prevé.
- Los plazos (notificación de vulneraciones, inscripción del delegado, vigencia de las excepciones) quedan aplazados por decisión del propietario.
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
