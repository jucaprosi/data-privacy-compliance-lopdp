# Briefs por bloque de trabajo — Hoja de Ruta Inteligente
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento:** 32 tasks abiertas (de 34; ENT-01 y GOB-02 ya están hechas) = 31 en 29 bloques + 1 sin agente · 7 tandas · 11 cruces de archivos entre tasks (más las secciones reservadas).

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
| S | `features/organizacion/organizacion_service.py` (secciones `#ID`) | `RM-10` · `RM-15` · `RM-16` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |
| S | `features/roadmap/roadmap_service.py` (secciones `#ID`) | `RM-07` · `RM-08` · `RM-09` · `RM-12` · `RM-13` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |

Archivos que solo edita un bloque por diseño: `main.py` (BL-03) y `vercel.json` (BL-11).

## Tandas de lanzamiento

Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques son independientes. Los bloques estructurales (BL-01, BL-02) van **solos**, con los demás en pausa.

| Tanda | Bloques | Nota |
| :-- | :-- | :-- |
| 0 | BL-01 | Estructural: mueve código de organización y hoja de ruta. Va solo. |
| 1 | BL-02 | Estructural: cambia la sesión de BD y los imports de varias salas. Va solo. |
| 2 | BL-03, BL-04, BL-05, BL-06, BL-07, BL-08, BL-09, BL-10, BL-16, BL-18, BL-27, BL-28 | Aditivos y de archivos disjuntos. |
| 3 | BL-11, BL-12, BL-13, BL-15, BL-17, BL-19 | Requieren bloques de las tandas 0 a 2 integrados. |
| 4 | BL-14, BL-20, BL-21, BL-22, BL-23, BL-29 | Requieren la tanda 3. |
| 5 | BL-24, BL-26 | Integración y auditoría. |
| 6 | BL-25 | Cierra el plan: requiere todo lo anterior. |

## Briefs

### BL-01 · reestructura-organizacion-roadmap  (tanda 0)

**Contexto.** Sala(s): `organizacion`, `roadmap`. Bloque **estructural**: va solo. Depende de: nada. Especificaciones: `governance/tareas/RM-01.md`.

**Objetivo** (en este orden):

