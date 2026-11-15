# RET-00 · Árbitro y depuración de pruebas nativas en Google Cloud
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. La suite de pruebas ejecuta directamente contra PostgreSQL 16 local y los contratos nativos de Google Cloud.

| Componente | Estado final |
| :--- | :--- |
| `tests/conftest.py` y `exigir_base_de_pruebas()` | única guardia común para la suite contra PostgreSQL 16 local o el servicio del CI |
| `tests/test_alembic_una_cabeza.py`, `tests/test_indice_tareas.py` y `tests/test_reparto.py` | árbitros activos de migraciones, tareas y reparto |
| suite de producto en `tests/` | pruebas de dominio y contratos de Google Cloud, GCS, Vertex AI y Cloud Run |

## 2. API

No aplica.

## 3. Reglas

- **R1 · Conjunto depurado de pruebas.** Toda prueba en `tests/` valida comportamiento real de la aplicación o de sus árbitros estructurales vigentes en Google Cloud.
- **R2 · Referencias coherentes.** Los workflows, `pytest.ini`, `tests/duraciones.json`, las fichas y los briefs referencian únicamente archivos de prueba activos.
- **R3 · Lo que se conserva.** La guardia de base de pruebas local, `exigir_base_de_pruebas()`, pertenece a `RET-01a`.
- **R4 · Verde.** La suite completa pasa contra PostgreSQL 16 local y en el CI.
- **R-ADPA · Ortogonalidad ZERAG (`RET-00`).** Solo `tests/` y gobernanza.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `main`, **entonces** todas las referencias de `tests/` corresponden a módulos y pruebas vigentes en Google Cloud. | criterio de revisión del PR |
| **Dado** el CI, **entonces** la suite completa pasa contra `postgres:16`. | la suite existente |
| **Dado** `pytest.ini`, `tests/duraciones.json` y las fichas, **entonces** todos los nombres citados existen en el árbol activo. | `tests/test_indice_tareas.py` y `tests/test_reparto.py`, que ya existen |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-00.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`.
