+++
id = "DEP-01"
titulo = "Dependencias de Cloud Storage y de Vertex AI en requirements.txt, con versión exacta"
ola = "backlog"
estado = "en_curso"
sala = "operaciones"
depende_de = ["BIB-205", "SEC-03"]
propiedad = ["requirements.txt", "tests/test_dep01_dependencias.py"]
crea = ["tests/test_dep01_dependencias.py"]
arbitro = "pytest tests/test_dep01_dependencias.py; mutación documentada: quitar una línea de requirements.txt"
rastros = ["¤arbitro"]
+++

# DEP-01 · Dependencias de Cloud Storage y de Vertex AI en requirements.txt, con versión exacta

Ficha de andamiaje del Arquitecto ADPA (2026-11-09). `requirements.txt` lo necesitan dos fichas de la misma tanda: EVI-01 (`app_core/storage/gcs.py`, que usa `google-cloud-storage`) e IA-03 (la compuerta de Vertex AI, que usa `google-genai`). Dos fichas sobre el mismo archivo chocan, así que lo toma esta, que va primero. EVI-01 e IA-03 dependen de ella y **no llevan `requirements.txt` en su propiedad**; no pueden pedir fusión antes de que DEP-01 esté en `main`.

## Entrega
- `google-cloud-storage==3.1.0`: la versión que ya fijó DEMO-05 en el Dockerfile de `jobs/purga_demo`; la prueba la cita.
- `google-genai==<versión exacta>`: la fija el ingeniero **tras comprobar en la documentación oficial de Google** que sustituye al SDK antiguo `vertexai.generative_models` y qué versión estable corresponde. El Arquitecto lo recordó de memoria y no lo comprobó.
- Solo esas dos líneas. No cambia ninguna otra dependencia.

## Dónde importa cada cosa
No hay código: solo `requirements.txt` y una prueba.

## Árbitro, con su mutación
- Una prueba importa los dos módulos (`google.cloud.storage` y `google.genai`).
- Otra comprueba que ambos están en `requirements.txt` con `==` (versión exacta, nunca `>=`) y que la de Cloud Storage coincide con la del Dockerfile de DEMO-05.
- Mutación: quitar una de las dos líneas deja la prueba en rojo.
