# Programa RET: mapa de eliminación por ficha
`¤sdd`

Arquitecto ADPA, 2026-11-14. Las plataformas que Google Cloud reemplazó se eliminan del repositorio como si nunca se hubiera trabajado con ellas. Ninguna regla, invariante ni árbitro las nombra o las prohíbe. Cada PR de eliminación tiene como árbitro la suite existente en verde. La historia queda en git.

Medido en `origin/main` b216ab4e:
- 137 archivos fuera de `governance/` nombran las plataformas;
- unos 220 dentro de `governance/`;
- ninguno en `.github/`, `scripts/` ni `.githooks/`.

## 1. Mapa

| Ficha | Qué elimina | Brief al propietario |
| :--- | :--- | :--- |
| **RET-00** | Las pruebas que vigilaban plataformas: `tests/plataforma_unica/` y `test_plataforma_unica.py`, la carpeta de la guardia de huellas y su prueba, `test_ci17_…`, `test_vercel_despliegue.py` y `verificadores/`. Va primero. | no |
| **RET-01a** (#809) | La carga de archivos de entorno en `tests/conftest.py` y la guardia antigua de la suite. Deja `exigir_base_de_pruebas()` con la lista blanca local. | no |
| **RET-01** | La carga de archivos de entorno en `app_core/config.py`, `python-dotenv`, `.env.example` y las variables de las plataformas en `huellas_produccion.py`, `cloud/gcp_runtime.py` y las guardias de arranque. Sus pruebas: `test_sec15/16/17/20`, `test_ep01`, `test_ep05`, `test_demo_purga`, `test_conftest_entorno` y `test_base_por_trabajador`. | sí: borrar los secretos de las plataformas en Secret Manager y en GitHub |
| **RET-02** | `app_core/storage/` del almacén anterior (el adaptador queda en Cloud Storage) y sus paquetes. En el frontend: `EvidenciaPanel.tsx`, `subirEvidencia.ts`, `HarnessEvidencia.tsx`, `useRoadmapStore.ts`, `types/roadmap.ts`, `generar_tipos.js`, `cliente.mock.test.ts`, los e2e de `criterio12`, `next.config.ts` y `features/roadmap/domain/models.py`. La columna `r2_key` se renombra a `clave_objeto` con una migración nueva, `ret02_clave_objeto.py`. | no |
| **RET-03** | `app_core/queue/`, el paquete de la cola y `test_redis_client.py`. | sí, solo si se usa Cloud Tasks: crear la cola |
| **RET-04** (nueva) | `app_core/ai/` (cliente anterior), `assistant_provider.py`, `preanalisis/services/proveedor.py`, `roadmap/ai/client.py`, sus variables y sus pruebas (`test_ai_copilot_motivo_neutro`, `test_preanalisis`, `test_preanalisis_motivo_neutro`, `test_ia07_asistente_inferencia`). | no |
| **RET-05** | `vercel.json`, `frontend/vercel.json` y las ramas de entrada anteriores en `security.py`, `bucle_eventos.py`, `firma_anf.py` y `modo.ts`. También `frontend/.dockerignore`, `frontend/README.md` y `cabeceras.spec.ts`, y los archivos de bloqueo regenerados. Si conviven dos archivos de bloqueo, uno se elimina. | sí: borrar el proyecto de la plataforma de despliegue anterior |
| **RET-06** | Las pruebas que comprueban la base por su cuenta pasan a `exigir_base_de_pruebas()`. Las que llevan fixtures o comentarios de la base anterior se limpian: `test_bib117`, `test_bib_203/205/206/207`, `test_diagnostico_respuestas`, `test_diag12_estados`, los dos e2e, `test_evidencia_*`, `test_org_14`, `test_organizacion_*`, `test_rat_plantilla_salud`, `test_roadmap_control_ref`, `exportacion_engine.py` y `duraciones.json`. Si una mención es de almacén, cola o IA, va a RET-02, RET-03 o RET-04. | no |
| **RET-08** (nueva) | El boceto del proveedor de correo anterior en `features/notificaciones/` y `test_notificaciones.py`. Queda el puerto con el doble de pruebas. | sí: elegir el proveedor (§3) |
| **RET-09** (nueva) | Documentación (§2). | no |
| **RET-10** (nueva) | Los comentarios de las migraciones aplicadas (§4). | no |

RET-07 no existe: ya no hay árbitro de menciones que retirar.

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

1. **RET-00 y RET-01a.** Sin las pruebas que vigilaban plataformas, las demás fichas solo borran código.
2. **En paralelo,** porque no comparten archivos: RET-01, RET-02, RET-03, RET-04, RET-05, RET-06, RET-08 y RET-10.
3. **RET-09,** al final, porque sus fichas y briefs citan las anteriores.
4. **Briefs al propietario,** cada uno después de su ficha: los secretos (RET-01), la cola (RET-03), el proyecto de despliegue anterior (RET-05) y el proveedor de correo (RET-08). Al cerrar el programa, las cuentas de la base, la caché, el almacén y la IA anteriores.