1. `RM-01` — Reestructuración ADPA: salas Organización y Hoja de Ruta

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤adpa`: 40 coincidencias en 10 archivos.
- `¤rbac-tenant`: 12 coincidencias en 5 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/organizacion/**`
  - `features/roadmap/**`
  - `api/rbac.py`
  - `api/routers/organizacion.py`
  - `api/routers/roadmaps.py`
  - `app_core/services/**`
  - `app_core/schemas/**`
  - `app_core/workers/**`
  - `app_core/ai/roadmap_prompts.py`
  - `tests/test_organizacion_*.py`
  - `tests/test_roadmap_service.py`
  - `tests/test_roadmaps_api.py`
  - `tests/test_adpa_bulkhead.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No cambies el comportamiento de ningún endpoint: solo mueves y reexportas. Ningún otro bloque corre mientras este no esté integrado.

**Hecho si** (árbitro exógeno):

- `RM-01`: suite existente de organización y roadmaps en verde + pytest tests/test_adpa_bulkhead.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-02 · sesion-bd-unica  (tanda 1)

**Contexto.** Sala(s): `pasillo_central`. Bloque **estructural**: va solo. Depende de: nada. Especificaciones: `governance/tareas/RM-02.md`.

**Objetivo** (en este orden):

1. `RM-02` — Sesión de BD única y cero SQL interpolado

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤adpa`: 40 coincidencias en 10 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `app_core/database.py`
  - `app_core/db/**`
  - `api/routers/ai_copilot.py`
  - `api/routers/arco_router.py`
  - `api/routers/terceros_router.py`
  - `app_core/models_base.py`
  - `features/derechos_arco/domain/models.py`
  - `features/terceros/domain/models.py`
  - `features/transferencias/services/encargados_service.py`
  - `scripts/seed_database.py`
  - `tests/test_database_rls.py`
  - `tests/test_ai_copilot.py`
  - `tests/test_api_integracion.py`
  - `tests/test_sin_sql_interpolado.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No cambies firmas públicas de las compuertas; solo la sesión de BD y el SQL. Ningún otro bloque corre mientras este no esté integrado.

**Hecho si** (árbitro exógeno):

- `RM-02`: pytest tests/test_sin_sql_interpolado.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-03 · andamiaje-compartido  (tanda 2)

**Contexto.** Sala(s): `pasillo_central`. Depende de: nada. Especificaciones: `governance/tareas/RM-00.md`.

**Objetivo** (en este orden):

1. `RM-00` — Andamiaje compartido: contrato, autoregistro de routers, errores y una sola cabeza de migraciones

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤adpa`: 40 coincidencias en 10 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `scripts/exportar_contrato_hoja_ruta.py`
  - `governance/contratos/**`
  - `main.py`
  - `app_core/errors.py`
  - `api/errores.py`
  - `tests/test_contrato_hoja_ruta.py`
  - `tests/test_registro_automatico_routers.py`
  - `tests/test_errores_negocio.py`
  - `tests/test_alembic_una_cabeza.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Eres el único bloque que edita `main.py`; los demás no lo tocan (el autoregistro de routers existe para eso).

**Hecho si** (árbitro exógeno):

- `RM-00`: pytest tests/test_contrato_hoja_ruta.py tests/test_registro_automatico_routers.py tests/test_errores_negocio.py tests/test_alembic_una_cabeza.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-04 · audit-events  (tanda 2)

**Contexto.** Sala(s): `pasillo_central`. Depende de: nada. Especificaciones: `governance/tareas/RM-14.md`.

**Objetivo** (en este orden):

1. `RM-14` — Tabla audit_events y registro de eventos

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 15 coincidencias en 7 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_audit_events.py`
  - `app_core/audit.py`
  - `tests/test_audit_events.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-14`: pytest tests/test_audit_events.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-05 · matriz-de-permisos  (tanda 2)

**Contexto.** Sala(s): `pruebas`. Depende de: nada. Especificaciones: `governance/tareas/RM-03.md`.

**Objetivo** (en este orden):

1. `RM-03` — Matriz de permisos como prueba

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤arbitro`: 42 coincidencias en 5 archivos.
- `¤rbac-tenant`: 12 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `tests/test_matriz_permisos.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-03`: pytest tests/test_matriz_permisos.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-06 · cobertura-evidencia-redis  (tanda 2)

**Contexto.** Sala(s): `pruebas`. Depende de: `RM-01` (BL-01). Especificaciones: `governance/tareas/TEST-01.md`.

**Objetivo** (en este orden):

1. `TEST-01` — Cobertura pendiente de evidencia y Redis

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤arbitro`: 42 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `tests/test_evidencia_http.py`
  - `tests/test_redis_client.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `TEST-01`: pytest tests/test_evidencia_http.py tests/test_redis_client.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-07 · roadmap-edicion  (tanda 2)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-01` (BL-01). Especificaciones: `governance/tareas/RM-07.md`.

**Objetivo** (en este orden):

1. `RM-07` — Editar tareas de la hoja de ruta

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/tarea_edicion_engine.py`
  - `api/routers/roadmaps_edicion.py`
  - `tests/test_roadmap_tarea_edicion.py`
  - `features/roadmap/roadmap_service.py#RM-07`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-07`: pytest tests/test_roadmap_tarea_edicion.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-08 · roadmap-asignacion  (tanda 2)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-01` (BL-01). Especificaciones: `governance/tareas/RM-08.md`.

**Objetivo** (en este orden):

