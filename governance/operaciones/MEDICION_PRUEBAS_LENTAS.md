# Medición de las pruebas lentas contra Neon
`¤ci-cd` `¤arbitro`

> Estado al 2026-11-02: **medición incompleta**. Falta la corrida con `--durations` contra Neon, que separa preparación, llamada y limpieza. Las decisiones de la sección 4 son provisionales y la ficha `CI-08` no se cierra hasta tener esa corrida.

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

## 4. Decisión por archivo (provisional)

Neon es el tiempo por archivo en la corrida lenta (41479331361) y en la rápida (41446452507), deducido de las marcas de tiempo del registro `-v`. Local es la separación medida con PostgreSQL local. Sirve de indicio y no sustituye a la de Neon: allí pesa la latencia de red, y aquí no.

| Archivo | Pruebas | Neon lenta (s) | Neon rápida (s) | Local: preparación / llamada / limpieza (s) | % fixture local | Decisión provisional |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- |
| `test_roadmap_hallazgos` | 33 | 131 | 24 | 2,3 / 5,7 / 4,4 | 54 | Separar lo que no escribe del `ctx` que crea 2 organizaciones y 5 usuarios por prueba. |
| `test_diagnostico_resultados` | 20 | 116 | 23 | 4,9 / 1,0 / 4,2 | 90 | Ficha: compartir el `ctx` entre las pruebas que solo leen. |
| `test_dpo_bitacora` | 15 | 100 | 18 | 2,3 / 1,0 / 4,4 | 87 | Ficha: revisar la limpieza, que pesa el doble que la preparación. |
| `test_organizaciones_por_persona` | 15 | 87 | 17 | 4,0 / 0,7 / 3,7 | 92 | Ficha: fixture por módulo si las pruebas no se pisan. |
| `test_controles_periodicos` | 18 | 76 | 15 | 1,3 / 1,0 / 1,3 | 72 | Esperar a la medición con Neon. |
| `test_incidentes` | 13 | 67 | 13 | 1,8 / 0,5 / 3,1 | 91 | Ficha: revisar la limpieza. |
| `test_rat_persistencia` | 9 | 68 | 13 | 1,3 / 1,1 / 1,8 | 74 | Esperar a la medición con Neon. |
| `test_responsable_requests` | 26 | 65 | 12 | 5,0 / 1,5 / 0,0 | 77 | Ficha: la preparación se repite 26 veces. |
| `test_capa_persistencia` | 6 | 52 | 10 | 0,7 / 0,5 / 1,3 | 80 | Esperar a la medición con Neon. |
| `test_rat_eipd` | 7 | 51 | 10 | 0,8 / 0,9 / 1,6 | 73 | Esperar a la medición con Neon. |

Ninguna decisión aplica `rollback` a toda la suite ni adopta `pytest-split`. Cada ficha debe comprobar el aislamiento de su archivo antes de compartir un fixture.

## 5. Fichas propuestas

No se corrige nada en `CI-08`. El coordinador decide cuáles abrir.

1. **Causa de la variación de cinco veces en Neon.** Es la de mayor efecto: pasar de 36 a 7 minutos no exige tocar ninguna prueba. Consultar el cómputo de la rama de pruebas y la región durante una corrida lenta y una rápida.
2. **Fixtures de `test_diagnostico_resultados`, `test_organizaciones_por_persona` y `test_responsable_requests`.**
3. **Limpieza de `test_dpo_bitacora` y `test_incidentes`.**
4. **Reparto de `test_roadmap_hallazgos`.**
5. **`test_hook_pre_push.py`.** Fija el piso del arnés local: 51,7 s de unos 75 s.
6. **Cierre nativo de un `pytest` hijo.** En una corrida local, sin orden por duración, `test_conftest_guardias.py::test_database_url_de_produccion_sin_url_de_pruebas_tambien_se_detiene` falló porque el proceso hijo terminó con `0xC0000409` en Windows. Ocurrió una vez en siete corridas y no se investigó la causa.

## 6. Lo que falta

Una corrida en serie contra una rama Neon de desarrollo propia, nunca `ep-late-hall`, con `pytest tests/ --durations=0 -vv`. Requiere un `.env` de esa rama en el worktree. Con su resultado se confirma o cambia cada decisión de la sección 4.
