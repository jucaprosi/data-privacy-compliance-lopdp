# ¤¤backend-developer
"""Punto de entrada principal y Pasarela REST Gateway de EVYDENTIA.
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
import importlib
import pkgutil

from app_core.config import config
# === SEC-15 ===
# Guarda de arranque: con la configuración ya cargada y antes de crear la aplicación, para que falle
# también con `uvicorn main:app` y con cualquier lanzador (INV_LOPDP_HEADERS_NEVER_WITH_PRODUCTION).
from app_core.security import exigir_arranque_seguro

exigir_arranque_seguro()
# === fin SEC-15 ===
# === EP-01 ===
# Identidad y guardias del entorno de pruebas y la demo (PRD EVYDENTIA §5.5 y §5.6.2).
from app_core.entorno import entorno_actual, validar_arranque

ENTORNO = validar_arranque()
# === fin EP-01 ===
from app_core.bucle_eventos import configurar_bucle_eventos
from api.middleware.limite_cuerpo import LimiteCuerpoMiddleware
from api.errores import ErrorNegocio, error_negocio_handler

# Fijar bucle de eventos compatible con psycopg en Windows antes de instanciar app o motores
configurar_bucle_eventos()

logger = logging.getLogger("jubys_lopdp_json_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

# ¤jsonformatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        if hasattr(record, "request_info"):
            log_record["request"] = record.request_info
        return json.dumps(log_record)

handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

app = FastAPI(
    title="EVYDENTIA · API REST Gateway",
    version="1.0.0",
    description="Pasarela unificada de microservicios estancos ADPA para gobernanza de privacidad y cumplimiento LOPDP Ecuador.",
)

# ¤error_negocio_handler
app.add_exception_handler(ErrorNegocio, error_negocio_handler)

# ¤http_exception_handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException: {exc.detail}",
        extra={"request_info": {"method": request.method, "url": str(request.url), "status_code": exc.status_code}}
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# === EP-01 ===
@app.middleware("http")
async def cabecera_entorno(request: Request, call_next):
    respuesta = await call_next(request)
    if ENTORNO != "production":
        respuesta.headers["X-Entorno"] = ENTORNO
    return respuesta
# === fin EP-01 ===


# --- INICIO SEC-13 ---
# Límite de peticiones por IP, usuario y organización (tabla ventana_peticiones en Cloud SQL).
# Antes de CORS: el 429 lleva cabeceras CORS. En AUTH_MODE=headers la identidad es autodeclarada y ese
# modo nunca arranca en producción (SEC-15), así que el limitador solo se registra con identidad verificada.
from app_core.security import modo_autenticacion, MODO_HEADERS  # noqa: E402
from api.middleware.limite_peticiones import LimitePeticionesMiddleware  # noqa: E402

if modo_autenticacion() != MODO_HEADERS:
    app.add_middleware(LimitePeticionesMiddleware)
# --- FIN SEC-13 ---

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

# --- INICIO OPS-07 ---
# Observabilidad: registro JSON saneado (Cloud Logging / Error Reporting) y X-Request-ID.
# Se añade después de CORS para quedar por fuera de todo: también los 429 y 413 llevan X-Request-ID.
from app_core.observabilidad import configurar_registro
from api.middleware.correlacion import CorrelacionMiddleware

registro_ops07 = configurar_registro()
app.add_middleware(CorrelacionMiddleware, registro=registro_ops07)
# --- FIN OPS-07 ---

# Registro desacoplado y resiliente de enrutadores ADPA bajo /api/v1 (Mamparos Estancos)
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
    # === RM-21 ===
    # Va antes de roadmaps: GET /roadmaps/{roadmap_id} capturaría GET /roadmaps/hallazgos (Starlette
    # resuelve por orden de registro). Al estar aquí, AUTO_ROUTERS_MAP lo excluye y no se registra dos veces.
    ("api.routers.roadmaps_hallazgos", "roadmaps_hallazgos"),
    # === fin RM-21 ===
    # === RM-25a ===
    # Sección reservada para RM-25a (router de la primera validación de evidencia).
    ("api.routers.roadmaps_validacion", "roadmaps_validacion"),
    # === fin RM-25a ===
    ("api.routers.roadmaps", "roadmaps"),
    ("api.routers.roadmaps_informe", "roadmaps_informe"),  # RM-20
    ("api.routers.organizacion", "organizacion"),
    # === RAT-03 ===
    ("api.routers.rat_eipd", "rat_eipd"),
    # === fin RAT-03 ===
    # === MTGE-02 ===
    ("api.routers.riesgos_mtge_obligaciones", "riesgos_mtge_obligaciones"),
    # === fin MTGE-02 ===
]


def descubrir_routers_auto(paquete="api.routers", importar=importlib.import_module):
    """Descubre módulos de api.routers que declaran AUTO_REGISTRO = True."""
    auto_map = []
    mod_paquete = importar(paquete)
    if not hasattr(mod_paquete, "__path__"):
        return auto_map
    for _, modname, _ in pkgutil.iter_modules(mod_paquete.__path__):
        full_name = f"{paquete}.{modname}"
        try:
            m = importar(full_name)
            if getattr(m, "AUTO_REGISTRO", False) and hasattr(m, "router"):
                auto_map.append((full_name, modname))
        except Exception as exc:
            # Si falla la importación al inspeccionar AUTO_REGISTRO,
            # se incluye para que el cargador registre el mamparo fallido
            auto_map.append((full_name, modname))
    return auto_map


def registrar_routers(application, routers_map, importar=importlib.import_module, prefix="/api/v1"):
    """Registra cada router en su mamparo y devuelve (cargados, fallidos).

    Un router que falla al importarse no tumba la API, pero queda registrado
    para que /health lo informe: solo se conserva el tipo de la excepción
    (el mensaje va al log) porque /health es público.
    """
    cargados, fallidos = [], []
    for module_path, name in routers_map:
        try:
            mod = importar(module_path)
            application.include_router(mod.router, prefix=prefix)
            cargados.append(name)
        except Exception as exc:
            fallidos.append({"router": name, "error": type(exc).__name__})
            logger.warning(f"Mamparo ADPA activado: router '{name}' no cargado ({exc})")
    return cargados, fallidos


# 1. Registrar routers existentes de ROUTERS_MAP
ROUTERS_CARGADOS, ROUTERS_FALLIDOS = registrar_routers(app, ROUTERS_MAP)

# 2. Descubrir y registrar módulos con AUTO_REGISTRO = True
AUTO_ROUTERS_MAP = [
    item for item in descubrir_routers_auto()
    if item[0] not in [m[0] for m in ROUTERS_MAP]
]
if AUTO_ROUTERS_MAP:
    auto_cargados, auto_fallidos = registrar_routers(app, AUTO_ROUTERS_MAP)
    ROUTERS_CARGADOS.extend(auto_cargados)
    ROUTERS_FALLIDOS.extend(auto_fallidos)


def get_total_routers():
    """Devuelve la cantidad total de routers mapeados y auto-registrados."""
    return len(ROUTERS_MAP) + len(AUTO_ROUTERS_MAP)


@app.get("/", tags=["Salud del Sistema"])
@app.get("/health", tags=["Salud del Sistema"])
@app.get("/api/v1/health", tags=["Salud del Sistema"])
# ¤health-check
def health_check():
    """Endpoint de verificación de estado y disponibilidad operativa de la plataforma.

    Devuelve 503 si algún router no pudo cargarse (estado DEGRADED), para que un
    despliegue incompleto no se marque como sano; el detalle va en el cuerpo.
    """
    cuerpo = {
        "status": "OPERATIONAL" if not ROUTERS_FALLIDOS else "DEGRADED",
        "platform": "EVYDENTIA",
        "version": "1.0.0",
        "routers": {
            "total": get_total_routers(),
            "cargados": ROUTERS_CARGADOS,
            "fallidos": ROUTERS_FALLIDOS,
        },
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
    return JSONResponse(content=cuerpo, status_code=503 if ROUTERS_FALLIDOS else 200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