1. `RM-08` — Distribuir tareas a los responsables

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 12 coincidencias en 5 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/tarea_asignacion_engine.py`
  - `api/routers/roadmaps_asignacion.py`
  - `tests/test_roadmap_tarea_asignacion.py`
  - `features/roadmap/roadmap_service.py#RM-08`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-08`: pytest tests/test_roadmap_tarea_asignacion.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-09 · roadmap-consulta-auditoria  (tanda 2)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-01` (BL-01). Especificaciones: `governance/tareas/RM-09.md`.

**Objetivo** (en este orden):

1. `RM-09` — Consultar el audit log

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 15 coincidencias en 7 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/auditoria_consulta_engine.py`
  - `api/routers/roadmaps_auditoria.py`
  - `tests/test_roadmap_auditoria_consulta.py`
  - `features/roadmap/roadmap_service.py#RM-09`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-09`: pytest tests/test_roadmap_auditoria_consulta.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-10 · roadmap-generacion-ia  (tanda 2)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-01` (BL-01). Especificaciones: `governance/tareas/RM-12.md`.

**Objetivo** (en este orden):

1. `RM-12` — Generación fiable con IA

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤copiloto-ia`: 29 coincidencias en 7 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/ai/**`
  - `features/roadmap/services/generacion_engine.py`
  - `tests/test_roadmap_generacion.py`
  - `features/roadmap/roadmap_service.py#RM-12`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-12`: pytest tests/test_roadmap_generacion.py (modelo simulado).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-11 · roadmap-generacion-en-linea  (tanda 3)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-12` (BL-10). Especificaciones: `governance/tareas/RM-13.md`.

**Objetivo** (en este orden):

1. `RM-13` — Generación en línea (decisión D-1)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤adpa`: 40 coincidencias en 10 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `vercel.json`
  - `features/roadmap/services/generacion_en_linea.py`
  - `api/routers/roadmaps.py`
  - `tests/test_roadmap_generacion_en_linea.py`
  - `features/roadmap/roadmap_service.py#RM-13`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- `vercel.json` y `api/routers/roadmaps.py` los editas tú, después de BL-01; no cambies la configuración de la cuenta de Vercel (es del propietario).

**Hecho si** (árbitro exógeno):

- `RM-13`: pytest tests/test_roadmap_generacion_en_linea.py + tests/test_matriz_permisos.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-12 · organizacion-configuracion  (tanda 3)

**Contexto.** Sala(s): `organizacion`. Depende de: `RM-01` (BL-01), `RM-02` (BL-02), `RM-14` (BL-04). Especificaciones: `governance/tareas/RM-15.md`.

**Objetivo** (en este orden):

1. `RM-15` — Configuración de la organización y vocabulario de tamaños

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 59 coincidencias en 9 archivos.
- `¤rbac-tenant`: 12 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_tenants_tamano_check.py`
  - `features/organizacion/services/configuracion_engine.py`
  - `api/routers/organizacion_configuracion.py`
  - `app_core/models_base.py`
  - `app_core/models.py`
  - `tests/test_organizacion_configuracion.py`
  - `features/organizacion/organizacion_service.py#RM-15`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `RM-15`: pytest tests/test_organizacion_configuracion.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

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

**Contexto.** Sala(s): `pasillo_central`. Depende de: `RM-00` (BL-03), `RM-01` (BL-01). Especificaciones: `governance/tareas/SEC-03.md`.

**Objetivo** (en este orden):

1. `SEC-03` — Autenticación verificable con Google (OIDC)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 12 coincidencias en 5 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `api/rbac.py`
  - `api/dependencies.py`
  - `alembic/versions/*_users_google_sub.py`
  - `tests/test_autenticacion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No crees el cliente OAuth ni cargues secretos: es del propietario (ver «Sin agente»). Usa tokens simulados en las pruebas.

**Hecho si** (árbitro exógeno):

- `SEC-03`: pytest tests/test_autenticacion.py (tokens simulados) + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-16 · compuertas-arco-terceros-transferencias  (tanda 2)

**Contexto.** Sala(s): `derechos_arco`, `terceros`, `transferencias`. Depende de: `RM-02` (BL-02). Especificaciones: `governance/tareas/ADPA-01.md`.

**Objetivo** (en este orden):

1. `ADPA-01` — Compuertas de las salas Derechos ARCO, Terceros y Transferencias

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤adpa`: 40 coincidencias en 10 archivos.
- `¤derechos`: 5 coincidencias en 4 archivos.
- `¤transferencias`: 5 coincidencias en 4 archivos.

