+++
id = "GCP-11"
titulo = "Diagnóstico del arranque de la revisión 00006 de evydentia-backend"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = ["FIRMA-06", "MARCA-01", "SEC-16", "SEC-17"]
propiedad = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "scripts/verificar_secretos_sin_bom.py", "tests/test_gcp11_secretos_sin_bom.py", "tests/test_gcp11_manifiesto_secretos.py", "tests/test_gcp11_brief_solo_lectura.py", "app_core/config.py#SEC-17", "tests/test_gcp11_bom_configuracion.py"]
crea = ["governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md", "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md", "scripts/verificar_secretos_sin_bom.py", "tests/test_gcp11_secretos_sin_bom.py", "tests/test_gcp11_manifiesto_secretos.py", "tests/test_gcp11_brief_solo_lectura.py", "tests/test_gcp11_bom_configuracion.py"]
arbitro = "pytest tests/test_gcp11_secretos_sin_bom.py tests/test_gcp11_manifiesto_secretos.py tests/test_gcp11_brief_solo_lectura.py tests/test_gcp11_bom_configuracion.py + python scripts/generar_indice_tareas.py --verificar con código 0; mutaciones documentadas de cada árbitro; el parte confirma la causa con la salida de los comandos de solo lectura"
rastros = ["¤versionado-despliegue"]
+++

# GCP-11 · Revisión 00006 de evydentia-backend sin escuchar en 8080

Pedido del CTO (2026-11-13). Modelo sugerido: sonnet. Libre: no depende de RET-01 ni de SEC-21. La especificación SDD la escribe el Arquitecto (`governance/especificaciones/GCP-11.md`) antes de lanzarla. Orden de entrada: CI-27 → GCP-11 → RET-00.

**Incidente.** La revisión `evydentia-backend-00006-7ks` no escuchó en el puerto 8080 que Cloud Run espera.

**Diagnóstico medido por el Arquitecto (solo lectura).** No es un fallo de puerto ni de código: el proceso terminó al importar la aplicación con `RuntimeError INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED` y el mensaje «DATABASE_URL no es de PostgreSQL» (`app_core/config.py:171`, SEC-17). La guardia falló cerrado, como debe. La revisión `00007-g7q` (misma imagen, mismos nombres de variables) funciona y recibe el 100 % del tráfico. Entre la 00005 y la 00006 cambió `JWT_SECRET_KEY` por `JWT_SECRET` y `SESSION_SECRET`. El propietario halló que los secretos de Secret Manager tenían una marca de orden de bytes UTF-8 (BOM); con su versión 2, sin BOM, la revisión arrancó (estado verdadero, `/health` 200). Un BOM al inicio rompe la comprobación del esquema `postgresql://`: es la causa probable. La entrada es `main:app`, así que no hay cruce con RET-05. La ficha confirma el diagnóstico con los registros de solo lectura y, si dicen otra cosa, lo declara.

**Entrega (sin tocar Google Cloud).**
1. Parte `governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md`: causa confirmada o «no determinada», con la salida de cada comando de lectura como evidencia (sin valores de secretos) y la comparación 00006 frente a 00007-g7q.
2. **Árbitro de secretos sin BOM, para el propietario:** `scripts/verificar_secretos_sin_bom.py`, de solo lectura. **Ninguna IA ni el CI lo ejecuta** (leer el valor exige acceso a los secretos de producción): lo ejecuta el propietario como paso del brief antes de cada despliegue. Lee solo los tres primeros bytes de cada secreto, no imprime ni registra ningún valor y devuelve solo el nombre del secreto y sí o no. `tests/test_gcp11_secretos_sin_bom.py` lo prueba con secretos simulados (con BOM, sin BOM, vacío), sin tocar Google Cloud, y con mutación: quitar la comparación del BOM hace fallar el caso con BOM.
3. **Prueba del manifiesto:** `tests/test_gcp11_manifiesto_secretos.py` comprueba, con el lector común de manifiestos (sin `import yaml`), que el manifiesto de despliegue del backend toma `DATABASE_URL` (y los secretos de sesión y de firma) de Secret Manager y no como valor en claro. Mutación: poner un valor literal hace fallar la prueba.
3b. **Complemento sin leer secretos:** `exigir_configuracion_en_la_nube` (`app_core/config.py`, SEC-17) detecta el BOM al inicio de `DATABASE_URL` y lo dice en el error («empieza por una marca de orden de bytes»), sin quitarlo en silencio ni imprimir el valor. `tests/test_gcp11_bom_configuracion.py` lo prueba y lleva mutación: quitar la detección hace fallar la prueba. La ficha posee `app_core/config.py#SEC-17` (la sección tiene marcas: `# === SEC-17 ===` y `# === fin SEC-17 ===`); no edita `tests/test_sec17_configuracion_nube.py`, que es de SEC-21. Orden en `app_core/config.py`: GCP-11 → RET-01 → RET-05.
4. **Brief para el propietario:** `governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md`, con comandos pegables completos en PowerShell (cada bloque con su `cd` y sus variables) para Antigravity: cómo se cargó `DATABASE_URL` (sin imprimir su valor) y la comprobación previa al despliegue, que ejecuta el árbitro del punto 2 y exige que el esquema empiece por `postgresql://`. Incluye la forma correcta de crear una versión de secreto sin BOM (escribir los bytes en UTF-8 sin BOM, nunca con una redirección que lo añada). Los comandos de lectura van primero; cualquier cambio es un paso aparte que ejecuta solo el propietario.
5. `tests/test_gcp11_brief_solo_lectura.py`: los bloques de lectura del brief no contienen verbos que cambien recursos (`deploy`, `update`, `delete`, `set-`, `add-`, `replace`, `update-traffic`) y ningún bloque imprime el valor de un secreto.

**No hace.** No despliega, no cambia tráfico, no crea versiones de secretos, no toca la base ni las variables. Si hace falta un cambio de código, abre una ficha aparte.
