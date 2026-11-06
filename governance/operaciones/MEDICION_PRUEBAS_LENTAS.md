# Medición de las pruebas lentas contra Neon
`¤ci-cd` `¤arbitro`

> Estado al 2026-11-02: **medición completa**. La sección 4 trae la corrida con `--durations` contra Neon, que separa preparación, llamada y limpieza, y una decisión por cada uno de los 10 archivos más lentos. Las correcciones se proponen como fichas.

---

## 1. La condición de la ficha se cumple

Duración del paso `Backend Pytest (E2E y Unitarias)` en las corridas verdes recientes del Arnés completo hacia `main`, con 1 487 a 1 706 pruebas contadas en el registro:

| Corrida | Fecha (UTC) | Pytest (min) |
| :--- | :--- | ---: |
| 41479331361 | 2026-11-02 | 35,9 |
| 41446452507 | 2026-11-02 | 7,1 |
| 41350268991 | 2026-11-01 | 10,9 |
| 41303828615 | 2026-11-01 | 28,4 |
| 41237785238 | 2026-10-31 | 25,8 |

Son 36 minutos en la corrida más reciente, en un flujo obligatorio hacia `main`. Sigue siendo un problema.

## 2. El hallazgo principal: todo se multiplica por cinco

Las mismas pruebas tardan cinco veces más en unas corridas que en otras, y la razón es casi igual en todos los archivos: entre 4,9 y 5,5 en los diez más lentos, comparando 35,9 min con 7,1 min. Ningún archivo explica esa diferencia, porque la suite entera se desplaza.

Además, el tiempo está repartido: 128 archivos, y los diez más lentos suman entre el 37 % y el 51 %. El mayor no pasa de 131 s en 36 minutos.

Por eso, la palanca grande no es un archivo sino lo que cambia entre corridas. Candidatos sin comprobar: el tamaño de cómputo de la rama de Neon en ese momento, y la ubicación del ejecutor de GitHub frente a la región de Neon. Los datos de esta medición no distinguen entre ellos.

## 3. Qué hace y qué no hace el orden por duración

`tests/duraciones.json` ordena los archivos de más lento a más rápido en los trabajadores de xdist.

- **No acorta Neon.** Esa corrida es en serie y `tests/conftest.py` prohíbe `-n` sobre Neon: el orden no cambia una suma. Tampoco se aplica en serie.
- **Hoy solo actúa en `verificadores/arnes_local.py`.** El CI corre `pytest tests/ -v` sin `-n`, también en las ramas.
- **Efecto medido en el arnés local**, 12 trabajadores, corridas alternadas: sin orden 84,9 s y 77,2 s; con orden 73,8 s, 82,0 s y 74,6 s. La mejora es pequeña y queda dentro del ruido de la máquina. La simulación del reparto con las duraciones medidas da 60,4 s con el orden de xdist y 51,7 s por duración, que es el piso: `test_hook_pre_push.py` solo ya tarda 51,7 s.
- **Mismas pruebas.** Las corridas previa y posterior ejecutan los mismos identificadores más las 9 nuevas de `tests/test_orden_por_duracion.py`; 1 787 pasadas y 22 omitidas.

Con `--dist loadfile`, xdist reordena por número de pruebas e ignora el orden de la colección. `tests/conftest.py` lo desactiva solo si existe el archivo de duraciones; sin esa línea el gancho no tiene efecto, y lo vigila una prueba con xdist real.

**Regenerar cada mes**, desde una corrida completa con PostgreSQL local:

```powershell
pytest tests/ -n auto --dist loadfile --durations=0 -vv > salida.txt
python tests/orden_por_duracion.py salida.txt
```

## 4. Medición contra Neon y decisión por archivo

**Cómo se midió.** Pytest en serie con `--durations=0 -vv` contra la rama de desarrollo `test-juan-carlos-ci08`, migrada a la cabeza de Alembic, desde el equipo de desarrollo. El 2026-11-02 el worktree se retiró a mitad de la corrida, y 27 archivos dieron 122 fallos y errores por archivos ausentes. Esos 27 se repitieron completos en otro worktree: 311 pasadas y ninguna falla. Las cifras de esos archivos salen de la repetición; las de los otros 104, de la primera corrida.

**Total de los 131 archivos: 68,3 min.** Preparación 27,2 min (40 %), llamada 29,9 min (44 %), limpieza 11,2 min (16 %). Las cifras absolutas no se comparan con el CI, que tardó de 7 a 36 min desde otra red: valen las proporciones. Los 10 archivos más lentos suman el 42,7 %.

