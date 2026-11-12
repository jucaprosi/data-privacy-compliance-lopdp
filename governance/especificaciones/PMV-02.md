# PMV-02 · Reporte ejecutivo del Assessment: tablero HTML descargable, sin cifra única
`¤sdd` `¤diagnostico-reporte` `¤tablero-dimensiones`

## 1. Datos

Sin datos persistentes. El generador recibe, en el navegador:

- `ResultadoAssessment` calculado con `calcularResultadoAssessment("declarado")`. **Campos que usa:** `dimensiones[]` (`id`, `nombre`, `itemsAplicables`, `itemsEvaluados`, `coberturaPorcentaje`, `nivel`, `nivelEtiqueta`, `brechasCriticas`, `brechasAltas`), `brechas[]` (`preguntaId`, `control`, `dimensionId`, `dimensionNombre`, `severidad`, `nivelEfectivo`, `riesgo`, `esEstructural`), `brechasCriticas`, `brechasAltas`, `totalEvaluados`, `totalAplicables`, `coberturaInsuficiente`, `soloReferencia`.
- `CompanyData`: `razonSocial` y `sector`.
- La fecha de corte, tomada del navegador en la zona `America/Guayaquil`.

**Campos que el documento no puede mostrar** (son cifras de la organización, Doctrina 4): `scorePonderado`, `nivelTeorico`, `nivelTeoricoEtiqueta`, `nivelAjustado`, `nivelAjustadoEtiqueta`, el `coberturaPorcentaje` global y el `score` de cada dimensión.

Modelo derivado (`modeloReporteEjecutivo.ts`): `estado` («Preliminar» | «Completo»), `dimensionesEvaluadas` (0 a 10), `radar[]` (por dimensión: `id`, `nivel` o `null`), `prioridades[]` (las diez primeras, con `horizonte`) y `anexo[]` (todas las brechas críticas y altas).

## 2. API

Sin API nueva. La descarga es local: archivo `reporte-assessment-sgpdp-AAAA-MM-DD.html`, con la fecha de corte.

## 3. Reglas

