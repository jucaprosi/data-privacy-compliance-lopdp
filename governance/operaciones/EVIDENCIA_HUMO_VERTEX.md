# Evidencia de humo de la compuerta de inferencia con Vertex AI real (IA-03b)

Estado: **pendiente de ejecución por el propietario.** Esta ficha no se marca como hecha hasta que el CTO reciba la salida y el Tech Lead la registre en la sección «Registro» de este archivo.

## 1. Qué se prueba

La compuerta `features/inferencia/inferencia_service.py` (IA-03) hace una llamada real a Gemini en Vertex AI y valida la respuesta contra dos esquemas:

- `PropuestaModelo` (`features/preanalisis/domain/models.py`)
- `PlanMitigacionResponse` (`features/ai_copilot/domain/models.py`)

La prueba es `tests/test_ia03_humo_vertex.py`. Es opt-in: sin `VERTEX_HUMO=1` se omite. Solo la ejecuta una persona; el CI no la corre.

Lo que la prueba no cubre: `gemini-2.5-pro`. El test usa únicamente `gemini-2.5-flash`. Si hace falta comprobar también `gemini-2.5-pro` en `us-central1`, es otra ficha, no esta.

## 2. Proyecto: solo el de pruebas

**Nunca el proyecto de producción.** El brief de Vertex del 2026-11-09 (`governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md`) apunta a `evydentia`, que es el proyecto de producción. Para esta evidencia se usa **el proyecto de pruebas** (`PROYECTO_PRUEBAS`, `governance/operaciones/ENTORNO_DE_PRUEBAS.md`), cuyo identificador vive solo en tus archivos locales y no se escribe en el repositorio. Si todavía no existe, el propietario lo crea primero con el procedimiento de EP-04 y no se continúa con producción.

Antes de cualquier comando, el propietario fija dos variables (sustituir los marcadores; no pegar identificadores reales aquí):

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
if ($PROYECTO -eq "evydentia") { throw "Eso es producción: no sigas con este brief." }
```

## 3. Pasos del propietario (PowerShell, copiar y pegar completos)

### Paso 1 · Comprobar el estado (solo lectura)

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
gcloud services list --enabled --project=$PROYECTO --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)"
gcloud projects get-iam-policy $PROYECTO --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$SA_BACKEND" --format="table(bindings.role)"
```

Si la API ya está habilitada o el rol ya existe, salta el paso 2 o el 3. No se da por hecho ningún estado previo.

### Paso 2 · Habilitar la API en el proyecto de pruebas

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
gcloud services enable aiplatform.googleapis.com --project=$PROYECTO
```

### Paso 3 · Rol mínimo a la cuenta de servicio de pruebas

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
gcloud projects add-iam-policy-binding $PROYECTO --member="serviceAccount:$SA_BACKEND" --role="roles/aiplatform.user" --condition=None
```

No conceder `roles/aiplatform.admin` ni `roles/owner`.

### Paso 4 · Comprobar que quedó (solo lectura)

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
gcloud services list --enabled --project=$PROYECTO --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)"
gcloud projects get-iam-policy $PROYECTO --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$SA_BACKEND AND bindings.role:roles/aiplatform.user" --format="value(bindings.role)"
```

Resultado esperado: `aiplatform.googleapis.com` y `roles/aiplatform.user`.

### Paso 5 · Credenciales para la prueba (sin claves en archivos)

Se usan credenciales de Application Default del propietario, sin descargar ninguna clave JSON. El propietario necesita poder suplantar la cuenta de pruebas (`roles/iam.serviceAccountTokenCreator` sobre ella). Si no lo tiene, para y avisa al CTO.

```powershell
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
gcloud auth application-default login --impersonate-service-account=$SA_BACKEND
```

No guardes el archivo de credenciales dentro del repositorio ni lo copies a ningún lado.

### Paso 6 · Ejecutar la prueba de humo

Desde la raíz de **tu worktree de la ficha** (no la carpeta principal del clon), con el entorno de Python del proyecto activo:

```powershell
cd "<ruta-de-tu-worktree>"
$env:GOOGLE_CLOUD_PROJECT = "<id-del-proyecto-de-pruebas>"
$env:VERTEX_LOCATION = "us-central1"
$env:VERTEX_HUMO = "1"
python -m pytest tests/test_ia03_humo_vertex.py -v
```

Si `conftest` pide una base de datos, usa la base de pruebas indicada en `herramientas\` (no la imprimas ni la copies aquí). Nunca la de producción.

Salida esperada: `2 passed`, una línea por cada esquema (`test_humo_esquema[...]`).

### Paso 7 · Guardar la evidencia (fuera del repositorio)

Copia la salida completa a un archivo local, por ejemplo `herramientas\evidencia-humo-vertex.txt`. **Antes de enviarla al CTO, sustituye el identificador del proyecto y cualquier correo por `<proyecto-de-pruebas>` y `<cuenta>`.** Este documento y la salida no deben llevar identificadores de proyecto, URL, contraseñas ni claves (ver ENTORNO_DE_PRUEBAS.md).

La salida que se pega en «Registro» no lleva identificadores de proyecto, correos ni tokens: sustitúyelos antes de pegarla.

Envíala al CTO. El Tech Lead la registra en la sección «Registro» de este archivo.

## 4. Si algo falla

- **«Permission denied» o «API not enabled»:** repite el paso 1 y revisa el 2 y el 3.
- **«Model not found»:** para y avisa al Arquitecto ADPA. No cambies de región por tu cuenta.
- **Un esquema falla la validación:** no cambies la API de la compuerta. Entrega la salida al Tech Lead, que abre una ficha de ajuste del esquema o del adaptador.

## 5. Reversión

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
$SA_BACKEND = "<cuenta-de-servicio-backend-de-pruebas>"
gcloud projects remove-iam-policy-binding $PROYECTO --member="serviceAccount:$SA_BACKEND" --role="roles/aiplatform.user"
```

La API puede quedar habilitada: no genera costo por sí sola.

## 5.1 Limpieza de la credencial suplantada

Al terminar la prueba, revoca la credencial de Application Default que creaste en el paso 5:

```powershell
gcloud auth application-default revoke
```

No copies ni conserves el archivo de credenciales fuera de su ubicación por defecto.

## 6. Registro (lo rellena el Tech Lead)

| Campo | Valor |
|---|---|
| Fecha | _pendiente_ |
| Proyecto | proyecto de pruebas (id no registrado aquí) |
| Modelo | `gemini-2.5-flash` |
| Región | `us-central1` |
| Esquema `PropuestaModelo` | _pendiente_ |
| Esquema `PlanMitigacionResponse` | _pendiente_ |
| Resultado de pytest | _pendiente_ |
| Quién ejecutó | _pendiente_ |
| Recibido por el CTO | _pendiente_ |
