# GEN-02 · Escala de madurez de 1 a 5 sin marca: versión madurez_1_5, contrato, servidor, pantalla y archivo de assessment
`¤sdd` `¤diagnostico-scoring` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Programa: GEN-01 §0. Estado final: los 37 archivos de la propiedad usan el vocabulario de GEN-01 R1.

Hecho medido en `origin/main` ea6d26bf:
- `features/diagnostico/domain/models.py:46`: `ESCALA_SELLADA` es la versión de escala que se escribe en `indicadores.escala` de cada diagnóstico sellado (`diagnostico_resultados.indicadores`, JSONB), y que cubre su huella SHA-256.
- `resultados.py:89` y `:105`: un `indicadores.escala` distinto de `ESCALA_SELLADA` se trata como escala anterior: se conserva tal cual y se lee como «anterior». `AuditHistory.tsx:36` y `lib/diagnostico/indicadores.ts:36` repiten la comparación en la pantalla.
- `escala_madurez.json`: `version`, `decision`, `fuente.archivo` (con la huella `328127a1…`) y `lectura_historica`, que nombra la prueba de la escala. `scripts/verificar_escala_madurez.py` busca el archivo en la raíz o en `data/` (`archivo_fuente`) y comprueba su huella (E2).
- `ESCALA_MADUREZ.md:4` e `INFORME_SEGURIDAD_PRESENTACION_LOPDP.md:56` nombran el archivo de assessment.
- `tests/test_diag07b_siembra_como_admin.py:23` y `tests/duraciones.json:45` nombran la prueba de la escala.

## 2. API

Ninguna ruta cambia de forma. `indicadores.escala` de los sellados nuevos vale `"madurez_1_5"`. Las descripciones de `nivel_asignado` (`api/routers/diagnostico.py:38,51`) dicen «Nivel asignado de la escala de madurez de 1 a 5».

## 3. Reglas

- **R1 · Resultados sellados: el recuento del propietario va antes de lanzar.**
  - El propietario cuenta, en producción, pruebas y demo, los sellados con la versión de escala que retira esta ficha. Lo hace con la consulta de solo lectura del brief `C:\Users\Juan Carlos\compartido\evydentia\briefs\GEN-propietario-recuentos.md`.
  - **Con cero en los tres entornos**, el cambio es limpio y la ficha se lanza.
  - **Con alguno**, la ficha no se lanza: el recuento se anota en esta especificación y decide el CTO.
  - **Un sellado nunca se reescribe.** Su huella cubre la escala.
- **R2 · Una sola versión.** `ESCALA_SELLADA = "madurez_1_5"`. `resultados.py`, `AuditHistory.tsx`, `indicadores.ts` (tipo `"madurez_1_5" | "anterior"`) y `escala_madurez.json` (`version`) la toman del contrato o de la constante. No hay alias ni lectura doble.
- **R3 · Textos.**
  - Todos los textos y comentarios dicen «escala de madurez de 1 a 5».
  - `useAuditStore.ts` conserva su `version: 6`: solo cambia el comentario y no la forma persistida.
  - `escala-activa.spec.ts` y `escala.spec.ts` nombran la escala por su nombre final en `describe`.
- **R4 · Archivo de assessment.**
  - `Assessment_Madurez_SGPDP_COAC_SMARTCIDI (2).xlsx` se renombra con `git mv` a `Assessment_Madurez_SGPDP.xlsx`, en la raíz. Los bytes no cambian, así que la huella `328127a1…` es la misma y E2 sigue en verde.
  - `escala_madurez.json` (`fuente.archivo`), `ESCALA_MADUREZ.md:4`, `INFORME_SEGURIDAD_PRESENTACION_LOPDP.md:56` y `scripts/verificar_escala_madurez.py` (E2) lo nombran así.
- **R5 · Prueba renombrada.**
  - `tests/test_diagnostico_escala_smartcidi.py` pasa a `tests/test_diagnostico_escala_1_5.py` con `git mv`. Sus funciones nombran la escala final, por ejemplo `test_la_escala_es_la_del_archivo_de_assessment`.
  - `MIGRACION` sigue apuntando al archivo de Alembic vigente hasta GEN-06, que la actualiza.
  - `lectura_historica`, `test_diag07b_siembra_como_admin.py` y `duraciones.json` nombran la ruta nueva.
- **R6 · Sin prohibiciones.** Ninguna prueba busca la palabra retirada (GEN-01 R3). E4 sigue vigilando solo el vocabulario retirado de la escala 0 a 3, como hoy.
- **R-ADPA · Ortogonalidad ZERAG (`GEN-02`).** Solo la propiedad. El pasillo `app_core/pasillo/diagnostico.py` solo cambia su docstring. Sin `import yaml`.

## 4. Interfaz

Textos visibles: «escala de madurez de 1 a 5» donde hoy figura el nombre de la marca. UX/UI confirma los textos en el PR. La forma no cambia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un diagnóstico sellado nuevo, **entonces** `indicadores.escala == "madurez_1_5"` y su huella se verifica. Mutación m1: dejar el valor anterior en `escala_madurez.json` y cambiar la constante (o al revés) da rojo. | `tests/test_diagnostico_escala_1_5.py`, `tests/test_escala_madurez.py` |
| **Dado** un sellado simulado sin escala, **entonces** se lee como «anterior» y su huella no cambia. | `tests/test_diagnostico_resultados.py`, `tests/test_roadmap_hallazgos.py` |
| **Dado** el archivo de assessment, **entonces** `verificar_escala_madurez.py` da código 0 con `Assessment_Madurez_SGPDP.xlsx`. Mutación m2: dejar `fuente.archivo` con el nombre anterior da rojo en E2. | `python scripts/verificar_escala_madurez.py` |
| **Dado** la pantalla con resultados simulados `madurez_1_5`, **entonces** el historial y la cartera los muestran como escala vigente. Mutación m3: comparar con otra cadena en `AuditHistory.tsx` da rojo. | `frontend/tests/diagnostico/`, `cartera.spec.ts`, `ficha-resumen.spec.ts` |

## 6. Trazabilidad

- Programa GEN-01 §0. Vocabulario de GEN-01 R1. Condición §5.1 del brief del CTO.
- Depende de las fichas hechas que comparten estos archivos: DIAG-08, DIAG-09, DIAG-10 y DIAG-13.
