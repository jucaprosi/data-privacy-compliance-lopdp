+++
id = "RET-10"
titulo = "Comentarios de las migraciones aplicadas sin nombrar plataformas retiradas"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["RET-00", "RET-01a", "BIB-117"]
propiedad = ["alembic/versions/20261008_app_role_rls.py", "alembic/versions/20261108_biblioteca_capacidades_propietario.py"]
crea = []
arbitro = "pytest tests/test_alembic_una_cabeza.py + suite completa en el CI; el AST de cada archivo, sin docstrings, queda idéntico al de origin/main (se comprueba una sola vez al revisar el PR)"
rastros = ["¤arbitro"]
+++

# RET-10 · Comentarios de las migraciones aplicadas

Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md` (§4). Especificación del Arquitecto: `governance/especificaciones/RET-10.md` (por redactar; la ficha no se lanza sin ella). Modelo sugerido: sonnet.

**Medido por el Arquitecto.** Alembic 1.20.0 identifica cada migración por su revisión; `alembic_version` solo guarda `version_num` y no calcula ninguna suma del contenido. Reescribir comentarios y docstrings no cambia las cabezas ni rompe las bases ya migradas.

**Entrega.**
- Solo comentarios y docstrings de `alembic/versions/20261008_app_role_rls.py` y `alembic/versions/20261108_biblioteca_capacidades_propietario.py`: describen el rol de aplicación y la biblioteca en términos de Cloud SQL y del PostgreSQL local, sin nombrar plataformas retiradas.
- No se tocan `upgrade`, `downgrade` ni los identificadores de revisión.
- Comprobación del PR (una sola vez, no queda como prueba permanente): el AST de cada archivo, sin docstrings, es idéntico al de `origin/main`.
- Fuera de alcance: `r2_key` en `20261005_roadmaps.py` y `org20_papelera.py` es esquema vivo; lo renombra la migración nueva de RET-02.
