# ¤roadmap
"""Prueba de integridad de Alembic: garantiza una sola cabeza de migraciones (RM-00).

Invariante: La base de datos no puede tener ramas de migraciones divergentes o múltiples cabezas.
Cualquier migración nueva debe encadenarse a la cabeza actual de main.
"""
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory

RAIZ = Path(__file__).resolve().parent.parent


def test_alembic_tiene_exactamente_una_cabeza():
    """Verifica que get_heads() de Alembic devuelva exactamente una sola revisión head."""
    alembic_ini = RAIZ / "alembic.ini"
    assert alembic_ini.exists(), f"No se encontró alembic.ini en {alembic_ini}"

    cfg = Config(str(alembic_ini))
    script_dir = ScriptDirectory.from_config(cfg)
    heads = script_dir.get_heads()

    assert len(heads) == 1, (
        f"Alembic tiene múltiples cabezas o ninguna: {heads}. "
        "Trae origin/main y reencadena tu down_revision a su cabeza, o añade una migración de fusión "
        "si la tuya ya está aplicada en una base compartida: governance/operaciones/FUSION_ALEMBIC.md."
    )


def test_la_regla_de_fusion_que_cita_el_mensaje_existe():
    """El mensaje de fallo remite a un documento; si se mueve o se borra, la prueba lo avisa."""
    assert (RAIZ / "governance" / "operaciones" / "FUSION_ALEMBIC.md").is_file()
