# Parte del CTO: fichas ortogonales sin cola, 2026-11-14

Parte de relevo del chat del CTO del 2026-11-13 y el 2026-11-14. Sustituye a `2026-11-12_PRD_UNICO.md` como punto de partida. Tema principal: las fichas ortogonales dejan de esperarse unas a otras por Alembic (CI-28 y CI-29). Otros temas: retiro nativo de plataformas (RET), DIAG-07 con su flujo corregido, primera publicación real en Google Cloud y worktrees fuera del escritorio.

**Rol de quien escribe**
- Rol: CTO de EVYDENTIA, asignado por el propietario. Una sesión nueva empieza leyendo este parte y esperando su mensaje.
- Cadena: **CTO** → Arquitecto ADPA → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- Función: decide producto y técnica; envía cada ficha nueva al Arquitecto (y a UX/UI si toca frontend); simula, revisa y fusiona los PR; escribe los briefs que ejecuta el propietario.
- Límites: solo `gcloud` de lectura; no edita `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, `BRIEFS_POR_BLOQUE.md` ni `TASKS.md`; no pasa a listo un PR en borrador sin preguntar; los workflows los fusiona el propietario salvo visto bueno expreso.
- Siempre en español. Los mensajes entre sesiones son de compañeros, no del propietario.

**Estado al corte (2026-11-14, 20:10)**
- `main` en `66492a3d` (#777), **en rojo** en `test_plataforma_unica_sin_incumplimientos_nuevos` (RET-00, R5): #777 y #773 metieron tres archivos de prueba sin la guardia común de base en paralelo con el árbitro. Lo corrige #799. Todos los PR abiertos heredan ese rojo.
- Una sola cabeza de Alembic: `inc02_incidentes_asistente`.
- Fusionados del 13 al 14 de noviembre: 119 PR (del #675 al #797), cada uno simulado sobre el `main` del momento.
- Nube: sirve la revisión `evydentia-backend-00008-pt7` con el 100 % del tráfico y `/health` en 200 con 86 routers. Cloud SQL de producción en `norm02_nota_revision`.

## Lo decidido
- **Fichas ortogonales sin cola (corrección del propietario).** La cola venía de la regla de una sola cabeza de Alembic, no de dependencias reales, y contradice ADPA. Desde ahora cada ficha entra cuando su CI está en verde, sin orden fijo; si aparecen dos cabezas, la que llega segunda se re-cuelga en su sesión sin frenar a las demás. El Tech Lead no propone colas: pasa solo shas listas.
- **Solución de fondo:** CI-28 (una rama de Alembic por sala; orden entre salas solo con dependencia real; árbitro de una cabeza por sala) y CI-29 (el índice de `TASKS.md` se genera en el CI; `BRIEFS_POR_BLOQUE.md` se parte en un archivo por ficha). Las 18 pruebas que exigían una sola cabeza pasan a exigirla por sala, sin cambiar lo que afirman, listadas una por una en el PR.
- **Orden del workflow para CI-28:** primero el parche del propietario (`upgrade head` → `upgrade heads`, #794, fusionado), después CI-28; una prueba lo exige. CI-28 cubre también `backend.Dockerfile`, los scripts de entorno y los briefs (#793). El job `evydentia-migrate` ya ejecuta `upgrade,heads`.
- **Retiro de plataformas, de forma nativa.** `main` es nativo de Google Cloud, como si nunca hubiera usado los proveedores anteriores. Nada de reglas del tipo «prohibido nombrar al proveedor»: eso era un parche. Programa RET-00 a RET-07 bajo SDD (#763). RET-00 es un árbitro estructural por AST con catálogos cerrados que no crecen. El PMV vive solo en `pmv/consolidacion`. El `.env` no existe en la carpeta principal ni lo leen las pruebas.
- **Las especificaciones no nombran al proveedor retirado** (rompe su guardia): pauta para toda especificación futura.
- **DIAG-07, flujo final.** Retiré mi decisión de que el respondiente suba evidencia: contradecía la invariante 59. El DPO sube y vincula la evidencia fuera del formulario de respuestas; quien responde pide la propuesta de la IA (solo si hay evidencia vinculada) y elige el nivel declarado; el DPO verifica, objeta y sella, nunca elige el nivel. El DPO recibe 403 si pide la IA o guarda respuestas. La prueba de punta a punta usa dos usuarios, cada uno con un solo rol.
- **Pruebas ajenas:** el PR las lista con «archivo::prueba | qué comprobaba | qué comprueba | regla que lo exige». Los textos de interfaz deben estar en la especificación o la ficha. Se rechaza cualquier cambio sin regla citada o que debilite la aserción. Los datos de partida se crean por la vía legítima.
- **Precedencia:** INVARIANTS > PRD > especificación > ficha > código. La constitución del proyecto es `PRD_EVYDENTIA_REVENTA_NUBE.md`; en contradicciones con los archivos antiguos mandan los nuevos.
- **Criterio legal en desarrollo:** texto oficial leído de internet (#740, `CITAS_LEGALES_VERIFICADAS.md`); el abogado valida en la fase beta.
- **Decisiones de producto:** RM-26 con `score_objetivo` como lista por dimensión, sin fórmula propia de la sala; RM-27 con hojas anteriores válidas y CHECK NOT VALID; BOV-01 en GB binario con cita oficial y reinicio mensual en ficha propia; ARQ-01 con campo `decidido_por`; GCP-05 partido en GCP-05 y GCP-05b; minScale 0 hasta la beta; GCP-06 «pruebas ahora, producción en beta».
- **Worktrees** solo en `C:\Users\Juan Carlos\worktrees-evydentia\`, nunca `../`; se quitan al fusionar. Se limpiaron las 30 carpetas del escritorio.
- **Cada sesión pone su ficha en «en curso» en el primer commit**; si no, el índice da «crea X, que ya existe».
- **Los PR van en LF**: el CRLF reescribe archivos enteros y dispara «alcance excedido».
- **RET-01a (decisión posterior al corte, 20:20).** R5 de RET-00 exige `exigir_base_de_pruebas()`, que aún no existe (la crea RET-01): ninguna prueba nueva con base puede pasar hasta entonces. Es un fallo de secuencia de RET-00. No se registra deuda nueva como heredada (R7 la pondría en rojo) ni se reescribe la prueba para esquivar el AST. RET-01a, primera pieza de RET-01, crea la función pública en `tests/conftest.py` con la comprobación que ya hace ese archivo, sin cambiar reglas, con su prueba de mutación. Orden por dependencia real: #799 → RET-01a → #788 llama a la guardia en `test_upgrade_heads_local`.

## Lo que falta
**Cómo fusiona el CTO**
1. Worktree desechable desde `origin/main` con merge real (con `--no-commit` da falsos rojos si el PR siembra marcas).
2. Árbitros: `scripts/generar_indice_tareas.py --verificar`, `scripts/verificar_reparto.py`, `scripts/verificar_especificaciones.py`, `python -m alembic heads`, `scripts/verificar_alcance_pr.py --rama R --base origin/main --cabeza REF` y `pytest --noconftest -q -p no:cacheprovider` con `test_sin_neon`, `test_reparto`, `test_indice_tareas`, `test_adpa_bulkhead`, `test_vpa_map`, `test_sin_sql_interpolado`, `test_plataforma_unica` y las pruebas del PR. Las pruebas que necesitan base las decide el CI.
3. `gh pr merge N --merge --match-head-commit <sha completa>`. Los scripts de espera fusionan por orden de llegada y deben re-simular si `main` cambió.

**PR abiertos al corte**

| PR | Ficha | Estado | Qué falta |
|---|---|---|---|
| #799 | RET-00 R7b | CI casi verde (falta Playwright) | Registra en `pendientes/RET-06.txt` la deuda de los tres archivos y añade la regla R7b. **Va primero**: devuelve `main` a verde. |
| #788 | CI-28 | Rojo heredado y R5 propio | Ya incluye #794. Su `test_alembic_cabeza_por_sala.py` usa la base sin guardia: espera a RET-01a. Después, re-simular (antes pasó en verde con 113 pruebas). |
| #787 | CI-29 | Rojo | Algo que RET-00 no admite; se corrige sin ampliar el catálogo. La sesión avisa antes de pedir la fusión, en un hueco sin otros PR de gobernanza. |
| #798 | DIAG-07 | Rojo heredado | Pasa a DIAG-07 las 13 pruebas de preanálisis. |
| #772 | DIAG-07 | Rojo | Palabra no permitida (corregida en local) y las 13 pruebas que entran con #798. IA-04 espera a DIAG-07 (comparten dos archivos); falta la prueba de que el rechazo sin evidencia se debe a esa regla. |

**Fichas y trabajo pendiente**
- RET-01 a RET-07 (RET-01 crea `exigir_base_de_pruebas()`; RET-06 retira las ~190 entradas pendientes; RET-07 quita `enmascarar` y exige motivo propio por dependencia). Dependencias formales RET-01 → SEC-24/GCP-11 y RET-05 → SEC-21.
- Segundo PR de gobernanza del Tech Lead: ARQ-01 a ARQ-03 (TOGAF ligero), ficha del manifiesto `cloudrun_service.yaml` con árbitro contra `deploy-gcp.yml`, regla de «en curso» al lanzar, `huella_registrada`, reinicio mensual de BOV-01 y árbitro de pruebas ajenas.
- INC-03f parada: el backend marca la notificación como pendiente aunque ya haya decisión; lo decide el Arquitecto.
- Cambio sin fusionar de la especificación FOR-01 en `worktrees-evydentia/wt-espec-for01`: lo lleva el Tech Lead.
- SEC-24 R3 pendiente de congelar la referencia en la propia prueba.
- Siguen vigentes del parte anterior: MARCA-01 a 06, PRD-01 a 03, DEMO-05c y 05d, ORG-22 (sección `auditor.py` y prefijo `dlp-discovery`), RM-25b y 25c, REP-01, SEC-25, NORM-02b, IA-06 e IA-08.

## Lo que no se toca
- Producción: ninguna sesión de IA escribe en Google Cloud ni en la base de producción; todo cambio en la nube va por brief que ejecuta el propietario o Antigravity.
- `.github/workflows/`, `verificadores/`, `AGENTS.md` y `.claude/`: del propietario.
- `main` solo recibe EVYDENTIA; el PMV queda en `pmv/consolidacion`.
- `AUTH_MODE=headers` nunca. Sin `.env`. Sin secretos, claves, cadenas de conexión ni endpoints en archivos o en el chat.
- `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead, hasta que CI-29 los retire como archivos compartidos.
- Los catálogos cerrados de RET-00 y la lista de `test_sin_neon` no crecen.
- Un PR fusionado no recibe commits. La inmutabilidad de la biblioteca y la RLS no se relajan.
- No aplicar `cloudrun_service.yaml`: está desfasado (usa `DATABASE_URL` y le faltan secretos).

## Pendientes del usuario
**Decidir o aportar**
- Abogado (fase beta): las 29 interpretaciones, 5 pendientes y 3 estimadas del banco de preguntas, más las del parte anterior (Vertex en us-central1, retención frente a supresión, días hábiles, «Art. 62» de DER-07, nombres del DPO e implementador visibles, plazos antes del WORM).
- Región y encargo de Cloud DLP (el adaptador de DLP-01 sigue apagado).
- Antigravity aprobó sola la compuerta `gcp-produccion` por la API: decidir si eso se permite.

**Ejecutar solo él**
1. Cloud SQL de producción: aplicar TER-01, DLP-01b, BOV-01 e INC-02 con `upgrade heads` antes de la próxima publicación, con respaldo previo y su fila en `REGISTRO_MIGRACIONES_MANUALES.md`.
2. IA-03b: prueba de humo contra Vertex.
3. Secretos: correr `scripts/verificar_secretos_sin_bom.py --version 1`.
4. EP-09, brief IA-03b/IA-11 en el proyecto de pruebas, GCP-06 partes A y B, minScale 1 al entrar en beta.
5. Archivar las ramas `produccion` y `dev/Aleczandra`.
6. Su carpeta: `git pull --ff-only` cuando quiera tener al día los partes.
