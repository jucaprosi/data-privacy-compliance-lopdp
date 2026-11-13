# Consultas por prueba
`¤ci-cd` `¤arbitro`

> Medido el 2026-11-02 contra PostgreSQL local, con la suite completa en serie: 1 841 pasadas y 22 omitidas. **Las consultas sí explican la diferencia entre regiones:** salen unos 60 ms por viaje, una cifra posible y casi igual en los diez archivos. No se implementa ningún cambio aquí.

---

## 1. Cuánto se habla con la base

| Medida en toda la suite | Cantidad |
| :--- | ---: |
| Pruebas | 1 863 |
| Pruebas que llegan a la base | 490 (26 %) |
| Sentencias | 19 551 |
| Sentencias en preparación y limpieza | 10 367 (53 %) |
| Conexiones abiertas | 498 |
| Checkouts del pool | 1 978 |
| BEGIN | 1 978 |
| COMMIT | 1 403 |
| ROLLBACK | 575 |
| **Viajes sin contar el saludo de cada conexión** | **25 485** |

Una prueba que llega a la base envía una mediana de 29,5 sentencias y abre una conexión propia. `before_cursor_execute` no ve BEGIN, COMMIT, ROLLBACK, el `pool_pre_ping` ni la apertura de conexiones: son 5 934 viajes más, el 23 % del total. Se cuentan aparte para que la latencia implícita no salga inflada.

## 2. Los 10 archivos más lentos

Son los de `MEDICION_PRUEBAS_LENTAS.md`.

| Archivo | Pruebas | Consultas | Mediana por prueba | Máximo | % en fixtures | Conexiones | Viajes sin saludo |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `test_roadmap_hallazgos` | 33 | 1424 | 0 | 138 | 48 | 14 | 1769 |
| `test_diagnostico_resultados` | 20 | 1281 | 63 | 108 | 70 | 18 | 1533 |
| `test_dpo_bitacora` | 15 | 1001 | 63 | 90 | 70 | 15 | 1214 |
| `test_rat_validaciones` | 13 | 994 | 66 | 220 | 53 | 11 | 1216 |
| `test_rat_exportacion` | 18 | 963 | 67 | 118 | 62 | 13 | 1155 |
| `test_roadmap_cierre_recordatorios` | 20 | 925 | 68.5 | 119 | 60 | 12 | 1183 |
| `test_controles_periodicos` | 18 | 849 | 0 | 134 | 50 | 8 | 1056 |
| `test_organizaciones_por_persona` | 15 | 841 | 56 | 71 | 60 | 15 | 1072 |
| `test_dpo_informe_anual` | 11 | 821 | 111 | 177 | 75 | 6 | 1118 |
| `test_rat_persistencia` | 9 | 747 | 77 | 118 | 55 | 9 | 927 |

La mediana de 0 en `test_roadmap_hallazgos` y `test_controles_periodicos` se debe a que más de la mitad de sus pruebas no tocan la base; las que sí la tocan se llevan todo.

**Lo que no se ve:** ningún archivo de prueba usa `psycopg.connect`. Tampoco se ven las consultas de los subprocesos.

## 3. Comprobación de coherencia

Se comparan dos corridas del informe de variación del arnés (histórico del PMV, en `governance/historico/pmv/`): 41479331361 en `westus` y 41446452507 en `northcentralus`. Se divide la diferencia de segundos de cada archivo entre sus viajes medidos.

| Archivo | Diferencia (s) | Viajes | Latencia implícita (ms) |
| :--- | ---: | ---: | ---: |
| `test_roadmap_hallazgos` | 107 | 1769 | 60,5 |
| `test_diagnostico_resultados` | 94 | 1533 | 61,1 |
| `test_rat_exportacion` | 89 | 1155 | 77,1 |
| `test_dpo_bitacora` | 82 | 1214 | 67,6 |
| `test_rat_validaciones` | 75 | 1216 | 61,8 |
| `test_organizaciones_por_persona` | 70 | 1072 | 65,4 |
| `test_roadmap_cierre_recordatorios` | 68 | 1183 | 57,9 |
| `test_dpo_informe_anual` | 68 | 1118 | 61,2 |
| `test_controles_periodicos` | 61 | 1056 | 58,1 |
| `test_rat_persistencia` | 55 | 927 | 59,1 |
| **Toda la suite** | **1 638** | **24 286** | **67,4** |

