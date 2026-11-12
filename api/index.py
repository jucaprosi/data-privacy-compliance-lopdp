import sys
import os

# Asegurar que la raíz del proyecto esté en el sys.path para importar app_core y features
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# SEC-16 y SEC-17: aquí no se pone ningún valor por defecto. app_core.config conserva los de desarrollo
# fuera de la nube; en la nube, si falta un secreto, DATABASE_URL o CORS_ORIGINS, impide el arranque y
# se sirve la API de emergencia (503 STARTUP_ERROR) en lugar de arrancar abierto.

try:
    from main import app
except Exception as e:
    import logging
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="EVYDENTIA Fallback API")
    # El detalle (mensaje y traceback) va solo al log del despliegue: /health es público
    # y un traceback revela rutas del servidor y nombres de configuración.
    logging.getLogger("jubys.arranque").exception("Fallo al importar la aplicación; se sirve la API de emergencia")
    # `e` se elimina al salir del bloque except: se guarda ahora el tipo para el cuerpo.
    err_tipo = type(e).__name__

    @app.get("/")
    @app.get("/health")
    @app.get("/api/v1/health")
    def fallback_health():
        return JSONResponse(
            status_code=503,
            content={"status": "STARTUP_ERROR", "error": err_tipo},
        )

handler = app

