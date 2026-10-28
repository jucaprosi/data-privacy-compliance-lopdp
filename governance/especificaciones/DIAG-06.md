# DIAG-06 · Comparativo con la línea base
`¤sdd` `¤diagnostico`

## 1. Datos

Sin tablas nuevas. Lee resultados sellados (`diagnostico_resultados`, DIAG-03) por `diagnostico_service.listar_resultados`. La línea base es el resultado con menor `secuencia` salvo que se indique otro.

## 2. API

Router `api/routers/diagnostico_comparativo.py`, prefijo `/diagnostico`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /diagnostico/comparativo?base=&actual=` | `implementador`, `coordinador`, `dpo`, `admin_organizacion` | ids opcionales; por defecto `base` = menor secuencia, `actual` = mayor | `200 Comparativo` |

`Comparativo` = `{base: {id, secuencia, sellado_en}, actual: {id, secuencia, sellado_en}, dimensiones: [{dimension, nombre, base: Indicadores, actual: Indicadores, delta: {nivel_madurez: int, brechas_criticas: int}}], brechas: {cerradas: [Brecha], nuevas: [Brecha], persistentes: [Brecha]}}`. `Indicadores` por dimensión = `{nivel_madurez, brechas_criticas, brechas_altas}`; `Brecha` = `{pregunta_id, control, dimension, severidad}`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 404 | `DIAG_SIN_RESULTADO` | menos de un resultado sellado |
| 404 | `RESULTADO_NO_ENCONTRADO` | `base` o `actual` no existen en la organización |
| 409 | `COMPARATIVO_MISMO_RESULTADO` | `base = actual` |
| 409 | `COMPARATIVO_ORDEN` | `secuencia(base) > secuencia(actual)` |

## 3. Reglas

- **R1 · Conjuntos.** Sea `B` el conjunto de `(pregunta_id)` con brecha (severidad `CRITICO` o `ALTO`) en la base y `A` en el actual: `cerradas = B \ A`, `nuevas = A \ B`, `persistentes = A ∩ B`.
- **R2 · Por dimensión.** `delta.nivel_madurez = actual.nivel_madurez − base.nivel_madurez` (entero, puede ser negativo); igual para `brechas_criticas`.
- **R3 · Sin cifra única.** No hay «avance global» ni promedio de deltas (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- **R4 · Misma organización.** Ambos resultados salen de la consulta con el tenant del token; RLS impide mezclar.
- **R5 · Un solo resultado.** Con un único resultado sellado, la pantalla lo dice y no hay comparación (404 en la API).

## 4. Interfaz

Pantalla Diagnóstico › Comparativo (`menus/DIAG-06.ts`, `pantallas/DIAG-06.tsx`, `Comparativo.tsx`): selectores de base y actual (fecha y secuencia); tabla por dimensión con nivel base, nivel actual y delta con flecha; tres listas de brechas (cerradas, nuevas, persistentes) con las tarjetas de FE-24. Con un solo resultado: «Aún no hay un segundo assessment sellado».

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** base con brechas {P3, P7, P12} y actual con {P7, P20}, **entonces** `cerradas = [P3, P12]`, `nuevas = [P20]`, `persistentes = [P7]`. Mutación: invertir base y actual hace fallar la prueba. | `test_comparativo_conjuntos` |
| **Dado** `D04` con nivel 1 en base y 3 en actual, **entonces** `delta.nivel_madurez = 2`. | `test_comparativo_delta_dimension` |
| **Dado** un resultado de otra organización como `actual`, **entonces** 404. | `test_comparativo_rls` |
| **Dado** `base = actual`, **entonces** 409 `COMPARATIVO_MISMO_RESULTADO`. | `test_comparativo_mismo` |
| **Dado** la respuesta, **entonces** no contiene `avance_global` ni `promedio`. | `test_comparativo_sin_cifra_unica` |
| **Dado** dos resultados simulados, **cuando** se abre la pantalla, **entonces** se ven las tres listas y ningún porcentaje global. | `frontend/tests/diagnostico/comparativo.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-06.md`. PRD: Módulo 1 («Comparativo»). Contraste: apartado 6 (DIAG), D-1.
