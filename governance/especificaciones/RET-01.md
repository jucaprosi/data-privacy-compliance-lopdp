# RET-01 · Configuración solo por variables de entorno y guardia de base local
`¤sdd` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Cambia de dónde sale la configuración:

- `app_core/config.py` deja de leer el archivo `.env`: sin `load_dotenv` y sin `env_file`. Solo lee variables del proceso.
- `python-dotenv` sale de `requirements.txt`. `.env.example` se retira.
- `governance/operaciones/ENTORNO_LOCAL.md` lista cada variable, y `scripts/entorno_local.ps1` las fija en la ventana de PowerShell. El script no contiene secretos ni URLs reales: pide los valores o usa los del arnés local.
- `app_core/huellas_produccion.py`: `VARIABLES_DE_NUBE = ("K_SERVICE",)`. Se retira `HUELLA_HOST_PRODUCCION` (la de la base gestionada del PMV). La huella de Cloud SQL de producción (SEC-20) se queda.

## 2. API

No aplica: no hay rutas HTTP nuevas. El arranque de la API conserva `exigir_arranque_seguro` (SEC-15).

## 3. Reglas

- **R1 · Un `.env` se ignora.** Aunque exista un `.env` en la carpeta, ni la aplicación, ni la suite, ni Alembic, ni el hook, ni los scripts lo leen.
- **R2 · Guardia de base local (lista de permitidos, no de prohibidos).** La suite de pruebas y el modo `headers` solo arrancan si el host de cada variable de base (`DATABASE_URL`, `MIGRATION_DATABASE_URL`, `DATABASE_URL_DIRECT`) es `localhost`, `127.0.0.1`, `::1` o el servicio de base del CI. Cualquier otro host detiene el arranque con un error que nombra la regla y la variable, nunca la URL.
  - **`/cloudsql/` no cuenta como local.** El programa lo propone como «del contenedor del arnés», pero ese es el camino del socket con el que Cloud Run se conecta a Cloud SQL, incluida la de producción. Queda fuera de la lista hasta que el CTO lo decida. Si el arnés lo necesita, se añade con una condición que excluya `K_SERVICE` y la huella de SEC-20.
- **R3 · La misma regla en todos los puntos de entrada.** `tests/conftest.py`, `alembic/env.py`, `.githooks/pre-push`, `scripts/arnes_local.py`, `app_core/entorno/guardias.py` y los scripts que hoy importan `huellas_produccion` usan una sola función de `app_core`. Ninguno reimplementa la comprobación.
- **R4 · Invariantes que no se debilitan.** SEC-15 (`HEADERS_NEVER_WITH_PRODUCTION`), SEC-16 (`NO_DEFAULT_SECRETS_IN_CLOUD`) y SEC-20 siguen verdes. Si un cambio choca con uno de ellos, la ficha se detiene y lo informa.
- **R5 · `conftest` no exige `.env`.** Sin variables de base, las pruebas que la necesitan se omiten con un motivo visible; no fallan ni buscan un archivo.
- **R6 · Sin secretos por defecto.** Ninguna variable gana un valor por defecto que sirva en la nube.
- **R-ADPA · Ortogonalidad ZERAG (`RET-01`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica: no hay pantalla. La interfaz de quien desarrolla es `scripts/entorno_local.ps1`, documentado en `ENTORNO_LOCAL.md` con comandos pegables.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un `.env` en la carpeta con una URL de producción, **cuando** se carga la configuración, **entonces** se ignora y los valores salen solo del proceso. Mutación: restaurar `load_dotenv` hace fallar la prueba. | `test_env_en_carpeta_se_ignora` |
| **Dado** `DATABASE_URL` con un host remoto, **cuando** arranca la suite, **entonces** se detiene y el mensaje nombra la regla y la variable, sin la URL. Mutación: aceptar cualquier host hace fallar la prueba. | `test_suite_solo_con_base_local` |
| **Dado** una URL con socket `/cloudsql/`, **entonces** no se trata como local. | `test_cloudsql_no_es_local` |
| **Dado** el modo `headers` con `K_SERVICE` definido o una base no local, **entonces** el arranque falla (SEC-15). `VERCEL` ya no se consulta. | `test_sec15_guarda_arranque` |
| **Dado** el hook `pre-push`, `alembic/env.py` y `arnes_local.py`, **entonces** los tres aplican la misma guardia y ninguno importa `dotenv`. | `test_puntos_de_entrada_misma_guardia` |
| **Dado** `requirements.txt` y el árbol, **entonces** no aparece `dotenv` fuera de la historia. | `test_sin_dotenv` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-01.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763, 39dbf4b5), decisiones del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. La historia del PMV la retira RET-07. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Sustituye, solo para `main`, dos acuerdos del 2026-11-09: la huella de la base gestionada del PMV y la carga del `.env`.
- Invariantes: SEC-15, SEC-16 y SEC-20. Depende de RET-00.
