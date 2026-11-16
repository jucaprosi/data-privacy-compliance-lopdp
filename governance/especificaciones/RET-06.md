# RET-06 · Guardia única de base de pruebas en `tests/`
`¤sdd` `¤arbitro`


## 1. Datos

Sin tablas. Cambian solo archivos de prueba:

- los archivos de prueba de dominio en `tests/` que validan la base mediante `exigir_base_de_pruebas()`;
- las configuraciones de Playwright `humo` e `integracion` y `tests/humo/servidor_humo.py`;
- `tests/matriz/FIRMA-03.py` y `FIRMA-04.py`.

La ficha mide la lista exacta al empezar: las pruebas de `tests/` que comprueban la base por su cuenta en lugar de llamar a `exigir_base_de_pruebas()` (RET-01a).

## 2. API

No aplica.

## 3. Reglas

- **R1 · Una sola guardia.** Cada archivo sustituye su comprobación propia por una llamada a `exigir_base_de_pruebas()` de `tests/conftest.py` (RET-01). Ningún archivo conserva una copia de la comprobación.
- **R2 · Lo que afirma cada prueba no cambia.** El cambio es mecánico: docstring y guardia. Si una prueba necesita otro cambio para pasar, queda fuera del PR y se informa.
- **R3 · Un PR por dominio.** Biblioteca, diagnóstico, roadmap, organización, evidencias, firma y resto. Un archivo que posee una ficha `en_curso` o `pendiente` no entra hasta que esa ficha esté fusionada, o lo limpia esa ficha.
- **R4 · Script revisado a mano.** La sustitución la hace un script; su diff se revisa archivo por archivo antes del commit.
- **R5 · Por dominio.** Cada PR limpia las pruebas de un dominio y deja la suite en verde.
- **R6 · Sin texto de sustitución.** El docstring nuevo describe la prueba sobre el PostgreSQL 16 local o el del CI. No dice qué había antes ni usa un término neutro en su lugar.
- **R-ADPA · Ortogonalidad ZERAG (`RET-06`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cada PR de dominio, **entonces** sus archivos llaman a `exigir_base_de_pruebas()` y la suite pasa. | la suite existente en el CI |
| **Dado** el último PR de dominio, **entonces** ninguna prueba de `tests/` comprueba la base por su cuenta, y la suite completa pasa en el CI. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-06.md`.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-00 y RET-01a.
- Medido: `tests/test_diagnostico_respuestas.py` y `tests/test_diagnostico_resultados.py` son de DIAG-07 (`en_curso`); el dominio diagnóstico va después de DIAG-07.
