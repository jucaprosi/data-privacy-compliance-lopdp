from features.diagnostico.services.ner_sanitizer import NERSanitizer

def test_sanitizer_removes_pii():
    """Valida que el sanitizador reemplaza correos, cédulas y nombres por tokens."""
    sanitizer = NERSanitizer()
    texto_crudo = "El empleado Juan Perez con cédula 1712345678 y correo juan.perez@empresa.com reportó el incidente. Luego Maria Gomez (maria@empresa.com) lo validó."
    
    texto_seguro = sanitizer.sanitize(texto_crudo)
    
    # Nombres
    assert "Juan Perez" not in texto_seguro
    assert "Maria Gomez" not in texto_seguro
    assert "[PERSONA_1]" in texto_seguro
    assert "[PERSONA_2]" in texto_seguro
    
    # Cédulas
    assert "1712345678" not in texto_seguro
    assert "[CEDULA_1]" in texto_seguro
    
    # Correos
    assert "juan.perez@empresa.com" not in texto_seguro
    assert "maria@empresa.com" not in texto_seguro
    assert "[EMAIL_1]" in texto_seguro
    assert "[EMAIL_2]" in texto_seguro
