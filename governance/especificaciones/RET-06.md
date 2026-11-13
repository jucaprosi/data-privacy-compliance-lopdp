# RET-06 · Pruebas sin la «rama Neon»: una sola guardia común
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Cambian solo archivos de prueba:

- los que tienen el aviso «rama Neon» en el docstring y el `assert "ep-late-hall" not in url` repetido (unos 62 en `tests/`);
- las configuraciones de Playwright `humo` e `integracion` y `tests/humo/servidor_humo.py`;
- `tests/matriz/FIRMA-03.py` y `FIRMA-04.py`.

La lista exacta es `tests/sin_plataformas_pmv/pendientes/RET-06.txt`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Una sola guardia.** Cada archivo sustituye su comprobación propia por una llamada a `exigir_base_de_pruebas()` de `tests/conftest.py` (RET-01). Ningún archivo conserva una copia de la comprobación.
- **R2 · Lo que afirma cada prueba no cambia.** El cambio es mecánico: docstring y guardia. Si una prueba necesita otro cambio para pasar, queda fuera del PR y se informa.
- **R3 · Un PR por dominio.** Biblioteca, diagnóstico, roadmap, organización, evidencias, firma y resto. Un archivo que posee una ficha `en_curso` o `pendiente` no entra hasta que esa ficha esté fusionada, o lo limpia esa ficha.
- **R4 · Script revisado a mano.** La sustitución la hace un script; su diff se revisa archivo por archivo antes del commit.
- **R5 · La lista solo baja.** Cada PR reduce `pendientes/RET-06.txt` en lo que limpió.
- **R-ADPA · Ortogonalidad ZERAG (`RET-06`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un archivo de pruebas con base, **entonces** llama a `exigir_base_de_pruebas()` y no contiene `ep-late-hall` ni «rama Neon». | `test_sin_menciones_fuera_de_las_listas` |
| **Dado** la guardia común con una base no local, **entonces** la prueba se detiene antes de conectar. Mutación: una copia local de la comprobación vuelve a contar como mención y el árbitro da rojo. | `test_guardia_comun_unica` |
| **Dado** el último PR de dominio, **entonces** `pendientes/RET-06.txt` queda vacío y la suite completa pasa en el CI. | `test_pendientes_sin_crecer` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-06.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763, 39dbf4b5), decisiones del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. La historia del PMV la retira RET-07. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-00 y RET-01. Absorbe NEON-02.
- Medido: `tests/test_diagnostico_respuestas.py` y `tests/test_diagnostico_resultados.py` son de DIAG-07 (`en_curso`); el dominio diagnóstico va después de DIAG-07.
