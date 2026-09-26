# -*- coding: utf-8 -*-
# ¤¤dlp_privacy_guard
"""Sanitización DLP pre-inferencia para identificadores y contactos ecuatorianos."""

import re

DLP_TOKEN = "[DATO_SANITIZADO_POR_DLP]"
_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+")
_CEDULA = re.compile(r"(?<!\w)[0-9]{10}(?!\w)")
# Formatos nacionales e internacionales. No atravesar saltos de línea ni
# sustituir una porción de identificadores numéricos más largos.
_PHONE = re.compile(
    r"(?<![\w+])(?:"
    r"\+593[ -]?9(?:[ -]?[0-9]){8}|"
    r"09(?:[ -]?[0-9]){8}|"
    r"\+593[ -]?[2-7](?:[ -]?[0-9]){7}|"
    r"0[2-7](?:[ -]?[0-9]){7}"
    r")(?!\w)"
)


# ¤validar-cedula-ecuatoriana
def validar_cedula_ecuatoriana(cedula: str) -> bool:
    """Valida una cédula ecuatoriana usando el algoritmo Módulo 10."""
    if not isinstance(cedula, str) or not re.fullmatch(r"[0-9]{10}", cedula):
        return False
    provincia = int(cedula[:2])
    if provincia not in range(1, 25) and provincia != 30:
        return False
    if int(cedula[2]) > 5:
        return False
    suma = 0
    for indice, caracter in enumerate(cedula[:9]):
        valor = int(caracter) * (2 if indice % 2 == 0 else 1)
        suma += valor - 9 if valor > 9 else valor
    return (-suma) % 10 == int(cedula[9])


# ¤sanitizar-texto-pii
def sanitizar_texto_pii(texto: str) -> str:
    """Enmascara correos, cédulas válidas y teléfonos ecuatorianos.

    No intenta identificar personas por sus nombres ni alterar referencias
    normativas. El llamador aplica esta función a todo dato enviado al proveedor.
    """
    if not texto:
        return texto

    def reemplazar_cedula(match: re.Match) -> str:
        valor = match.group(0)
        return DLP_TOKEN if validar_cedula_ecuatoriana(valor) else valor

    texto = _EMAIL.sub(DLP_TOKEN, texto)
    texto = _CEDULA.sub(reemplazar_cedula, texto)
    return _PHONE.sub(DLP_TOKEN, texto)

# ¤sanitizar-texto-dlp
def sanitizar_texto_dlp(texto: str) -> tuple[str, int]:
    """API de compatibilidad de la compuerta: texto seguro y número de reemplazos."""
    seguro = sanitizar_texto_pii(texto)
    reemplazos = (seguro or "").count(DLP_TOKEN) - (texto or "").count(DLP_TOKEN)
    return seguro, max(0, reemplazos)
