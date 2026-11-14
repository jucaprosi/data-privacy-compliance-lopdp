+++
id = "GCP-11"
titulo = "Diagnóstico del arranque de la revisión 00006 de evydentia-backend"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "tests/test_gcp11_brief_solo_lectura.py", "scripts/verificar_secretos_sin_bom.py", "tests/test_gcp11_secretos_sin_bom.py"]
crea = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "tests/test_gcp11_brief_solo_lectura.py", "scripts/verificar_secretos_sin_bom.py", "tests/test_gcp11_secretos_sin_bom.py"]
arbitro = "pytest tests/test_gcp11_secretos_sin_bom.py tests/test_gcp11_brief_solo_lectura.py + python scripts/generar_indice_tareas.py --verificar con código 0; el parte confirma la causa con la salida de los comandos de solo lectura; mutaciones documentadas del árbitro"
rastros = ["¤despliegue"]
+++

# GCP-11 · Revisión 00006 de evydentia-backend sin escuchar en 8080

Pedido del CTO (2026-11-13). Modelo sugerido: sonnet. Libre: no depende de RET-01 ni de SEC-21. La especificación SDD la escribe el Arquitecto (`governance/especificaciones/GCP-11.md`) antes de lanzarla. Orden de entrada: CI-27 → GCP-11 → RET-00.

**Incidente.** La revisión 00006 del servicio `evydentia-backend` (proyecto `evydentia`, región `us-central1`) no arrancaba: el contenedor no empezaba a escuchar en el puerto 8080 que Cloud Run espera. El `Dockerfile` arranca con `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`, así que el fallo estaba antes de que uvicorn abriera el puerto.

**Diagnóstico inicial (del propietario, a confirmar).** Los secretos de Secret Manager tenían una marca de orden de bytes UTF-8 (BOM) al inicio. Con su versión 2, ya sin BOM, la revisión 00007-g7q arrancó (estado verdadero, `/health` 200). La ficha lo toma como hipótesis principal y lo confirma con los registros de solo lectura; si los registros dicen otra cosa, lo declara.

**Entrega (sin tocar Google Cloud).**
1. Lectura de registros con `gcloud` de **solo lectura**: condiciones de la revisión 00006, registros del arranque y diferencias de imagen, comando y variables con la revisión 00007-g7q. Comprueba además si la revisión arrancaba con una entrada distinta de `main:app` (cruce con RET-05).
2. Parte `governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md`: causa confirmada o «no determinada», con la salida de cada comando como evidencia (sin valores de secretos).
3. **Árbitro estructural:** `scripts/verificar_secretos_sin_bom.py`, de solo lectura, comprueba que ningún secreto de la lista del entorno empieza por BOM. Lee solo los primeros tres bytes de cada versión activa, nunca imprime ni guarda el valor y falla con el nombre del secreto y la versión. `tests/test_gcp11_secretos_sin_bom.py` lo prueba con un lector doble (con BOM, sin BOM, vacío) y con mutaciones: quitar la comparación del BOM hace fallar el caso con BOM.
4. `governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md`: comandos pegables completos para el propietario, en PowerShell, cada bloque con su `cd` y sus variables, para Antigravity. Incluye el paso de **prevención**: ejecutar el árbitro antes de publicar una versión nueva de un secreto y crear las versiones sin BOM (por ejemplo, escribir el valor con `[System.IO.File]::WriteAllBytes` y una codificación UTF-8 sin BOM, nunca con redirección que la añada). Los comandos de lectura van primero; cualquier cambio es un paso aparte que ejecuta solo el propietario.
5. `tests/test_gcp11_brief_solo_lectura.py`: los bloques de lectura del brief no contienen verbos que cambien recursos (`deploy`, `update`, `delete`, `set-`, `add-`, `replace`, `update-traffic`) y ningún bloque imprime el valor de un secreto.

**No hace.** No despliega, no cambia tráfico, no crea versiones de secretos, no toca la base ni las variables. Si el diagnóstico concluye que hace falta un cambio de código, abre una ficha aparte.
