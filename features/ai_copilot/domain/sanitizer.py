# ¤¤llm_data_sanitizer
"""Redacción de datos de entrada antes de enviarlos al proveedor de inferencia."""

import re
from typing import Any, Dict

from app_core.app_service import sanitizar_texto_pii


# ¤llm-data-sanitizer
class LLMDataSanitizer:
    # La heurística de nombres no debe destruir términos normativos o procesos.
    # No equivale a un reconocedor universal de entidades personales.
    _LEGAL_WORDS = {
        "ley", "orgánica", "orgánico", "reglamento", "general", "protección",
        "datos", "personales", "delegado", "delegada", "autoridad",
        "superintendencia", "registro", "oficial", "asamblea", "nacional",
        "artículo", "consentimiento", "responsable", "encargado", "tratamiento",
        "evaluación", "impacto", "derechos", "política", "seguridad",
        "constitución", "república", "riesgos", "derecho", "interés", "legítimo",
    }

    def __init__(self):
        self._email_map: Dict[str, str] = {}
        self._ip_map: Dict[str, str] = {}
        self._empresa_map: Dict[str, str] = {}
        self._persona_map: Dict[str, str] = {}
        self._counters = {"email": 0, "ip": 0, "empresa": 0, "persona": 0}

    def _replace_email(self, match: re.Match) -> str:
        email = match.group(0)
        if email not in self._email_map:
            self._counters["email"] += 1
            self._email_map[email] = f"[EMAIL_{self._counters['email']}]"
        return self._email_map[email]

    def _replace_ip(self, match: re.Match) -> str:
        ip = match.group(0)
        if ip not in self._ip_map:
            self._counters["ip"] += 1
            self._ip_map[ip] = f"[IP_{self._counters['ip']}]"
        return self._ip_map[ip]

    def _replace_empresa(self, match: re.Match) -> str:
        empresa = match.group(0)
        if empresa not in self._empresa_map:
            self._counters["empresa"] += 1
            self._empresa_map[empresa] = f"[EMPRESA_{self._counters['empresa']}]"
        return self._empresa_map[empresa]

    def _replace_persona(self, match: re.Match) -> str:
        persona = match.group(0)
        if any(word.lower() in self._LEGAL_WORDS for word in persona.split()):
            return persona
        if persona not in self._persona_map:
            self._counters["persona"] += 1
            self._persona_map[persona] = f"[PERSONA_{self._counters['persona']}]"
        return self._persona_map[persona]

    def sanitize_text(self, text: str) -> str:
        if not text:
            return text

        # Conserva tokens estables para el contexto dentro de la misma petición.
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+"
        text = re.sub(email_pattern, self._replace_email, text)
        text = sanitizar_texto_pii(text)
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        text = re.sub(ip_pattern, self._replace_ip, text)

        empresa_pattern = (
            r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ ]+"
            r"(?:S\.A\.|C\.A\.|Inc\.?|LLC|Corp\.?)(?=\W|$)"
        )
        text = re.sub(empresa_pattern, self._replace_empresa, text)
        nombre_pattern = r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+[ ]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b"
        return re.sub(nombre_pattern, self._replace_persona, text)

    def sanitize_value(self, value: Any) -> Any:
        """Sanitiza valores de JSON a cualquier profundidad sin mutar la entrada."""
        if isinstance(value, str):
            return self.sanitize_text(value)
        if isinstance(value, dict):
            return {key: self.sanitize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.sanitize_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.sanitize_value(item) for item in value)
        return value

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza recursivamente todos los valores string de un diccionario."""
        return self.sanitize_value(data)
