# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex
"""Mapa cerrado región de Vertex → país del aviso (IA-13 R4). Una región sin etiqueta falla cerrada.

`us` es la multirregión de generación y `us-central1` la región de vectores; ambas en Estados Unidos.
Un cambio de región exige cambiar esta tabla y el aviso a la vez.
"""

UBICACION_POR_REGION: dict[str, str] = {"us": "Estados Unidos", "us-central1": "Estados Unidos"}
