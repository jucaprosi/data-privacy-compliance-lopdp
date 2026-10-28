# ORG-15 · Cartera de organizaciones por pertenencia
`¤sdd` `¤rbac-tenant` `¤cartera`

## 1. Datos

Sin tablas nuevas. Lee `mis_organizaciones(usuario) RETURNS TABLE (tenant_id text, nombre_comercial text, roles text[])` (ORG-13, `SECURITY DEFINER`, `EXECUTE` solo para `lopdp_app`) y, por cada organización, con `fijar_contexto_rls(session, tenant_id, user_id)` en su propia transacción: el último resultado sellado (`diagnostico_service`), los hallazgos `abierto` (`roadmap_service`, RM-21) y las tareas no `completada` con `end_date < hoy` (`roadmap_service`).

## 2. API

Router `api/routers/organizacion_cartera.py`, prefijo `/organizacion`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /organizacion/cartera` | cualquier usuario autenticado; **no exige** `X-Tenant-ID` (como `/organizacion/mis-organizaciones`, declarada en `FUERA_DE_MATRIZ`) | — | `200 {"organizaciones": [FilaCartera]}` ordenadas por `nombre` |

`FilaCartera` = `{tenant_id, nombre, roles: [str], diagnostico: {nivel_madurez: int, cumplimiento: bool, respaldo_documental: float, riesgo_residual: float, brechas_criticas: int, sellado_en: str} | null, hallazgos_abiertos: int, tareas_vencidas: int, cadena_integra: bool}`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 401 | — | sin token válido |
| 200 con `organizaciones: []` | — | la persona no tiene rol vigente en ninguna organización (no es error) |

Si una organización falla al calcular sus indicadores, su fila lleva `diagnostico: null`, `hallazgos_abiertos: null`, `tareas_vencidas: null` y `error: "SIN_DATOS"`; la respuesta sigue siendo 200.

## 3. Reglas

- **R1 · Pertenencia.** `organizaciones = mis_organizaciones(user_id)`; ningún otro origen. `∀ f ∈ respuesta : ∃ rol vigente (user_id, f.tenant_id)` (`INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`).
- **R2 · Una transacción por organización.** Los indicadores de `f` se consultan solo con `app.current_tenant_id = f.tenant_id`; nunca con una consulta que cruce organizaciones, nunca con `BYPASSRLS`.
- **R3 · Sin cifra única.** La fila lleva las cuatro dimensiones y las brechas; no lleva promedio ni puntaje global (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- **R4 · Sin datos personales.** La respuesta no incluye correos, nombres de personas ni contenidos; solo nombre comercial, roles de quien consulta y contadores.
- **R5 · Tareas vencidas.** `end_date < hoy` en `America/Guayaquil` y `status ≠ 'completada'`.
- **R6 · Fase 2 fuera.** Sin proyección ni caché; si la cartera supera 50 organizaciones, la respuesta puede tardar y se abre la fase 2 de O-4 como tarea nueva.

## 4. Interfaz

`frontend/src/app/cartera/`: pantalla Inicio › Tablero de cartera. Tabla con una fila por organización: nombre, roles, cuatro semáforos (tarjetas de `components/tableros/`, FE-24), brechas críticas, hallazgos abiertos, tareas vencidas. Elegir una fila cambia de organización con el selector de FE-21. Con cero organizaciones: «Tu cuenta no pertenece a ninguna organización; pide una invitación». Entrada de menú en `menus/ORG-15.ts` (menú `inicio`, vista `cartera`).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** rol vigente en A y B, **cuando** se pide la cartera, **entonces** aparecen A y B; **y** tras revocar el rol en B, solo A. Mutación: listar todas las organizaciones del operador hace fallar la prueba. | `test_cartera_por_pertenencia` (INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP) |
| **Dado** un hallazgo abierto solo en B, **cuando** se calcula la fila de A con `lopdp_app`, **entonces** `hallazgos_abiertos` de A es 0. | `test_cartera_contexto_por_organizacion` |
| **Dado** una organización sin diagnóstico sellado, **entonces** su fila lleva `diagnostico: null` y la respuesta es 200. | `test_cartera_sin_diagnostico` |
| **Dado** la respuesta, **entonces** no contiene claves `email`, `promedio` ni `puntaje`. | `test_cartera_sin_datos_personales_ni_cifra_unica` |
| **Dado** una persona con dos organizaciones, **cuando** abre Inicio › Tablero de cartera y elige la segunda, **entonces** el encabezado muestra esa organización. | `frontend/tests/cartera/cartera.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-15.md`. PRD: §3.2 (cartera), criterio 15. Invariante: `INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`. Función de origen: `alembic/versions/20261028_organizaciones_por_persona.py`.
- Decisión abierta: umbral de 50 organizaciones para abrir la fase 2 (proyección).
