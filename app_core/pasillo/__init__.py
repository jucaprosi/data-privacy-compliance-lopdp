# ¤adpa
"""Pasillo central entre salas (ADPA §3, ADR 0001).

Una sala nunca importa a otra: llama a estas funciones, que invocan la compuerta proveedora.
Cada función importa la compuerta en su cuerpo para no formar un ciclo de importación, comparte
la `session` de quien llama y devuelve datos propios, nunca tipos internos de la sala. Aquí no
hay lógica de negocio.
"""
