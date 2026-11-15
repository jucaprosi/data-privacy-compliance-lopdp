# Programa RET: mapa de eliminación por ficha
`¤sdd`

Arquitecto ADPA, 2026-11-14. Las plataformas que Google Cloud reemplazó se eliminan del repositorio como si nunca se hubiera trabajado con ellas. Ninguna regla, invariante ni árbitro las nombra o las prohíbe. Cada PR de eliminación tiene como árbitro la suite existente en verde. La historia queda en git.

Medido en `origin/main` b216ab4e:
- 137 archivos fuera de `governance/` nombran las plataformas;
- unos 220 dentro de `governance/`;
- ninguno en `.github/`, `scripts/` ni `.githooks/`.

## 1. Mapa

Criterio de cada fila: un archivo que nombra una plataforma no es por eso de esa plataforma. **Se borra** solo lo que existe únicamente para ella. **Se reescribe** lo que tiene una función viva (arneses, guardias de base local, pruebas de dominio, componentes): se cambia la parte de la plataforma y se conserva el resto. Las cuatro pruebas que borra RET-00 existen solo para vigilar plataformas (medido en `origin/main`).

| Ficha | Qué borra y qué reescribe | Brief al propietario |
| :--- | :--- | :--- |
| **RET-00** | Las pruebas que vigilaban plataformas: `tests/plataforma_unica/` y `test_plataforma_unica.py`, la carpeta de la guardia de huellas y su prueba, `test_ci17_…`, `test_vercel_despliegue.py`. Va primero. | no |
| **RET-01a** (#809) | La carga de archivos de entorno en `tests/conftest.py` y la guardia antigua de la suite. Deja `exigir_base_de_pruebas()` con la lista blanca local. | no |
| **RET-01** | Borra `python-dotenv` y `.env.example`. Reescribe `app_core/config.py` (configuración desde el entorno del proceso), `huellas_produccion.py`, `cloud/gcp_runtime.py` y las guardias de arranque, quitando solo las variables de las plataformas. Reescribe sus pruebas: `test_sec15/16/17/20`, `test_ep01`, `test_ep05`, `test_demo_purga`, `test_conftest_entorno` y `test_base_por_trabajador`. | sí: borrar los secretos de las plataformas en Secret Manager y en GitHub |
| **RET-02** | Borra el adaptador del almacén anterior en `app_core/storage/` y sus paquetes; el adaptador de Cloud Storage se conserva. Reescribe, sin borrarlos, en el frontend: `EvidenciaPanel.tsx`, `subirEvidencia.ts`, `HarnessEvidencia.tsx`, `useRoadmapStore.ts`, `types/roadmap.ts`, `generar_tipos.js`, `cliente.mock.test.ts`, los e2e de `criterio12`, `next.config.ts` y `features/roadmap/domain/models.py`. La columna `r2_key` se renombra a `clave_objeto` con una migración nueva, `ret02_clave_objeto.py`. | no |
| **RET-03** | Borra el cliente de la cola anterior en `app_core/queue/`, su paquete y `test_redis_client.py`; si un llamador sigue vivo, pasa al puerto de Cloud Tasks. | sí, solo si se usa Cloud Tasks: crear la cola |
| **RET-04** (nueva) | Borra el cliente de IA anterior en `app_core/ai/` y sus variables. Reescribe hacia Vertex AI `assistant_provider.py`, `preanalisis/services/proveedor.py` y `roadmap/ai/client.py`, y reescribe sus pruebas de dominio (`test_ai_copilot_motivo_neutro`, `test_preanalisis`, `test_preanalisis_motivo_neutro`, `test_ia07_asistente_inferencia`). | no |
| **RET-05** | Borra `vercel.json` y `frontend/vercel.json`. Reescribe, quitando solo la rama de entrada anterior, `security.py`, `bucle_eventos.py`, `firma_anf.py`, `modo.ts`, `frontend/.dockerignore`, `frontend/README.md` y `cabeceras.spec.ts`; regenera los archivos de bloqueo y, si conviven dos, borra uno. | sí: borrar el proyecto de la plataforma de despliegue anterior |
| **RET-06** | Las pruebas que comprueban la base por su cuenta pasan a `exigir_base_de_pruebas()`. Las que llevan fixtures o comentarios de la base anterior se limpian: `test_bib117`, `test_bib_203/205/206/207`, `test_diagnostico_respuestas`, `test_diag12_estados`, las dos configuraciones de Playwright de extremo a extremo (`frontend/playwright.humo.config.ts` y `frontend/playwright.integracion.config.ts`) con `tests/humo/servidor_humo.py`, `test_evidencia_*`, `test_org_14`, `test_organizacion_*`, `test_rat_plantilla_salud`, `test_roadmap_control_ref`, `exportacion_engine.py` y `duraciones.json`. Si una mención es de almacén, cola o IA, va a RET-02, RET-03 o RET-04. | no |
| **RET-08** (nueva) | Borra el boceto del proveedor de correo anterior en `features/notificaciones/` y reescribe `test_notificaciones.py` contra el puerto. Queda el puerto con el doble de pruebas. | sí: elegir el proveedor (§3) |
| **RET-09** (nueva) | Documentación (§2). | no |
| **RET-10** (nueva) | Los comentarios de las migraciones aplicadas (§4). | no |

**Tokens de código.** RET-04 cambia en `assistant_provider.py` los tokens `¤esquema-deepseek` y `¤validar-salida-deepseek` por los neutros. `¤esquema-asistente` y `¤validar-salida-asistente` ya están indexados en `VPA_MAP.md`.

**Artefactos vivos.** `APORTES_INEDITOS.md`, `FUENTES_Y_BIBLIOGRAFIA.md` y `CANDIDATOS_VPA.json` van a RET-09. `TASKS.md` lo actualiza el Tech Lead al fusionar cada ficha. `PROBLEMS.json` no nombra ninguna plataforma.

## 2. Documentación (RET-09)

- **Se borran:**
  - `governance/historico/pmv/` entero;
  - `governance/operaciones/VERIFICACION_GENERACION.md`;
  - `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`;
  - `PROCESO_REESTRUCTURACION_COPILOTO.md`;
  - todo documento cuyo único tema sea una plataforma.
- **Se reescriben las menciones sueltas**, sin tocar encabezados, tokens, roles ni candados:
  - las guías de operaciones (`PRUEBAS_EN_FISICO.md` §6 pasa al PostgreSQL local);
  - los documentos raíz de `governance/`, los de arquitectura y los de apoyo;
  - en `APORTES_INEDITOS.md` y `FUENTES_Y_BIBLIOGRAFIA.md`, se retira el aporte o la fuente cuyo contenido es solo la plataforma, y se reescribe en términos neutros el que enseña algo general;
  - los números retirados no se reutilizan.
- **Fichas hechas de las plataformas** (la serie de cinco de la base anterior y las que solo la migraban), de modo que los árbitros de índice y reparto sigan en verde:
  1. En el mismo PR, se quitan sus ids del `depende_de` de cada ficha que las cita: `CI-24`, `CI-28`, `CI-29`, `IA-08`, `RET-01`, `RET-05` y `RET-06`, más las que encuentre la ficha.
  2. Se borran la ficha, su brief en `governance/apoyo/briefs/` y su especificación, si existe.
  3. Se corre `generar_indice_tareas.py` y `verificar_reparto.py`. Si una ficha queda sin dependencias, su `depende_de` pasa a `[]`.
  4. Las fichas que solo mencionan una plataforma de pasada se reescriben y se conservan.
- **Decisión del propietario:** `data/*.pdf` y el resto de `data/` son material suyo. RET-09 no los toca, y el propietario decide si alguno se borra.

## 3. Decisión pendiente: proveedor de correo

Google Cloud no tiene un servicio gestionado de correo transaccional. Recomiendo la **Gmail API de Google Workspace**: la cuenta de servicio de Cloud Run envía con delegación limitada al envío y la credencial vive en Secret Manager. La alternativa es el relé SMTP de Workspace. Mientras el propietario no decida, RET-08 deja solo el puerto.

## 4. Migraciones aplicadas (RET-10)

- **Medido:** Alembic 1.20.0 identifica cada migración por su revisión. La tabla `alembic_version` solo guarda `version_num`, y `alembic.runtime.migration` no calcula ninguna suma del contenido. Por eso reescribir comentarios y docstrings no cambia las cabezas ni rompe nada en las bases ya migradas.
- **Qué se toca:** solo los comentarios y docstrings de `20261008_app_role_rls.py` y `20261108_biblioteca_capacidades_propietario.py`. Ni `upgrade`/`downgrade` ni los ids.
- **Comprobación del PR:** el AST de cada archivo, sin docstrings, debe quedar idéntico al de `origin/main`. Se comprueba una sola vez al revisar el PR y no queda como prueba permanente.
- **Fuera de alcance:** `r2_key` en `20261005_roadmaps.py` y `org20_papelera.py` es esquema vivo. Lo renombra la migración nueva de RET-02.

## 5. Orden

La propagación va de arriba abajo:
1. PRD, INVARIANTS y VPA_MAP (este PR);
2. especificaciones, empezando por las RET;
3. fichas, briefs y artefactos vivos;
4. código, pruebas y configuración;
5. `verificadores/` y `.github/workflows/`, que son del propietario: `governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`.

Las fichas se fusionan en este orden:

1. **RET-00 y RET-01a.** Sin las pruebas que vigilaban plataformas, las demás fichas solo borran código.
2. **En paralelo,** porque no comparten archivos: RET-01, RET-02, RET-03, RET-04, RET-05, RET-06, RET-08 y RET-10.
3. **RET-09,** al final, porque sus fichas y briefs citan las anteriores.
4. **Briefs al propietario,** cada uno después de su ficha: los secretos (RET-01), la cola (RET-03), el proyecto de despliegue anterior (RET-05) y el proveedor de correo (RET-08). Al cerrar el programa, las cuentas de la base, la caché, el almacén y la IA anteriores.
