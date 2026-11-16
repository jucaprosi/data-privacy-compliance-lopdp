# ¤gemini-vertex ¤arbitro
"""Prompts versionados (IA-10, invariante 64): cada texto vive bajo (id, versión) y no se edita en su lugar.

Cada sala declara los suyos en `features/<sala>/ai/prompts.py` con `VERSIONES = {1: PromptVersionado(...), ...}`
y `VIGENTE`. Las versiones anteriores no se borran. La huella sha256 de cada `(id, versión)` queda en
`evaluacion/ia/huellas_prompts.json`; cambiar un texto sin subir la versión rompe la prueba de huellas.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVersionado:
    id: str  # "<sala>.<nombre>"; la sala de la traza sale del prefijo
    version: int
    sistema: str
    plantilla: str  # se rellena con str.format_map(valores)

    @property
    def sala(self) -> str:
        return self.id.split(".", 1)[0]

    def renderizar(self, valores: dict) -> str:
        return self.plantilla.format_map(valores)


def huella(prompt: PromptVersionado) -> str:
    """sha256 del texto completo del prompt (sistema y plantilla)."""
    contenido = f"{prompt.sistema}\n---\n{prompt.plantilla}"
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def clave_huella(prompt: PromptVersionado) -> str:
    return f"{prompt.id}@{prompt.version}"


def huellas_distintas(prompts: list[PromptVersionado], registradas: dict[str, str]) -> list[str]:
    """Claves cuyo texto ya no coincide con la huella registrada (versión editada en su lugar)."""
    return sorted(
        clave_huella(p) for p in prompts if clave_huella(p) in registradas and registradas[clave_huella(p)] != huella(p)
    )


def huellas_faltantes(prompts: list[PromptVersionado], registradas: dict[str, str]) -> list[str]:
    """Claves de prompts declarados que no tienen huella registrada."""
    return sorted(clave_huella(p) for p in prompts if clave_huella(p) not in registradas)
