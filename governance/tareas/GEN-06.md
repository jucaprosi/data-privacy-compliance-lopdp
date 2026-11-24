+++
id = "GEN-06"
titulo = "Alembic sin marca: archivo y revisión 20261031_diag_escala_madurez, con su descendiente y un docstring"
ola = "backlog"
estado = "en_curso"
tanda = 101
sala = "diagnostico"
depende_de = ["GEN-02", "DIAG-08", "DPO-02", "BIB-103"]
propiedad = ["alembic/versions/20261031_diagnostico_escala_madurez.py", "alembic/versions/20261030_dpo_inscripcion.py", "alembic/versions/20261103_biblioteca_mis_plantillas.py", "tests/test_diagnostico_escala_1_5.py"]
crea = ["alembic/versions/20261031_diagnostico_escala_madurez.py"]
arbitro = "pytest tests/test_diagnostico_escala_1_5.py tests/test_alembic_cabeza_por_sala.py contra PostgreSQL; alembic heads con una cabeza por sala; mutación m1; alembic_version de los tres entornos leída por el propietario antes de fusionar (R1)."
rastros = ["¤adpa", "¤arbitro"]
+++

# GEN-06 · Alembic sin marca: archivo y revisión 20261031_diag_escala_madurez, con su descendiente y un docstring

**Contrato:** `governance/especificaciones/GEN-06.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- `alembic/versions/20261031_diagnostico_escala_smartcidi.py` se renombra a `20261031_diagnostico_escala_madurez.py`, con la revisión `20261031_diag_escala_madurez`, y su descendiente `20261030_dpo_inscripcion.py` apunta a ella.
- El docstring de `20261103_biblioteca_mis_plantillas.py` usa el término de GEN-03.

## Límites
- No se fusiona sin la lectura de `alembic_version` del propietario (especificación R1). El SQL de las migraciones no cambia.