- **La latencia no sale imposible.** Son 58 a 77 ms por viaje, lejos de los «unos cientos de ms» que invalidarían la explicación.
- **Es casi la misma en archivos muy distintos**, que es lo que se espera de un coste fijo por viaje.
- **Control:** los 75 archivos sin ninguna consulta suman −1 s de diferencia. La distancia solo cuesta donde hay viajes.
- **El saludo de cada conexión cambia poco.** Si cada conexión costara 6 viajes, saldrían 60,3 ms; con 10, 56,4 ms. Ese número de viajes es un supuesto.

**Límites.** Es la diferencia entre `westus` y `northcentralus`, no la latencia absoluta hasta la base remota del PMV, que sigue sin medirse. Las dos corridas tienen menos pruebas que la suite de hoy (1 706 y 1 667 frente a 1 863), y eso baja algo la cifra. El número de viajes viene de PostgreSQL local; se asume igual en la base remota, aunque el pooler u otros datos podrían cambiarlo. Un checkout se cuenta como un viaje por `pool_pre_ping`, sin haberlo capturado en la red.

**Cómo se usa la cifra:** con 60 ms de diferencia, cada 1 000 viajes menos ahorran unos 60 s en el oeste y casi nada en las regiones cercanas.

## 4. Cambios propuestos

Ordenados por ahorro y riesgo para el aislamiento. Las cifras marcadas como *techo* son un máximo: no se comprobó cuánto se puede quitar. **Ninguno se implementa aquí**: cada uno es una ficha.

| # | Cambio | Ahorro por prueba | Ahorro en la suite | Riesgo de aislamiento |
| :--- | :--- | ---: | :--- | :--- |
| 1 | **Agrupar las escrituras de los fixtures en una transacción.** Cada COMMIT de más cuesta también su BEGIN y su checkout | En `test_dpo_informe_anual`, 12 COMMIT por prueba frente a 3 de los demás: unos 27 viajes | Sin calcular fuera de ese archivo | **Bajo:** cada prueba sigue con sus datos |
| 2 | **Una sola sentencia para insertar y limpiar** en los fixtures de los archivos con más de 40 consultas de fixture por prueba | *Techo:* la parte de unas 46 sentencias por prueba que se pueda fundir | *Techo:* 5 918 sentencias de fixture en los diez archivos, unos 6 min en el oeste | **Bajo:** cada prueba sigue con sus datos. Hay que respetar el orden de las claves foráneas |
| 3 | **Quitar `pool_pre_ping` solo en las pruebas** | 1 viaje por checkout, unos 4 a 12 | 1 978 viajes, unos 2 min en el oeste | **Ninguno** para el aislamiento. Las pruebas dejan de usar lo mismo que producción, y `app_core/db/session.py` es código de producción |
| 4 | **Una llamada a `set_config` en lugar de dos** en `fijar_contexto_rls` | 1 viaje por petición con usuario y organización | Sin medir: el plugin no guarda sentencias | **Medio:** es el contexto de RLS, sensible. También acortaría producción |
| 5 | **`test_ficha_ajena_no_encontrada_y_permisos`:** repartir lo que recorre en una sola prueba | 220 consultas, la mayor cifra de la suite | Unos 13 s en el oeste como techo | **Bajo** |
| 6 | **Fixtures de módulo** en las pruebas que solo leen | *Techo:* las unas 46 sentencias por prueba | Se solapa con los cambios 1 y 2 | **Alto:** hay que comprobar archivo por archivo que ninguna prueba escriba. Nunca `rollback` en toda la suite |

**Recomendación:** empezar por el 1 y el 2, que no tocan producción ni el aislamiento. El 3 es el más barato, pero lo decide el propietario porque toca una configuración que comparte con producción.

**Lo que se puede esperar:** los viajes explican unos 27 min de la diferencia entre `westus` y `northcentralus`. Los cambios 2 y 3, en su techo, quitarían unos 8 min en el oeste, y en la práctica menos. Ninguno iguala las regiones: solo lo hace mover el ejecutor (informe de variación del arnés, histórico del PMV, sección 4).

## 5. Cómo repetir la medición

El worktree necesita su `.env` propio, solo con la base local.

```powershell
python scripts/contar_consultas_pruebas.py --todos --salida tabla.md --json filas.json
```

Sin `--todos` mide los 10 archivos de `MEDICION_PRUEBAS_LENTAS.md`. El script rechaza cualquier URL remota, y el JSON solo guarda contadores.