- **R1 · Dimensión evaluada.** `evaluada(d) ⇔ d.itemsEvaluados > 0 ∧ d.nivel ≥ 1`. Si no, se rotula «Pendiente»; nunca se dibuja como cero ni cuenta como incumplimiento.
- **R2 · Estado.** `Completo ⇔ dimensionesEvaluadas = 10 ∧ ¬coberturaInsuficiente ∧ ¬soloReferencia`; en cualquier otro caso, «Preliminar».
- **R3 · Aviso de alcance.** Visible ⇔ el estado es «Preliminar»: el resultado describe solo lo evaluado y no es un nivel global ni una certificación. Si `soloReferencia`, el aviso añade que el conjunto es de referencia y sin valor probatorio.
- **R4 · Sin cifra única** (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`, Doctrina 4). Se permite: el nivel 1 a 5 de cada dimensión; la cobertura como «`totalEvaluados` de `totalAplicables` controles evaluados»; el porcentaje de cobertura solo por dimensión, rotulado «cobertura». No se muestra ningún nivel, puntaje ni porcentaje de la organización.
- **R5 · Brechas incluidas.** Solo `severidad ∈ {Crítico, Alto}`. Los contadores de brechas son `brechasCriticas` y `brechasAltas` del resultado.
- **R6 · Orden de las prioridades.** `esEstructural` descendente, luego severidad (Crítico antes que Alto), luego `riesgo` descendente, luego `preguntaId` ascendente. La sección muestra las diez primeras; el anexo muestra todas en el mismo orden.
- **R7 · Horizonte de gestión.** Crítico ∧ estructural ⇒ «0–30 días»; Crítico ∧ ¬estructural ⇒ «30–60 días»; Alto ⇒ «60–90 días». Siempre con la nota «Orden de trabajo interno; no es un plazo legal» (PRD, criterio 18).
- **R8 · Radar.** Diez ejes en el orden D01 a D10; radio `= nivel / 5`. Una dimensión pendiente no lleva punto y su eje muestra «Pendiente».
- **R9 · Evidencia del PMV.** El documento declara «Evidencia declarada, no verificada» (`INV_LOPDP_PMV_DECLARED_EVIDENCE`). No muestra evidencia por dimensión, porque el resultado no la trae.
- **R10 · Seguridad.** Todo texto del resultado y de la organización se escapa (`&`, `<`, `>`, `"`, `'`) antes de entrar en el HTML.
- **R11 · Autocontenido e imprimible.** Sin `<script>`, sin `<link>` y sin direcciones `http` o `https` en `src` o `href`; logo, estilos y colores dentro del propio documento; los colores son variables de `:root` tomadas de la marca; incluye reglas `@media print`.
- **R12 · Sin evaluaciones.** Con `totalEvaluados = 0` el documento se genera igual: estado «Preliminar», diez dimensiones pendientes, radar sin puntos y sin prioridades.
- **R-ADPA · Ortogonalidad (`PMV-02`).** Solo frontend: no importa módulos de otras salas ni llama a la API.

## 4. Interfaz

**Tarjeta en «Reportes»** (`ReportesModule.tsx`): título «Reporte de Assessment de Madurez SGPDP»; descripción «Tablero ejecutivo por dimensión: nivel 1 a 5, cobertura, brechas y prioridades.»; botón de descarga existente. La descripción no contiene «Score» ni «nivel ajustado».

**Documento descargable**, en este orden:
1. Encabezado con el logo, «Informe ejecutivo», organización, sector, fecha de corte y estado.
2. Aviso de alcance (R3).
3. Indicadores: «Cobertura del diagnóstico: N de M controles», «Dimensiones evaluadas: n de 10» y «Brechas confirmadas: críticas y altas».
4. Radar «Madurez observada por dimensión», escala 1 a 5, con la leyenda «Pendiente no equivale a incumplimiento».
5. Cobertura por dimensión (barras).
6. Mapa de las diez dimensiones: nivel o «Pendiente», brechas críticas y altas, y el rótulo de evidencia (R9).
7. Prioridades confirmadas (las diez primeras): prioridad, control, dimensión, severidad, estructural y horizonte (R6, R7).
8. Anexo: todas las brechas críticas y altas.
9. Pie: «Documento de trabajo interno, generado automáticamente a partir del estado del diagnóstico.»

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un resultado con 2 dimensiones evaluadas y 8 pendientes, **cuando** se descarga el reporte, **entonces** el estado es «Preliminar», aparece el aviso de alcance, el indicador dice «2 de 10» y las 8 dimensiones dicen «Pendiente». | `reportes/reporte-ejecutivo.spec.ts › resultado parcial` |
| **Dado** cualquier resultado, **entonces** el documento no contiene «Score Ponderado», «Nivel Ajustado» ni un porcentaje que no sea la cobertura de una dimensión. Mutación: añadir un puntaje de la organización hace fallar la prueba. | `reportes/reporte-ejecutivo.spec.ts › sin cifra única` |
| **Dado** una brecha cuyo control contiene `<script>alert(1)</script>`, **entonces** el HTML la muestra escapada y no contiene un `<script>` ejecutable. | `reportes/reporte-ejecutivo.spec.ts › escapa el texto` |
| **Dado** 12 brechas críticas y altas mezcladas, **entonces** las prioridades muestran 10 en el orden de R6 con el horizonte de R7, el anexo muestra las 12 y la nota dice que el horizonte no es un plazo legal. | `reportes/reporte-ejecutivo.spec.ts › orden y horizonte` |
| **Dado** un resultado sin controles evaluados, **entonces** el reporte se genera, el estado es «Preliminar», las diez dimensiones dicen «Pendiente» y el radar no tiene puntos. | `reportes/reporte-ejecutivo.spec.ts › sin evaluaciones` |
| **Dado** el documento descargado, **entonces** no tiene `<script>`, ni `<link>`, ni direcciones `http` o `https` en `src` o `href`, e incluye «declarada, no verificada». | `reportes/reporte-ejecutivo.spec.ts › autocontenido` |
| **Dado** un resultado con las diez dimensiones evaluadas, cobertura suficiente y datos propios, **entonces** el estado es «Completo» y no aparece el aviso de alcance. | `reportes/reporte-ejecutivo.spec.ts › resultado completo` |
| **Dado** la vista «Reportes», **entonces** la tarjeta del Assessment no contiene «Score ponderado» ni «nivel de madurez ajustado». | `reportes/reporte-ejecutivo.spec.ts › tarjeta sin score` |

## 6. Trazabilidad

- Ficha: `governance/tareas/PMV-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD, Módulo 1, apartado «Reporte ejecutivo del Assessment»; criterios 14, 18 y 26 de la sección 9; Doctrina 4.
- Invariantes: `INV_LOPDP_MULTIDIMENSIONAL_METRICS`, `INV_LOPDP_PMV_DECLARED_EVIDENCE`, `INV_LOPDP_SINGLE_ACTION_PLAN`.
- Escala: `governance/ESCALA_MADUREZ.md`; tareas DIAG-08, DIAG-09 y DIAG-13.
- Decisión de la propietaria (2026-11-12): las columnas «implicación» y «acción recomendada» quedan fuera de esta versión.
- Decisión abierta: la fecha de corte es la de la descarga; no hay un sello de emisión en el cliente.
