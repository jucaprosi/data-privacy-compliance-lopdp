# -*- coding: utf-8 -*-
# ¤¤dlp_privacy_tests
"""
Tests para el módulo de sanitización DLP (Data Loss Prevention)
"""

import pytest
from app_core.dlp_sanitizer import validar_cedula_ecuatoriana, sanitizar_texto_pii

# ¤test-validar-cedula-ecuatoriana-valida
def test_validar_cedula_ecuatoriana_valida():
    # Cédulas de prueba (se asumen válidas según el algoritmo)
    assert validar_cedula_ecuatoriana("1710034065") == True

# ¤test-validar-cedula-ecuatoriana-invalida
def test_validar_cedula_ecuatoriana_invalida():
    # Longitud incorrecta
    assert validar_cedula_ecuatoriana("171003406") == False
    assert validar_cedula_ecuatoriana("17100340651") == False
    
    # Caracteres no numéricos
    assert validar_cedula_ecuatoriana("1710A34065") == False
    
    # Provincia inválida (00 o mayor a 24/30)
    assert validar_cedula_ecuatoriana("0010034065") == False
    assert validar_cedula_ecuatoriana("2510034065") == False
    
    # Tercer dígito mayor a 5
    assert validar_cedula_ecuatoriana("1760034065") == False
    
    # Dígito verificador incorrecto
    assert validar_cedula_ecuatoriana("1710034066") == False

# ¤test-sanitizar-texto-pii
def test_sanitizar_texto_pii():
    texto_original = "El usuario con cédula 1710034065 hizo una solicitud. La cédula falsa 1710034066 no debe enmascararse. Tampoco el número 1234567890."
    texto_esperado = "El usuario con cédula [DATO_SANITIZADO_POR_DLP] hizo una solicitud. La cédula falsa 1710034066 no debe enmascararse. Tampoco el número 1234567890."

    assert sanitizar_texto_pii(texto_original) == texto_esperado

# ¤test-sanitizar-texto-pii-sin-cedulas
def test_sanitizar_texto_pii_sin_cedulas():
    texto = "Este texto no tiene ninguna cédula."
    assert sanitizar_texto_pii(texto) == texto

# ¤test-sanitizar-texto-pii-vacio
def test_sanitizar_texto_pii_vacio():
    assert sanitizar_texto_pii("") == ""
    assert sanitizar_texto_pii(None) == None

@pytest.mark.parametrize("phone", [
    "0991234567", "099 123 4567", "09-9123-4567",
    "+593991234567", "+593 99 123 4567", "+593-99-123-4567",
    "022123456", "02-212-3456", "+593 2 212 3456",
])
# ¤test-sanitizar-telefonos-ecuador
def test_sanitizar_telefonos_ecuador(phone):
    assert sanitizar_texto_pii(f"Contacto: {phone}.") == (
        "Contacto: [DATO_SANITIZADO_POR_DLP]."
    )


# ¤test-sanitizar-email-cedula-y-telefono-en-un-mensaje
def test_sanitizar_email_cedula_y_telefono_en_un_mensaje():
    entrada = "Escribir a ana.prueba+dpd@example.test, CI 1710034065, tel. +593 99 123 4567."
    salida = sanitizar_texto_pii(entrada)
    assert salida.count("[DATO_SANITIZADO_POR_DLP]") == 3
    assert "@example.test" not in salida
    assert "1710034065" not in salida
    assert "+593" not in salida


@pytest.mark.parametrize("texto", [
    "LOPDP: artículos 7, 8, 10, 12, 37 y 47. Plazo: 15 días.",
    "Ley Orgánica de Protección de Datos Personales. Registro Oficial 459.",
    "Código interno A0991234567Z; referencia 109912345670.",
    "Fecha 2026-09-20 y resolución SPDP-SPD-2024-0001-R.",
    "09\n91234567",
])
# ¤test-dlp-conserva-referencias-normativas-y-no-coincidencias
def test_dlp_conserva_referencias_normativas_y_no_coincidencias(texto):
    assert sanitizar_texto_pii(texto) == texto


# ¤test-dlp-es-idempotente
def test_dlp_es_idempotente():
    entrada = "CI 1710034065, email ana@example.test y teléfono 0991234567"
    salida = sanitizar_texto_pii(entrada)
    assert sanitizar_texto_pii(salida) == salida


# ¤test-cedula-rechaza-numerales-no-ascii
def test_cedula_rechaza_numerales_no_ascii():
    assert not validar_cedula_ecuatoriana("١٧١٠٠٣٤٠٦٥")
