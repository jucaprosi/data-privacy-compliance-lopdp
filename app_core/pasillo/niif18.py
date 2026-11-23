# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala NIIF 18 para otras salas."""


def contexto_doctrinal() -> str:
    from features.niif18 import niif18_service

    return niif18_service.NIIF18DoctrineService().get_doctrine_context()
