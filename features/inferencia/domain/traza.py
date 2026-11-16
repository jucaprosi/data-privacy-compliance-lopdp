# ¤gemini-vertex ¤arbitro
"""Traza de cada resultado de IA (IA-10, invariante 64)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Traza:
    sala: str
    tenant_id: str
    modelo_version: str  # lo que devuelve Vertex (`model_version`), nunca el alias
    modelo_solicitado: str  # el alias pedido
    prompt_id: str
    prompt_version: int
    corpus_sha256: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
