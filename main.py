# ¤¤backend-developer
"""Punto de entrada principal y Pasarela REST Gateway de JUBYS Plataforma LOPDP 360.
Conecta de forma desacoplada las 7 salas ADPA con el Frontend e interfaces externas.
Invariantes: Aislamiento ADPA estricto, multi-inquilino hermético, UTF-8 sin BOM.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import datetime

from app_core.config import config

from api.middleware.limite_cuerpo import LimiteCuerpoMiddleware

logger = logging.getLogger("jubys_lopdp_json_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

# ¤jsonformatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        if hasattr(record, "request_info"):
            log_record["request"] = record.request_info
        return json.dumps(log_record)

handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

app = FastAPI(
    title="JUBYS Plataforma LOPDP 360 · API REST Gateway",
    version="1.0.0",
    description="Pasarela unificada de microservicios estancos ADPA para gobernanza de privacidad y cumplimiento LOPDP Ecuador.",
)

# ¤http_exception_handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException: {exc.detail}",
        extra={"request_info": {"method": request.method, "url": str(request.url), "status_code": exc.status_code}}
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.add_middleware(LimiteCuerpoMiddleware)  # tope de cuerpo en /preanalisis (antes de CORS: el 413 lleva cabeceras CORS)

# Configuración CORS dinámica desde config
cors_origins_list = [origin.strip() for origin in config.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro desacoplado y resiliente de enrutadores ADPA bajo /api/v1 (Mamparos Estancos)
import importlib

ROUTERS_MAP = [
    ("api.routers.diagnostico", "diagnostico"),
    ("api.routers.rat", "rat"),
    ("api.routers.riesgos_mtge", "riesgos_mtge"),
    ("api.routers.dpo_cockpit", "dpo_cockpit"),
    ("api.routers.auditoria_capa", "auditoria_capa"),
    ("api.routers.evidencias", "evidencias"),
    ("api.routers.regulacion_rag", "regulacion_rag"),
    ("api.routers.arco", "arco"),
    ("api.routers.rag_router", "rag_router"),
    ("api.routers.terceros_router", "terceros_router"),
    ("api.routers.ai_copilot", "ai_copilot"),
    ("api.routers.niif18", "niif18"),
    ("api.routers.preanalisis", "preanalisis"),
    ("api.routers.implementation_assistant", "implementation_assistant"),
]

for module_path, name in ROUTERS_MAP:
    try:
        mod = importlib.import_module(module_path)
        app.include_router(mod.router, prefix="/api/v1")
    except Exception as exc:
        logger.warning(f"Mamparo ADPA activado: router '{name}' no cargado ({exc})")



@app.get("/", tags=["Salud del Sistema"])
@app.get("/health", tags=["Salud del Sistema"])
@app.get("/api/v1/health", tags=["Salud del Sistema"])
# ¤health-check
def health_check():
    """Endpoint de verificación de estado y disponibilidad operativa de la plataforma."""
    return {
        "status": "OPERATIONAL",
        "platform": "JUBYS Plataforma LOPDP 360",
        "version": "1.0.0",
        "salas_adpa": [
            "diagnostico",
            "rat",
            "riesgos_mtge",
            "dpo_cockpit",
            "auditoria_capa",
            "evidencias",
            "regulacion_rag",
            "ai_copilot",
        ],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
