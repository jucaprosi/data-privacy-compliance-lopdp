# RET-00 · Árbitro sin plataformas del PMV en `main`
`¤sdd` `¤arbitro` `¤seguridad`

## 1. Datos

Sin tablas ni migraciones. Los datos son las listas del árbitro, en `tests/sin_plataformas_pmv/`:

- `permitidos.txt`: lista cerrada de historia, con entradas `ruta_o_patrón|motivo`. Solo admite:
  - `alembic/versions/**` y `governance/historico/pmv/**`;
  - `governance/artefactos/APORTES_INEDITOS.md` y `governance/artefactos/FUENTES_Y_BIBLIOGRAFIA.md`;
  - las fichas con `estado = "hecha"` y los informes y partes fechados;
  - `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` y la propia carpeta del árbitro.
- `pendientes/<ficha>.txt`: una lista por ficha dueña (`RET-01`, `RET-02`, `RET-03`, `RET-05`, `RET-06`, `IA-04`, `IA-06`, `IA-08`), con `ruta|recuento` de las menciones que esa ficha retira.
- Las listas de `tests/sin_neon/` no se borran aquí: las retira RET-07. Los pendientes de `tests/sin_neon/pendientes/NEON-02.txt` pasan a `pendientes/RET-06.txt`. Los de `NEON-01`, `NEON-03`, `NEON-04` y `FIRMA-02` conservan su ficha dueña.

## 2. API

No aplica: no hay rutas HTTP.

## 3. Reglas

- **R1 · Patrones.** El árbitro busca, sin distinguir mayúsculas, `neon`, `ep-late-hall`, `vercel`, `upstash`, `r2.cloudflarestorage`, `R2_`, `boto3`, `deepseek`, `openai`, `dotenv` y `load_dotenv` en todos los archivos versionados. Cada patrón se ancla para no contar dentro de otra palabra; la prueba lista los casos que no deben contar.
- **R2 · Toda mención tiene dueño.** Una mención que no está en `permitidos.txt` ni en un `pendientes/<ficha>.txt` pone el árbitro en rojo y dice el archivo y la línea.
- **R3 · Solo decrece.** Contra `origin/main`, ni `permitidos.txt` ni ningún `pendientes/*.txt` ganan entradas ni suben recuentos. La única excepción es el PR que crea el árbitro.
- **R4 · Listas cerradas.** Una entrada de pendientes cuyo archivo ya no tiene menciones es un error: se retira en el mismo PR que la limpió. Un pendiente a nombre de una ficha `hecha` es un error.
- **R5 · No toca código de producto.** Esta ficha solo crea el árbitro y sus listas. No retira ninguna mención.
- **R6 · Convive con `tests/test_sin_neon.py`** hasta RET-07; los dos corren en el CI.
- **R-ADPA · Ortogonalidad ZERAG (`RET-00`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica: no hay pantalla.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol de `main`, **cuando** corre el árbitro, **entonces** toda mención está en permitidos o en pendientes de una ficha abierta. | `test_sin_menciones_fuera_de_las_listas` |
| **Dado** una mención nueva de cualquiera de los patrones en un archivo de producto, **entonces** rojo con archivo y línea. Mutación: añadir `upstash` a un módulo hace fallar la prueba. | `test_mencion_nueva_da_rojo` |
| **Dado** una lista con una entrada más o un recuento mayor que en `origin/main`, **entonces** rojo. Mutación: permitir que crezca hace fallar la prueba. | `test_listas_cerradas_y_sin_crecer` |
| **Dado** un pendiente a nombre de una ficha `hecha` o de un archivo ya limpio, **entonces** rojo. | `test_pendientes_con_dueno_abierto` |
| **Dado** palabras que contienen un patrón sin serlo, **entonces** no cuentan. | `test_patrones_sin_falsos_positivos` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-00.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763), decisión del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se toca la rama `produccion` ni la historia (`alembic/versions/`, `governance/historico/pmv/`, fichas `hecha`, aportes, bibliografía). `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Generaliza `tests/test_sin_neon.py` (NEON-01; M2: las listas solo decrecen). Absorbe NEON-02, cuyos pendientes pasan a RET-06.
