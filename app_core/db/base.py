# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""Base declarativa unificada para los modelos ADPA.

Vive aparte de la sesión: declarar modelos no debe abrir ni exigir un motor de BD.
"""
from sqlalchemy.orm import declarative_base, declared_attr


class _BaseModelos:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=_BaseModelos)