**Escribe** (lista exclusiva):

  - `features/derechos_arco/**`
  - `features/terceros/**`
  - `features/transferencias/**`
  - `api/routers/arco_router.py`
  - `api/routers/terceros_router.py`
  - `tests/test_compuertas_arco_terceros_transferencias.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `ADPA-01`: pytest tests/test_compuertas_arco_terceros_transferencias.py tests/test_adpa_bulkheads.py + suite completa.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-17 · notificaciones-boceto  (tanda 3)

**Contexto.** Sala(s): `notificaciones`. Depende de: `RM-08` (BL-08). Especificaciones: `governance/tareas/NOTIF-01.md`.

**Objetivo** (en este orden):

1. `NOTIF-01` — Notificaciones por correo (boceto)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/notificaciones/**`
  - `tests/test_notificaciones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Es un boceto: no envíes correo ni configures el dominio de Resend.

**Hecho si** (árbitro exógeno):

- `NOTIF-01`: boceto aprobado por el usuario.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

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

### BL-19 · frontend-cliente-y-store  (tanda 3)

**Contexto.** Sala(s): `frontend`. Depende de: `RM-00` (BL-03). Especificaciones: `governance/tareas/FE-01.md`.

**Objetivo** (en este orden):

1. `FE-01` — Cliente de API y store del frontend

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/roadmap/**`
  - `frontend/src/store/useRoadmapStore.ts`
  - `frontend/src/types/roadmap.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-01`: tsc --noEmit y next build (Pilares 2 y 3 del arnés) + prueba del cliente contra el mock.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-20 · frontend-planeacion  (tanda 4)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-01` (BL-19). Especificaciones: `governance/tareas/FE-02.md`.

**Objetivo** (en este orden):

1. `FE-02` — Formulario de variables de planeación y generación

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/planeacion/**`
  - `frontend/tests/roadmap/planeacion.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-02`: Pilares 2 y 3 del arnés + frontend/tests/roadmap/planeacion.spec.ts (Playwright contra el mock).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-21 · frontend-olas  (tanda 4)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-01` (BL-19). Especificaciones: `governance/tareas/FE-03.md`.

**Objetivo** (en este orden):

1. `FE-03` — Vista de olas y tareas

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/olas/**`
  - `frontend/tests/roadmap/olas.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-03`: Pilares 2 y 3 del arnés + frontend/tests/roadmap/olas.spec.ts.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-22 · frontend-evidencia  (tanda 4)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-01` (BL-19). Especificaciones: `governance/tareas/FE-04.md`.

**Objetivo** (en este orden):

1. `FE-04` — Panel de evidencia

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 27 coincidencias en 9 archivos.
- `¤frontend-ide`: 35 coincidencias en 8 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/evidencia/**`
  - `frontend/tests/roadmap/evidencia.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-04`: Pilares 2 y 3 del arnés + frontend/tests/roadmap/evidencia.spec.ts.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-23 · frontend-administracion  (tanda 4)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-01` (BL-19). Especificaciones: `governance/tareas/FE-05.md`.

**Objetivo** (en este orden):

1. `FE-05` — Administración de la organización

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤rbac-tenant`: 12 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/admin/**`
  - `frontend/tests/roadmap/admin.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-05`: Pilares 2 y 3 del arnés + frontend/tests/roadmap/admin.spec.ts.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-24 · frontend-integracion  (tanda 5)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-02` (BL-20), `FE-03` (BL-21), `FE-04` (BL-22), `FE-05` (BL-23). Especificaciones: `governance/tareas/FE-06.md`.

**Objetivo** (en este orden):

1. `FE-06` — Integración del frontend

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤interfaz`: 12 coincidencias en 1 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/types/index.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `FE-06`: Pilares 2 y 3 del arnés.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

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

**Contexto.** Sala(s): `operaciones`. Depende de: nada. Especificaciones: `governance/tareas/OPS-01.md`, `governance/tareas/OPS-04.md`, `governance/tareas/CI-01.md`.

**Objetivo** (en este orden):

1. `OPS-01` — Variables de entorno en Vercel
2. `OPS-04` — Rama de Neon por agente de desarrollo
3. `CI-01` — Exigir ramas al día en main (solo cuando haga falta)

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤ci-cd`: 20 coincidencias en 5 archivos.
- `¤seguridad`: 35 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `governance/operaciones/VARIABLES_VERCEL.md`
  - `governance/operaciones/RAMAS_NEON_DE_DESARROLLO.md`
  - `governance/operaciones/PROTECCION_MAIN.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Redactas los documentos; no cargues variables, no crees ramas de Neon ni cambies la protección de `main` (acciones del propietario).

**Hecho si** (árbitro exógeno):

- `OPS-01`: lista revisada por el usuario; cada variable cargada en su entorno.
- `OPS-04`: un agente de desarrollo conecta a su rama test-<agente> y comprueba que el rol lopdp_app existe.
- `CI-01`: `gh api repos/<repo>/branches/main/protection` muestra `required_status_checks.strict = true`.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

### BL-28 · operaciones-verificar-despliegue  (tanda 2)

**Contexto.** Sala(s): `operaciones`. Depende de: nada. Especificaciones: `governance/tareas/OPS-03.md`.

**Objetivo** (en este orden):

1. `OPS-03` — Script de verificación de despliegue

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤arbitro`: 42 coincidencias en 5 archivos.
- `¤ci-cd`: 20 coincidencias en 5 archivos.

**Escribe** (lista exclusiva):

  - `scripts/verificar_despliegue.py`
  - `tests/test_verificar_despliegue.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.

**Hecho si** (árbitro exógeno):

- `OPS-03`: pytest tests/test_verificar_despliegue.py.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-29 · operaciones-verificar-generacion  (tanda 4)

**Contexto.** Sala(s): `operaciones`. Depende de: `OPS-01` (BL-27), `RM-13` (BL-11). Especificaciones: `governance/tareas/OPS-02.md`.

**Objetivo** (en este orden):

1. `OPS-02` — Verificar la generación en el entorno gratuito

**Rastro ¤** (verificado con `git grep --untracked -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 15 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `governance/operaciones/VERIFICACION_GENERACION.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- Redactas el procedimiento; la medición real contra Vercel la ejecuta el propietario.

**Hecho si** (árbitro exógeno):

- `OPS-02`: una generación completa termina dentro de 300 s en Vercel.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
- **Parte del propietario:** el árbitro de estas tasks no es una prueba automática (ver «Sin agente»); tu parte termina cuando el documento o boceto existe y queda enlazado desde su task.

## Sin agente (solo el propietario)

- `GOB-01` — promover rastros nuevos al VPA: escribe `governance/artefactos/data/CANDIDATOS_VPA.json`, estado del servidor MCP; ningún agente de desarrollo lo toca. Árbitro: los rastros aparecen en el VPA servido por el MCP.
- Crear el cliente OAuth de Google y cargar sus secretos (SEC-03, BL-15).
- Cargar las variables en Vercel y revisar la lista (OPS-01, BL-27); medir una generación completa dentro de 300 s (OPS-02, BL-29).
- Verificar el dominio en Resend (NOTIF-01, BL-17).
- Crear las ramas de Neon por agente de desarrollo (OPS-04, BL-27).
- Aplicar la protección de `main` que decida (CI-01, BL-27) y cualquier parche a archivos de gobernanza reservada que un bloque entregue.
- Aprobar los bocetos de firma electrónica y notificaciones (BL-17, BL-18).
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
