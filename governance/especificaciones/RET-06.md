# RET-06 · Pruebas sin la «rama de la base gestionada»: una sola guardia común
`¤sdd` `¤arbitro`

> **Convención.** «BG» es la serie de fichas del árbitro vigente de la base gestionada del PMV (BG-00 a BG-04), y «el árbitro vigente» es su prueba en `tests/`. Este documento no escribe el nombre del proveedor porque ese árbitro no admite menciones nuevas.

## 1. Datos

Sin tablas. Cambian solo archivos de prueba:

- los que tienen el aviso «rama de la base gestionada» en el docstring y el `assert "ep-late-hall" not in url` repetido (unos 62 en `tests/`);
- las configuraciones de Playwright `humo` e `integracion` y `tests/humo/servidor_humo.py`;
- `tests/matriz/FIRMA-03.py` y `FIRMA-04.py`.

La lista exacta es `tests/plataforma_unica/pendientes/RET-06.txt` (regla R5 de RET-00: una sola guardia de base).

## 2. API

No aplica.

## 3. Reglas

- **R1 · Una sola guardia.** Cada archivo sustituye su comprobación propia por una llamada a `exigir_base_de_pruebas()` de `tests/conftest.py` (RET-01). Ningún archivo conserva una copia de la comprobación.
- **R2 · Lo que afirma cada prueba no cambia.** El cambio es mecánico: docstring y guardia. Si una prueba necesita otro cambio para pasar, queda fuera del PR y se informa.
- **R3 · Un PR por dominio.** Biblioteca, diagnóstico, roadmap, organización, evidencias, firma y resto. Un archivo que posee una ficha `en_curso` o `pendiente` no entra hasta que esa ficha esté fusionada, o lo limpia esa ficha.
- **R4 · Script revisado a mano.** La sustitución la hace un script; su diff se revisa archivo por archivo antes del commit.
- **R5 · La lista solo baja.** Cada PR reduce `pendientes/RET-06.txt` en lo que limpió.
- **R6 · Sin texto de sustitución.** El docstring nuevo describe la prueba sobre el PostgreSQL 16 local o el del CI. No dice qué había antes ni usa un término neutro en su lugar.
- **R-ADPA · Ortogonalidad ZERAG (`RET-06`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un archivo de pruebas con base, **entonces** llama a `exigir_base_de_pruebas()` y no compara por su cuenta el host de la base. | `test_guardia_de_base_unica` |
| **Dado** la guardia común con una base no local, **entonces** la prueba se detiene antes de conectar. Mutación: dejar una copia local de la comprobación hace fallar el árbitro. | `test_guardia_comun_unica` |
| **Dado** el último PR de dominio, **entonces** `pendientes/RET-06.txt` queda vacío y la suite completa pasa en el CI. | `test_catalogos_y_pendientes_cerrados` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-06.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763, 39dbf4b5), decisiones del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. La historia del PMV la retira RET-07. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-00 y RET-01. Absorbe BG-02.
- Medido: `tests/test_diagnostico_respuestas.py` y `tests/test_diagnostico_resultados.py` son de DIAG-07 (`en_curso`); el dominio diagnóstico va después de DIAG-07.
