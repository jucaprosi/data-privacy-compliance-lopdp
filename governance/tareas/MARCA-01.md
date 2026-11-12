+++
id = "MARCA-01"
titulo = "Nombre único EVYDENTIA en la plataforma: configuración, arranque, /health y contrato OpenAPI"
ola = "backlog"
estado = "hecha"
sala = "plataforma"
depende_de = ["DIAG-01", "DIAG-08", "ENT-02", "EP-01", "FIRMA-06", "MTGE-01", "MTGE-02", "OPS-03", "OPS-07", "ORG-00", "RAT-01", "RAT-02", "RAT-03", "RM-00", "RM-13", "RM-20", "RM-21", "RM-22", "SEC-11", "SEC-13", "SEC-15", "SEC-16", "SEC-17"]
propiedad = ["app_core/config.py", "main.py", "api/__init__.py", "api/index.py", "tests/test_verificar_despliegue.py", "governance/contratos/hoja_de_ruta.openapi.json", "tests/test_marca_plataforma.py"]
crea = ["tests/test_marca_plataforma.py"]
arbitro = "pytest tests/test_verificar_despliegue.py tests/test_marca_plataforma.py (GET /health devuelve platform == EVYDENTIA y el título de OpenAPI dice EVYDENTIA) + suite completa; mutación documentada: volver a JUBYS en main.py hace fallar la prueba; el contrato OpenAPI se regenera desde el router, nunca a mano"
rastros = ["¤adpa"]
+++

# MARCA-01 · Nombre único EVYDENTIA en la plataforma: configuración, arranque, /health y contrato OpenAPI

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md`, `PRD.md`, `TASKS.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- `app_core/config.py:12` (`app_name`), `main.py` líneas 2, 57 (título de OpenAPI) y 221 (`"platform"` de `/health`), **no** la línea 37 (logger); `api/__init__.py:1` y `api/index.py:19`.
- `tests/test_verificar_despliegue.py:30` cambia con su fuente. `governance/contratos/hoja_de_ruta.openapi.json` se **regenera** desde el router (título), no se edita a mano.
- **Riesgo, sin medir el lado de la nube:** `"platform"` de `/health` solo lo leen `main.py` y su prueba dentro del repo. Antes de cambiarlo, `git grep '"platform"'` en `.github/` y `scripts/`: si una comprobación de despliegue o del balanceador compara ese texto, va en el mismo PR (y si es de `.github/workflows/`, que es gobernanza reservada, se entrega el parche en el informe).
- **No es de esta ficha:** `verificadores/arnes_cero_regresiones.py:92` (gobernanza reservada: se entrega el parche y lo aplica el propietario) ni `governance/artefactos/.test_verdict.json` (lo escribe el arnés; se regenera, no se edita).
- Prueba nueva `tests/test_marca_plataforma.py`: `/health` devuelve `platform == "EVYDENTIA"`.
