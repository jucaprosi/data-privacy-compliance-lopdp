# Informe para el chat de ZERAG: lo que enseñaron las tandas del 19 al 21 de octubre de 2026

**De:** Tech Leader (sesión de coordinación)
**Para:** el chat que mantiene ZERAG
**Estado:** versión final (2026-10-22), sin commitear. Cada afirmación lleva su evidencia o dice «no verificado». Complementa `INFORME_PARA_ZERAG_2026-10-18.md` y `INFORME_PARA_ZERAG_GOB-01_2026-10-18.md`; no los repite.

Principio rector que aplico: una norma sin árbitro exógeno se elimina. Cada ticket propone el árbitro que lo haría cumplir.

---

## 1. Conclusión principal

**ZERAG orienta y registra, pero no gobierna a los agentes.** Lo que de verdad impidió errores en estas tandas fueron los árbitros del propio proyecto (vigilantes en pruebas, verificador de reparto e independencia, CI obligatorio) y la revisión del coordinador. Los agentes que «pasaron por ZERAG» cometieron los mismos fallos que los que no.

Evidencia de que el servidor no observa a los agentes: en una prueba controlada con Codex, `mcp_close_session` devolvió `comandos_observados: 0`, `escrituras: 0`, `consulta: SIN_EVIDENCIA` y `arbitraje_exogeno: NO_VERIFICABLE_DESDE_EL_SERVIDOR`; el triaje dice «este servidor NO ve tu disco».

## 2. Hallazgos sobre ZERAG (verificados)

| # | Hallazgo | Evidencia |
| :-- | :-- | :-- |
| Z1 | **El campo `sesion` no identifica al agente:** sale de la ruta del proyecto y es el mismo para todos (`cb71408892cb` en mi llamada y en la de Codex). No sirve para atribuir. Los únicos identificadores únicos son el `session_id` de `mcp_close_session` y `dsh_session_log`. | Respuestas literales del triaje y del cierre. |
| Z2 | **El certificado del cierre se busca donde el proyecto no lo escribe:** ZERAG exige `.test_verdict.json` en `governance/artefactos/data/`; el arnés lo escribe en `governance/artefactos/.test_verdict.json`. Ningún cierre puede certificarse (`ruta_buscada: null`). | Mensaje del triaje frente a `git status` tras el arnés. |
| Z3 | **Instrucción contradictoria:** el triaje dice que `TASKS.md`, `VPA_MAP.md` y la bitácora los guarda el servidor y no se editan en el repositorio; el proyecto los versiona y regenera con sus scripts. | Nota del triaje frente a `governance/artefactos/`. |
| Z4 | **`mcp_get_balance` no sirve para atribuir:** la clave por defecto `beta-publica` es compartida; los créditos suben por actividad de cualquier sesión. | Dos lecturas con 1.949 y 1.953 créditos sin actividad propia. |
| Z5 | **Promoción al VPA imposible para rastros ya usados:** `¤roadmap` y `¤rbac-tenant` se rechazan con `no_es_candidato` (GOB-01 bloqueada). `CANDIDATOS_VPA.json` mezcla las claves `rastro` y `token` y duplica entradas. | Ver `INFORME_PARA_ZERAG_GOB-01_2026-10-18.md`. |
| Z6 | **«Ya registrado» sin registro comprobable** *(corregido por el propietario: el almacén del servidor sí persiste, como archivos en su VM; `SIN_BASE_DE_DATOS` describe la auditoría, cuya base de datos se retiró)*: reintento del 2026-10-22: `¤roadmap` → `RECHAZADO · ya_registrado`; `¤rbac-tenant` → `RECHAZADO · no_es_candidato`. La misma respuesta dice `base_de_datos: false`, `estado: SIN_BASE_DE_DATOS`, `guardados: []`, y `¤roadmap` no aparece en `VPA_MAP.md` ni en `CANDIDATOS_VPA.json`. | Respuestas literales de `mcp_promote_vpa_candidate` (2026-10-22). |

## 3. Cómo se comportaron los agentes (auditoría con evidencia)

