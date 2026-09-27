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

from api.routers.diagnostico import router as diagnostico_router
from api.routers.rat import router as rat_router
from api.routers.riesgos_mtge import router as riesgos_mtge_router
from api.routers.dpo_cockpit import router as dpo_cockpit_router
from api.routers.auditoria_capa import router as auditoria_capa_router
from api.routers.evidencias import router as evidencias_router
from api.routers.regulacion_rag import router as regulacion_rag_router
from api.routers.arco import router as arco_router
from api.routers.rag_router import router as rag_router_new
from api.routers.terceros_router import router as terceros_router
from api.routers.ai_copilot import router as ai_copilot_router
from api.routers.niif18 import router as niif18_router
from api.routers.preanalisis import router as preanalisis_router
from api.routers.implementation_assistant import router as implementation_assistant_router
from api.middleware.limite_cuerpo import LimiteCuerpoMiddleware

logger = logging.getLogger("jubys_lopdp_json_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
# Simple structured JSON logging
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

# Exception handler for unhandled HTTP exceptions with JSON logging
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

# Registro de enrutadores ADPA bajo el prefijo /api/v1
app.include_router(diagnostico_router, prefix="/api/v1")
app.include_router(rat_router, prefix="/api/v1")
app.include_router(riesgos_mtge_router, prefix="/api/v1")
app.include_router(dpo_cockpit_router, prefix="/api/v1")
app.include_router(auditoria_capa_router, prefix="/api/v1")
app.include_router(evidencias_router, prefix="/api/v1")
app.include_router(regulacion_rag_router, prefix="/api/v1")
app.include_router(arco_router, prefix="/api/v1")
app.include_router(rag_router_new, prefix="/api/v1")
app.include_router(terceros_router, prefix="/api/v1")
app.include_router(ai_copilot_router, prefix="/api/v1")
app.include_router(niif18_router, prefix="/api/v1")
app.include_router(preanalisis_router, prefix="/api/v1")
app.include_router(implementation_assistant_router, prefix="/api/v1")


@app.get("/", tags=["Salud del Sistema"])
@app.get("/health", tags=["Salud del Sistema"])
@app.get("/api/v1/health", tags=["Salud del Sistema"])
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
