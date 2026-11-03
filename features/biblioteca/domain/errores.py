# ¤adpa
# ¤¤developer-architect
"""Códigos de error de negocio de Biblioteca.

Viven en la sala que los lanza y se registran en CATALOGO_ERRORES al importarse; ninguna tarea
escribe en app_core/errors.py. Cada tarea pendiente añade sus códigos solo dentro de su sección.
Los códigos de BIB-105 se quedan en app_core/errors.py.
"""
from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio


# ¤adpa
def registrar(*codigos: CodigoErrorNegocio) -> None:
    """Añade los códigos al catálogo común; un código ya registrado distinto es un error de diseño."""
    for codigo in codigos:
        previo = CATALOGO_ERRORES.get(codigo.codigo)
        if previo is not None and previo != codigo:
            raise ValueError(f"Código de error duplicado: {codigo.codigo}")
        CATALOGO_ERRORES[codigo.codigo] = codigo


# === BIB-112 ===
# Infraestructura de esta sala: registrar() y las secciones reservadas de abajo.
# === fin BIB-112 ===

# === BIB-102 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-102 ===

# === BIB-103 ===
registrar(
    CodigoErrorNegocio('BIB_PLANTILLA_NO_ENCONTRADA', 404, 'No se encontró la plantilla.'),
    CodigoErrorNegocio('BIB_COPIA_SOLO_SMARTCIDI', 422,
                       'Solo se copian las plantillas SMARTCIDI; «Mi plantilla» se edita como versión nueva.'),
)
# === fin BIB-103 ===

# === BIB-104 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-104 ===

# === BIB-106 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-106 ===

# === BIB-107 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-107 ===

# === BIB-201 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-201 ===

# === BIB-202 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-202 ===

# === BIB-203 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-203 ===

# === BIB-204 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-204 ===

# === BIB-205 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-205 ===

# === BIB-206 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-206 ===

# === BIB-207 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-207 ===

# === BIB-208 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-208 ===

# === BIB-301 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-301 ===

# === BIB-302 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-302 ===

# === BIB-303 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-303 ===

# === BIB-304 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-304 ===

# === BIB-305 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-305 ===

# === BIB-306 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-306 ===

# === BIB-401 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-401 ===

# === BIB-402 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-402 ===
