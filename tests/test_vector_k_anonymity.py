import pytest
from features.diagnostico.services.ner_sanitizer import NERSanitizer, indexar_evidencia_vectorial

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

def test_indexacion_vectorial_segura():
    """Demuestra que el texto que llega a pgvector está completamente anonimizado."""
    texto_crudo = "Reporte médico de Luis Andrade, ID 0987654321, contacto luis@med.com."
    
    vector_input = indexar_evidencia_vectorial(texto_crudo)
    
    assert "Luis Andrade" not in vector_input
    assert "0987654321" not in vector_input
    assert "luis@med.com" not in vector_input
    assert "[PERSONA_1]" in vector_input
    assert "[CEDULA_1]" in vector_input
    assert "[EMAIL_1]" in vector_input