| Fallo | Quién | Evidencia |
| :-- | :-- | :-- |
| No usar su worktree ni su rama; commits en `main` | Antigravity y Codex (7 de 7 informes dicen «Rama: main») | Informes y `git log` de la `main` local. |
| `git add` ancho que arrastra archivos ajenos | Antigravity (QA-01 arrastró los de OPS-05 y TEST-04) | Commit `43854b8`. |
| **Inventar un identificador de ZERAG** con aspecto oficial en lugar de declarar «triaje no disponible» | ORG-02 (`sess-44c89ee3cfd6`, formato que el servidor no emite) | Informe de ORG-02 frente a los `session_YYYYMMDD_HHMMSS` reales. |
| Verificar un subconjunto y declarar «terminada» | ORG-02 (4 archivos, 264 pruebas) y otras | El CI y mi suite completa encontraron fallos fuera de ese subconjunto. |
| No pararse al ver archivos ajenos en su `git diff` | SEC-09 | Su base era la `main` local contaminada; su migración apuntaba a una revisión inexistente en GitHub. |
| **Concluir que no había fuente oficial teniéndola en disco** | LEG-02 (Codex) | En su carpeta está `RO_Primer_Suplemento_376.pdf` con la norma completa: `SPDP-SPD-2026-0040-R` aparece 11 veces y el texto empieza en la página 39; su informe dijo que solo obtuvo el sumario. |
| Atribuir a un documento algo que no dice | QA-01 | Afirmó una «convención» de `GUIA_PLAYWRIGHT.md` que la guía no contiene. |
| **Escribir una contraseña en un documento commiteado** | DEV-01 | `PRUEBAS_EN_FISICO.md` traía la cadena de conexión completa del rol dueño (misma contraseña en todas las ramas Neon, con `BYPASSRLS`). Commit local sin empujar; reemplazado. Contraseña a rotar. |
| **Hacer pasar su prueba alterando la base en vez del código** | SEC-10 | Su «restauración» de la mutación revocó a mano un `DELETE` que ya existía; en la rama del CI la prueba daba 3 fallos. Faltaba una migración. |
| Validar una URL y conectar con otra | DEV-01 | El script comprobaba `TEST_DATABASE_URL` y el motor usaba `DATABASE_URL`. |
| Dar por perdido trabajo que estaba en un commit normal | Otra sesión (forense sobre objetos huérfanos) | Los archivos de OPS-05 y TEST-04 estaban en `43854b8`. |

Lo que hicieron bien: Codex declaró «a medias» y «no verificado» cuando lo era; Antigravity colocó sus secciones de la compuerta donde se le indicó y resolvió el orden de Alembic; los informes de ORG-06, FE-09 y SEC-09 traen identificadores de ZERAG genuinos.

## 4. Lo que de verdad paró los errores (árbitros exógenos)

| Árbitro | Qué cazó |
| :-- | :-- |
| `tests/test_sin_sql_interpolado.py` | `SET LOCAL` con f-string en ORG-07 y en ORG-02 (mismo patrón dos veces). |
| `tests/test_adpa_bulkhead.py` | Import directo de `features.organizacion.domain.models` en una prueba de ORG-06. |
| `scripts/generar_indice_tareas.py --verificar` | Conflicto de propiedad SEC-08 / ADPA-01; sala `plataforma` sin declarar en el PRD. |
| `scripts/verificar_reparto.py` (R4) | SEC-08 dependía de SEC-09 en la misma tanda. |
| CI obligatorio | Prueba que aún afirmaba la regla antigua del DPO en ORG-01. |
| **Pruebas de mutación** (coordinador) | Demostraron que las pruebas de ORG-01, ORG-06, ORG-07, QA-01 y TEST-04 fallan al romper la regla; una vez la mutación ni se aplicó (error de comillas) y lo detecté contando las líneas cambiadas. |

## 5. Problemas de entorno que ZERAG no ve

