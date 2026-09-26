import re
from typing import Dict

class NERSanitizer:
    def __init__(self):
        # Mapeos de estado para asegurar anonimización consistente dentro de un mismo documento
        self._persona_map: Dict[str, str] = {}
        self._email_map: Dict[str, str] = {}
        self._cedula_map: Dict[str, str] = {}
        
        # Contadores
        self._counters = {
            "persona": 0,
            "email": 0,
            "cedula": 0
        }

    def reset_state(self):
        """Reinicia los contadores para un nuevo documento."""
        self._persona_map.clear()
        self._email_map.clear()
        self._cedula_map.clear()
        for k in self._counters:
            self._counters[k] = 0

    def _replace_email(self, match: re.Match) -> str:
        email = match.group(0)
        if email not in self._email_map:
            self._counters["email"] += 1
            self._email_map[email] = f"[EMAIL_{self._counters['email']}]"
        return self._email_map[email]

    def _replace_cedula(self, match: re.Match) -> str:
        cedula = match.group(0)
        if cedula not in self._cedula_map:
            self._counters["cedula"] += 1
            self._cedula_map[cedula] = f"[CEDULA_{self._counters['cedula']}]"
        return self._cedula_map[cedula]
        
    def _replace_persona(self, match: re.Match) -> str:
        persona = match.group(0)
        # Filtro básico para no anonimizar palabras comunes que empiecen en mayúscula al inicio de oración
        if persona.lower() in ["el", "la", "los", "las", "un", "una", "en", "por", "para"]:
            return persona
            
        if persona not in self._persona_map:
            self._counters["persona"] += 1
            self._persona_map[persona] = f"[PERSONA_{self._counters['persona']}]"
        return self._persona_map[persona]

    def sanitize(self, text: str) -> str:
        """
        Ejecuta el pipeline de sanitización (NER simulado) reemplazando PII con tokens k-anónimos.
        """
        # 1. Emails
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        text = re.sub(email_pattern, self._replace_email, text)
        
        # 2. Cédulas / DNIs (Simulado: 10 dígitos)
        cedula_pattern = r'\b\d{10}\b'
        text = re.sub(cedula_pattern, self._replace_cedula, text)
        
        # 3. Nombres Propios (Aproximación heurística: Dos palabras seguidas con mayúscula inicial)
        nombre_pattern = r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b'
        text = re.sub(nombre_pattern, self._replace_persona, text)
        
        return text

def indexar_evidencia_vectorial(document_text: str) -> str:
    """
    Simula la inserción en pgvector. Garantiza que solo el texto sanitizado
    llegue al embedding para evitar ataques de inversión vectorial.
    """
    sanitizer = NERSanitizer()
    safe_text = sanitizer.sanitize(document_text)
    
    # Aquí iría: pgvector.insert(embedding(safe_text))
    # Retornamos el texto seguro para fines de aserción en el test
    return safe_text
