+++
id = "RET-00"
titulo = "Árbitro de plataforma única: main solo depende de Google Cloud"
ola = "backlog"
estado = "hecha"
sala = "pruebas"
depende_de = []
propiedad = ["governance/tareas/RET-00.md"]
crea = []
arbitro = "pytest tests/test_alembic_una_cabeza.py + suite completa contra PostgreSQL 16 local en contenedor"
rastros = ["¤arbitro", "¤seguridad"]
+++

# RET-00 · Árbitro de plataforma única

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-00.md`. Modelo sugerido: sonnet. Primera ficha del programa de plataforma única en Google Cloud (`governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`).

**Problema.** Consolidar la estructura de `tests/` y sus árbitros para operar nativamente sobre Google Cloud y PostgreSQL 16 local.

**Entrega.**
- Higiene del árbol de pruebas con `exigir_base_de_pruebas()` (`RET-01a`) y `tests/test_alembic_una_cabeza.py` en verde.
- Consistencia completa en workflows, `pytest.ini`, `tests/duraciones.json`, fichas y briefs.