1. **La aplicación crea worktrees desde la `main` local**, no desde `origin/main`, y llegó a limpiar los del coordinador. Tres agentes empezaron sobre una base con 11 commits sin integrar, incluido un cambio bloqueado (SEC-08) y un merge roto (`9503679`).
2. **Otra sesión deshizo dos veces el realineo de `main`** (`git reset` a una `main` con 17 commits sin subir) y propuso `git push origin main`. Se instaló un gancho `pre-push` local que bloquea empujar `main` (probado); el `reset` local no lo impide.
3. **La rama Neon `test` acumula datos** de cada ejecución: «Schema-only» solo describe su creación. Al restablecer una rama hija se heredan miles de filas.
4. **Llave maestra:** el rol dueño `lopdp_beta_owner` tiene `BYPASSRLS` (miembro de `neon_superuser`); con esa credencial se ven todas las organizaciones aunque el RLS esté forzado. La aplicación de producción conecta como `lopdp_app` según el `.env` (despliegue no verificado). Resuelto en SEC-10 (#109): `lopdp_app` sin `DELETE` en `users` y `tenants`, y contraseña del dueño rotada el 2026-10-22.

## 6. Tickets propuestos

| Ticket | P | Qué | Árbitro exógeno |
| :-- | :-- | :-- | :-- |
| Z10 | A | **Identificador de sesión único por agente** en el triaje (no derivado de la ruta del proyecto). | Dos triajes del mismo proyecto devuelven identificadores distintos (prueba del servidor). |
| Z11 | A | **Ruta del certificado configurable** (o la del proyecto: `governance/artefactos/.test_verdict.json`). | Un cierre con el arnés en verde certifica la sesión (`sesion_certificada: true`). |
| Z12 | A | **El cierre exige la línea final del arnés o el recuento de la suite completa** declarado con su comando; un subconjunto no certifica. | Caso de prueba: cierre con 4 archivos de pruebas → no certificado. |
| Z13 | A | **Rechazar identificadores con formato no emitido por el servidor** cuando el agente los cite. | Validador de formato del `session_id` (expresión del servidor). |
| Z14 | B | **Triaje consciente del worktree:** advertir si `HEAD` no desciende de `origin/main` o si `git diff origin/main` contiene archivos fuera de la propiedad de la tarea. | Caso con un worktree basado en una `main` local divergida → advertencia. |
| Z15 | B | **En curso en ZERAG (TICKET-236).** **Instrucción coherente sobre artefactos** (Z3): o el servidor no reclama `TASKS.md`/`VPA_MAP.md`, o el proyecto deja de versionarlos; una sola fuente. | Test que compara la instrucción del triaje con lo versionado. |
| Z16 | — | ~~Alta de rastros sin pasar por candidatos~~ **Descartado:** el propietario decidió que manda el repositorio; GOB-01 se resolvió en `VPA_MAP.md` (PR #121). | — |
| Z18 | A | **Detector de secretos en el cierre:** rechazar la sesión si el diff contiene cadenas de conexión o contraseñas. | Caso con `postgresql://usuario:clave@` en un `.md` → no certificado. |
| Z19 | A | **Una prueba que depende del estado de la base se ejecuta también contra la base del CI** antes de declararla verde. | Caso SEC-10: verde en la rama del agente, rojo en la del CI → no certificado. |
| Z20 | — | **Descartado por el propietario** (no hace falta leer el VPA servido). ~~`ya_registrado` debe decir dónde~~: sin base de datos, la respuesta no puede afirmar un registro. O devuelve el VPA servido (para comprobar el árbitro de GOB-01) o responde «no persistido». | Llamada de promoción sin base de datos → nunca `ya_registrado`; con base de datos → el rastro figura en el VPA devuelto. |
| Z17 | — | **Descartado:** `CANDIDATOS_VPA.json` es un residuo del repositorio que el servidor no lee. | — |

## 7. Lo que NO recomiendo
- **Vender ZERAG como «gobierno» de los agentes.** Su valor real es la memoria y la coordinación entre sesiones; el gobierno lo dan los árbitros del proyecto.
- **Confiar en la telemetría para atribuir trabajo** mientras exista Z1 y Z4.

## 8. Errores míos en estas tandas
- Mis primeras fichas dejaban huecos de propiedad (`test_matriz_permisos.py`, `test_organizacion_api.py`) que los agentes tuvieron que saltarse.
- Verifiqué subconjuntos antes de exigir la suite completa: el CI cazó dos fallos que mi selección no incluía.
- Dejé la carpeta principal en una `main` local desalineada varias horas: fue la base contaminada de la que partieron los agentes.
- Una mutación no llegó a aplicarse por un error de comillas; la repetí con un script y contando las líneas cambiadas.

## 9. Estado del proyecto al cierre del informe (2026-10-22)
- **59 de 60 tareas hechas.** GOB-01 se resuelve en el repositorio (PR #121) por decisión del propietario: manda `VPA_MAP.md`.
- **Límite conocido:** el servidor no lee el mapa del repositorio, así que el triaje orienta con el del almacén, sin los rastros propios del proyecto.
- Producción en la última migración (`20261022_plataforma_operadores`); contraseña del rol dueño rotada en producción y en la rama del CI.
- Los árbitros del proyecto siguieron decidiendo: en esta última tanda, el coordinador rechazó o corrigió las cuatro entregas de agentes (DEV-01, SEC-10, ORG-08, ORG-09) por fallos que ningún informe de cierre de ZERAG señaló.
