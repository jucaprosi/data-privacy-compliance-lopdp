# RET-00 · Árbitro sin plataformas del PMV en `main`
`¤sdd` `¤arbitro` `¤seguridad`

Segunda decisión del propietario (2026-11-13): el árbitro va **sin lista blanca de historia**.

## 1. Datos

Sin tablas ni migraciones. Los datos son las listas del árbitro, en `tests/sin_plataformas_pmv/`:

- `exclusiones.txt`: lista cerrada y fija, con tres entradas y ninguna más:
  - `alembic/versions/**`, porque esa cadena de migraciones es también la historia de la base de EVYDENTIA en Cloud SQL y no se puede reescribir;
  - `tests/sin_plataformas_pmv/**` y `tests/test_sin_plataformas_pmv.py`, la propia carpeta del árbitro;
  - `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`, solo mientras el programa esté abierto. RET-07 retira esta entrada.
- `pendientes/<ficha>.txt`: una lista por ficha dueña (`RET-01`, `RET-02`, `RET-03`, `RET-05`, `RET-06`, `RET-07`, `IA-04`, `IA-06`, `IA-08`), con `ruta|recuento` de las menciones que esa ficha retira o reformula.
- No hay `permitidos.txt`. Las menciones de la historia del PMV (`governance/historico/pmv/`, fichas `hecha`, aportes, bibliografía, informes fechados, `tests/sin_neon/`) entran como pendientes de `RET-07`.
- Los pendientes de `tests/sin_neon/pendientes/NEON-02.txt` pasan a `pendientes/RET-06.txt`.

## 2. API

No aplica: no hay rutas HTTP.

## 3. Reglas

- **R1 · Patrones.** El árbitro busca, sin distinguir mayúsculas, `neon`, `ep-late-hall`, `vercel`, `upstash`, `r2.cloudflarestorage`, `R2_`, `boto3`, `deepseek`, `openai`, `dotenv` y `load_dotenv` en todos los archivos versionados. Cada patrón se ancla para no contar dentro de otra palabra; la prueba lista los casos que no deben contar.
- **R2 · Toda mención tiene dueño.** Una mención fuera de las tres exclusiones y de los `pendientes/<ficha>.txt` pone el árbitro en rojo y dice el archivo y la línea.
- **R3 · Sin lista blanca.** `exclusiones.txt` no admite ninguna línea más que las tres de §1. Añadir una da rojo. La comparación es contra una constante del propio árbitro, no contra `origin/main`.
- **R4 · Los pendientes solo decrecen.** Contra `origin/main`, ningún `pendientes/*.txt` gana entradas ni sube recuentos. La única excepción es el PR que crea el árbitro.
- **R5 · Listas cerradas.** Una entrada de pendientes cuyo archivo ya no tiene menciones es un error: se retira en el mismo PR que la limpió. Un pendiente a nombre de una ficha `hecha` es un error.
- **R6 · No toca código de producto ni historia.** Esta ficha solo crea el árbitro y sus listas. No retira ni reformula ninguna mención.
- **R7 · Convive con `tests/test_sin_neon.py`.** Los dos corren hasta RET-07. `test_sin_neon` está entre los árbitros mínimos de cada fusión: no se retira aquí, y RET-07 solo lo retira cuando este árbitro ya está en `main` y en la lista de árbitros mínimos.
- **R-ADPA · Ortogonalidad ZERAG (`RET-00`).** El árbitro no importa de ninguna sala.

## 4. Interfaz

No aplica: no hay pantalla.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol de `main`, **cuando** corre el árbitro, **entonces** toda mención está en una de las tres exclusiones o en pendientes de una ficha abierta. | `test_sin_menciones_fuera_de_las_listas` |
| **Dado** una mención nueva de cualquiera de los patrones en un archivo de producto, **entonces** rojo con archivo y línea. Mutación: añadir `upstash` a un módulo hace fallar la prueba. | `test_mencion_nueva_da_rojo` |
| **Dado** una cuarta línea en `exclusiones.txt`, **entonces** rojo. Mutación: añadir una línea a la lista hace fallar la prueba. | `test_sin_lista_blanca` |
| **Dado** un `pendientes/*.txt` con una entrada más o un recuento mayor que en `origin/main`, **entonces** rojo. Mutación: permitir que crezca hace fallar la prueba. | `test_pendientes_sin_crecer` |
| **Dado** un pendiente a nombre de una ficha `hecha` o de un archivo ya limpio, **entonces** rojo. | `test_pendientes_con_dueno_abierto` |
| **Dado** palabras que contienen un patrón sin serlo, **entonces** no cuentan. | `test_patrones_sin_falsos_positivos` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-00.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763, 39dbf4b5), con las dos decisiones del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- Generaliza `tests/test_sin_neon.py` (NEON-01). Absorbe NEON-02, cuyos pendientes pasan a RET-06.
- `.github/workflows/` y `verificadores/` son del propietario: si la lista de árbitros mínimos vive ahí, va un brief.
