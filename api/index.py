import sys
import os

# Asegurar que la raíz del proyecto esté en el sys.path para importar app_core y features
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Proveer valores por defecto en os.environ si las variables no están configuradas en Vercel
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("JWT_SECRET", "super_secret_jwt_key_for_lopdp_360_prod_fallback")

try:
    from main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="JUBYS Fallback API")
    err_trace = traceback.format_exc()
    # `e` se elimina al salir del bloque except: se guarda ahora para que el /health de emergencia pueda leerlo.
    err_detail = str(e)

    @app.get("/")
    @app.get("/health")
    @app.get("/api/v1/health")
    def fallback_health():
        return JSONResponse(
            status_code=503,
            content={
                "status": "STARTUP_ERROR",
                "error_detail": err_detail,
                "traceback": err_trace,
            },
        )

handler = app