| Archivo | Pruebas | Total (s) | Preparación / llamada / limpieza (s) | % fixture | Decisión |
| :--- | ---: | ---: | :--- | ---: | :--- |
| `test_diagnostico_resultados` | 20 | 237 | 111,7 / 72,8 / 52,2 | 69 | Ficha: compartir `ctx` entre las pruebas que no escriben. |
| `test_roadmap_hallazgos` | 33 | 234 | 74,2 / 120,4 / 39,7 | 49 | Ficha: la llamada pesa más; 7 pruebas superan 10 s, entre ellas 3 de un mismo parametrize por rol. |
| `test_dpo_bitacora` | 15 | 182 | 87,3 / 56,4 / 37,8 | 69 | Ficha: reducir la preparación de `dpo_env`. |
| `test_rat_validaciones` | 13 | 179 | 61,8 / 83,8 / 33,9 | 53 | Ficha: `test_ficha_ajena_no_encontrada_y_permisos` tarda 32,5 s, el 18 % del archivo. |
| `test_rat_exportacion` | 18 | 166 | 70,3 / 59,3 / 36,8 | 64 | Ficha conjunta de los fixtures de RAT. |
| `test_roadmap_cierre_recordatorios` | 20 | 162 | 58,4 / 68,0 / 35,8 | 58 | Sin ficha por ahora: reparto parejo y una sola prueba de 13,8 s. |
| `test_organizaciones_por_persona` | 15 | 160 | 53,6 / 66,6 / 39,9 | 58 | Sin ficha por ahora: reparto parejo. |
| `test_controles_periodicos` | 18 | 149 | 47,7 / 75,0 / 25,9 | 50 | Ficha: `test_responsable_y_roles` tarda 14,5 s. |
| `test_dpo_informe_anual` | 11 | 147 | 92,3 / 38,9 / 16,1 | 74 | Ficha: es el mayor peso de preparación de los diez. |
| `test_rat_persistencia` | 9 | 132 | 48,6 / 57,7 / 25,5 | 56 | Ficha conjunta de los fixtures de RAT. |

Ninguna decisión aplica `rollback` a toda la suite ni adopta `pytest-split`. El reparto no da motivo para ninguna de las dos cosas. Cada ficha debe comprobar el aislamiento de su archivo antes de compartir un fixture.

**Correcciones a la versión provisional:**

- **Cambia la lista.** Entran `test_rat_validaciones`, `test_rat_exportacion`, `test_roadmap_cierre_recordatorios` y `test_dpo_informe_anual`. Salen `test_incidentes` (127 s), `test_responsable_requests` (118 s), `test_rat_eipd` (98 s) y `test_capa_persistencia` (96 s).
- **La llamada pesa más de lo que indicaba PostgreSQL local.** Allí los fixtures eran entre el 54 % y el 92 %; en Neon, entre el 49 % y el 74 %. Con latencia real, compartir fixtures ahorra menos de lo estimado.
- **Se retira la decisión sobre la limpieza de `test_dpo_bitacora`.** Local la mostraba como el doble de la preparación; en Neon es menos de la mitad. Tampoco procede la ficha de limpieza de `test_incidentes`, donde la preparación es 3,3 veces la limpieza.
- **Se retiran las fichas de `test_responsable_requests` y `test_organizaciones_por_persona`.** El primero salió de la lista y el segundo tiene un reparto parejo.

## 5. Fichas propuestas

No se corrige nada en `CI-08`. El coordinador decide cuáles abrir.

1. **Causa de la variación de cinco veces en Neon.** Sigue siendo la de mayor efecto: los diez archivos juntos pesan el 42,7 %, y una mejora en ellos no alcanza a la variación entre corridas. Consultar el cómputo de la rama de pruebas y la región durante una corrida lenta y una rápida.
2. **Preparación de `test_diagnostico_resultados`, `test_dpo_bitacora` y `test_dpo_informe_anual`.** Suman 291 s de preparación.
3. **Fixtures de RAT: `test_rat_exportacion` y `test_rat_persistencia`.**
4. **Llamadas caras:** `test_roadmap_hallazgos`, `test_ficha_ajena_no_encontrada_y_permisos` y `test_responsable_y_roles`. Averiguar cuántas consultas hace cada una antes de cambiar nada.
5. **`test_hook_pre_push.py`.** Fija el piso del arnés local: 51,7 s de unos 75 s.
6. **Cierre nativo de un `pytest` hijo.** En una corrida local, sin orden por duración, `test_conftest_guardias.py::test_database_url_de_produccion_sin_url_de_pruebas_tambien_se_detiene` falló porque el proceso hijo terminó con `0xC0000409` en Windows. Ocurrió una vez en ocho corridas y no se investigó la causa.

## 6. Límites de esta medición

- La corrida salió del equipo de desarrollo y no del ejecutor de GitHub, con una latencia distinta. No explica la variación de la sección 2.
- No es una sola corrida continua: 27 archivos se midieron en la repetición.
- `--durations` no separa el tiempo de red del de la base.
- No se contaron consultas por prueba. Las decisiones de la sección 4 salen de tiempos, y la ficha 4 debe medir esa causa.
