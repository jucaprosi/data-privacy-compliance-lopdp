+++
id = "GCP-11"
titulo = "Diagnóstico del arranque de la revisión 00006 de evydentia-backend"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "tests/test_gcp11_brief_solo_lectura.py"]
crea = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "tests/test_gcp11_brief_solo_lectura.py"]
arbitro = "pytest tests/test_gcp11_brief_solo_lectura.py + python scripts/generar_indice_tareas.py --verificar con código 0; el parte adjunta la salida de los comandos de solo lectura y declara la causa o «no determinada»"
rastros = ["¤despliegue"]
+++

# GCP-11 · Revisión 00006 de evydentia-backend sin escuchar en 8080

Pedido del CTO (2026-11-13). Modelo sugerido: sonnet. Libre: no depende de RET-01 ni de SEC-21. La especificación SDD la escribe el Arquitecto (`governance/especificaciones/GCP-11.md`) antes de lanzarla.

**Incidente.** La revisión 00006 del servicio `evydentia-backend` (proyecto `evydentia`, región `us-central1`) no arranca: el contenedor no empieza a escuchar en el puerto 8080 que Cloud Run espera. El `Dockerfile` arranca con `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`, así que el fallo está antes de que uvicorn abra el puerto.

**Entrega (sin código de producto).**
1. Lectura de registros con `gcloud` de **solo lectura** (nada cambia en Google Cloud): condiciones de la revisión, registros del arranque y diferencias de imagen, comando y variables con la revisión que sirve hoy.
2. Parte `governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md`: causa raíz o «no determinada», con la salida de cada comando como evidencia. Hipótesis a contrastar, en orden: una importación que falla en `main.py` o `exigir_arranque_seguro()` (SEC-15, SEC-16 y SEC-20 detienen el arranque a propósito si falta una variable o el proyecto no coincide); una variable o secreto que la revisión no recibe; una conexión a la base que bloquea el arranque; un `PORT` o un comando distinto del esperado. **Comprueba si la revisión arranca con una entrada distinta de `main:app`** (por ejemplo `api.index`): es el cruce con RET-05.
3. `governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md`: comandos pegables completos para el propietario, en PowerShell, cada bloque con su `cd` y sus variables (`$PROYECTO`, `$REGION`, `$SERVICIO`), para Antigravity. Los de lectura van primero; cualquier cambio (variable, imagen, tráfico) es un paso aparte que ejecuta solo el propietario y el brief lo marca como tal.
4. `tests/test_gcp11_brief_solo_lectura.py`: los bloques de lectura del brief no contienen verbos que cambien recursos (`deploy`, `update`, `delete`, `set-`, `add-`, `replace`, `update-traffic`).

**No hace.** No despliega, no cambia tráfico, no toca la base ni las variables. Si el diagnóstico concluye que hace falta un cambio de código, abre una ficha aparte.

