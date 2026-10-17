+++
id = "SEC-05"
titulo = "Validación de evidencia en el servidor y diseño del antivirus"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-04", "RM-00"]
propiedad = ["app_core/storage/r2.py", "app_core/errors.py", "api/routers/roadmaps.py", "tests/test_evidencia_validacion_servidor.py", "governance/arquitectura/ANTIVIRUS_EVIDENCIA_BOCETO.md"]
arbitro = "pytest tests/test_evidencia_validacion_servidor.py + suite completa; el boceto lo aprueba el propietario"
rastros = ["¤seguridad", "¤evidencias"]
+++

# SEC-05 · Validación de evidencia en el servidor y diseño del antivirus

**Objetivo.** FE-04 restringe la extensión y el tamaño solo en la interfaz, y `app_core/storage/r2.py` no valida tipo ni tamaño al generar la URL de subida. La evidencia se descarga después, así que un archivo malicioso o desmesurado pasa. No existe antivirus en el repositorio.

## Entrega
- Lista blanca de tipos y tamaño máximo definidos en un único lugar del servidor, alineados con `frontend/src/components/modules/roadmap/evidencia/reglas.ts` (la interfaz sigue siendo una ayuda; decide el servidor). Se aplica al pedir la URL de subida y al registrar la evidencia, y el rechazo usa `ErrorNegocio` con un código nuevo del catálogo `app_core/errors.py`.
- Boceto (BBAP, paso 1) `ANTIVIRUS_EVIDENCIA_BOCETO.md`. El servidor no ve el archivo (sube directo a R2), así que el escaneo solo puede ser posterior a la subida. Evalúa las opciones (escáner externo por API, función con ClamAV y por qué es difícil en el plan gratuito de Vercel, cuarentena y estado «pendiente de análisis» de la evidencia) con límites y costos verificados en la documentación oficial, con fecha; lo demás va como «no verificado». Sin proveedor real ni credenciales. Termina con las decisiones que necesita el propietario.

## Límites
- No integra ningún escáner ni cambia el modelo de datos de la evidencia: si el diseño lo exige, lo propone como tarea.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
