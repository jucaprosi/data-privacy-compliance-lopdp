# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""IA-09: ubicación real desde la compuerta de inferencia, propagación de org_id y textos sin encuadre.

Mutaciones verificadas:
  M1. Etiqueta de ubicación cableada en el router o en `proveedor.py`
      -> test_ubicacion_sale_de_la_compuerta (cambia `UBICACION_POR_REGION` y espera el nuevo texto).
  M2. Pasar `None` o no propagar `tenant_id` desde el router / `analizar_control` hasta `ProveedorVertex.proponer`
      -> test_org_llega_al_proveedor.
  M4 (IA-13 m2). Aceptar una ubicación sin etiqueta en `UBICACION_POR_REGION`
      -> test_ia13_multirregion_us.
  M3. Escribir un país (p. ej. "Estados Unidos"), proveedor/modelo en frontend, o frases de encuadre/provisional
      -> test_sin_ubicacion_ni_encuadre_escritos_a_mano (con mutaciones verificadas en memoria).
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from features.evidencias.domain.models import EvidenciaRegistro
from features.evidencias.services.evidencias_engine import registrar_evidencia
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELO_GENERACION
from features.inferencia.domain.regiones import UBICACION_POR_REGION
from features.inferencia.services import cliente_vertex
from features.preanalisis.domain.models import ControlContexto, Fragmento, ProveedorNoDisponible
from features.preanalisis.preanalisis_service import analizar_control, inyectar_proveedor_de_prueba, restablecer_proveedor_entorno
from features.preanalisis.services import proveedor as mod
from main import app

RAIZ = Path(__file__).resolve().parents[1]
URL = "/api/v1/preanalisis"
PROYECTO = "proyecto-ia09-simulado"
HDR_ESTADO = {"X-Tenant-ID": "tenant-ia09"}
TENANT_ANALIZAR = "tenant-ia09-org"
HDR_ANALIZAR = {"X-Tenant-ID": TENANT_ANALIZAR, "X-User-ID": "admin-ia09", "X-Role": "admin_organizacion"}

ARCHIVOS_PRODUCCION_IA09: tuple[str, ...] = (
    "features/preanalisis/domain/models.py",
    "features/preanalisis/services/proveedor.py",
    "features/preanalisis/preanalisis_service.py",
    "api/routers/preanalisis.py",
    "frontend/src/lib/preanalisis/tipos.ts",
    "frontend/src/lib/preanalisis/cliente.ts",
    "frontend/src/components/preanalisis/ConsentimientoEnvio.tsx",
    "frontend/src/components/preanalisis/PanelPreanalisis.tsx",
)

CITA_VALIDA = "La organización designó formalmente a un Delegado de Protección de Datos"
TEXTO_FRAGMENTO = f"{CITA_VALIDA}."
CONTROL_DIC = {
    "control_id": 5,
    "control": "Delegado de Protección de Datos",
    "enunciado": "Se ha designado un Delegado de Protección de Datos",
    "evidencia_esperada": "Resolución de designación",
    "referencia_normativa": "LOPDP art. 48",
    "dimension": "D01",
    "fragmentos": [{"texto": TEXTO_FRAGMENTO, "origen": "p. 1"}],
}


class _ModelosFalsos:
    def __init__(self) -> None:
        self.llamadas: list[dict] = []

    async def generate_content(self, **kw):  # noqa: ANN003
        self.llamadas.append(kw)
        return SimpleNamespace(
            text=json.dumps({
                "estado": "Conforme",
                "citas": [{"fragmento": CITA_VALIDA, "motivo": "Constancia documental"}],
                "razonamiento": "Sustentado en el fragmento.",
            })
        )


@pytest.fixture()
def entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    consumos: list[str] = []

    async def consumir(org_id: str) -> None:
        consumos.append(org_id)

    for var in ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION", "VERTEX_LOCATION_EMBEDDING"):
        monkeypatch.delenv(var, raising=False)
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(consumir)
    restablecer_proveedor_entorno()
    try:
        yield consumos
    finally:
        svc.inyectar_cliente_de_prueba(None)
        svc.inyectar_consumidor_de_prueba(None)
        restablecer_proveedor_entorno()


def test_ubicacion_sale_de_la_compuerta(entorno_limpio: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """M1: la ubicación sale de la compuerta y cambia dinámicamente al cambiar UBICACION_POR_REGION."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROYECTO)
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    with TestClient(app) as client:
        r_us = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_us.status_code == 200
        assert r_us.json()["ubicacion"] == "Estados Unidos" and r_us.json()["region"] == "us"

        # Otra región en el mapa de regiones debe devolver su propia etiqueta.
        monkeypatch.setitem(UBICACION_POR_REGION, "europe-west1", "Irlanda")
        monkeypatch.setenv("VERTEX_LOCATION", "europe-west1")
        r_ie = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_ie.status_code == 200
        assert r_ie.json()["ubicacion"] == "Irlanda" and r_ie.json()["region"] == "europe-west1"

        # Mutación en memoria del mapa para verificar que `us` no está cableado en router ni proveedor.
        monkeypatch.setitem(UBICACION_POR_REGION, "us", "Canadá")
        monkeypatch.setenv("VERTEX_LOCATION", "us")
        r_mut = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_mut.status_code == 200
        assert r_mut.json()["ubicacion"] == "Canadá" and r_mut.json()["region"] == "us"

        # Proveedor inyectado sin atributo `ubicacion` -> None.
        class _ProveedorSinUbicacion:
            nombre = "falso"
            modelo = "m-1"

            async def proponer(self, sistema: str, usuario: str):  # noqa: ANN001
                raise NotImplementedError

        inyectar_proveedor_de_prueba(_ProveedorSinUbicacion())
        r_sin_attr = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_sin_attr.status_code == 200
        assert r_sin_attr.json()["ubicacion"] is None and r_sin_attr.json()["region"] is None

        restablecer_proveedor_entorno()
        # Compuerta disponible pero sin etiqueta de ubicación -> None.
        monkeypatch.setattr(
            mod.pasillo_inferencia,
            "estado",
            lambda: SimpleNamespace(disponible=True, proveedor="vertex-ai", modelo=None, motivo=None, ubicacion=None, region=None),
        )
        r_sin_ubic = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_sin_ubic.status_code == 200
        assert r_sin_ubic.json()["ubicacion"] is None and r_sin_ubic.json()["region"] is None

        # Compuerta no disponible -> disponible=False y ubicacion=None.
        monkeypatch.setattr(
            mod.pasillo_inferencia,
            "estado",
            lambda: SimpleNamespace(disponible=False, proveedor=None, modelo=None, motivo="No disponible", ubicacion=None, region=None),
        )
        r_off = client.get(f"{URL}/estado", headers=HDR_ESTADO)
        assert r_off.status_code == 200
        assert r_off.json()["disponible"] is False
        assert r_off.json()["ubicacion"] is None and r_off.json()["region"] is None


def test_org_llega_al_proveedor(entorno_limpio: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """M2: POST /analizar propaga tenant_id hasta ProveedorVertex.proponer(..., org_id=tenant_id) y None falla cerrado."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROYECTO)
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    modelos = _ModelosFalsos()
    svc.inyectar_cliente_de_prueba(SimpleNamespace(aio=SimpleNamespace(models=modelos)))

    orgs_en_proponer: list[str | None] = []
    proponer_original = mod.ProveedorVertex.proponer

    async def _espia_proponer(self, sistema: str, usuario: str, *, org_id: str | None = "preanalisis"):
        orgs_en_proponer.append(org_id)
        return await proponer_original(self, sistema, usuario, org_id=org_id)

    monkeypatch.setattr(mod.ProveedorVertex, "proponer", _espia_proponer)

    registrar_evidencia(
        EvidenciaRegistro(
            tenant_id=TENANT_ANALIZAR,
            nombre_archivo="designacion.pdf",
            sha256_hash=uuid.uuid4().hex * 2,
            controles_vinculados=[CONTROL_DIC["control_id"]],
        )
    )

    from api.rbac import get_context

    app.dependency_overrides[get_context] = lambda: {
        "tenant_id": TENANT_ANALIZAR,
        "user_id": HDR_ANALIZAR["X-User-ID"],
        "role": HDR_ANALIZAR["X-Role"],
    }
    try:
        with TestClient(app) as client:
            resp = client.post(f"{URL}/analizar", json=CONTROL_DIC, headers=HDR_ANALIZAR)
    finally:
        app.dependency_overrides.pop(get_context, None)

    assert resp.status_code == 200, resp.text
    assert orgs_en_proponer == [TENANT_ANALIZAR]
    assert entorno_limpio == [TENANT_ANALIZAR]
    assert len(modelos.llamadas) == 1

    # Llamada directa sin tenant_id (None o vacío): falla cerrado sin llamar a la compuerta ni consumir tope.
    ctx = ControlContexto(
        control_id=CONTROL_DIC["control_id"],
        control=CONTROL_DIC["control"],
        enunciado=CONTROL_DIC["enunciado"],
        evidencia_esperada=CONTROL_DIC["evidencia_esperada"],
        referencia_normativa=CONTROL_DIC["referencia_normativa"],
    )
    frags = [Fragmento(texto=TEXTO_FRAGMENTO, origen="p. 1")]
    for invalido in (None, "", "   "):
        with pytest.raises(ProveedorNoDisponible):
            asyncio.run(analizar_control(ctx, frags, invalido))
    assert entorno_limpio == [TENANT_ANALIZAR]
    assert len(modelos.llamadas) == 1


_LITERALES_PAIS = ("estados unidos", "irlanda", "united states", "ee. uu.", "eeuu")
_FRASES_ENCUADRE_GENERALES = (
    "garantías adecuadas",
    "garantias adecuadas",
    "transferencia conforme",
    "transferencia internacional",
    "adecuad",
    "provisional",
    "por confirmar",
)
_ARCHIVOS_SIN_PROVEEDOR_NI_MODELO = {
    "api/routers/preanalisis.py",
    "frontend/src/lib/preanalisis/tipos.ts",
    "frontend/src/lib/preanalisis/cliente.ts",
    "frontend/src/components/preanalisis/ConsentimientoEnvio.tsx",
    "frontend/src/components/preanalisis/PanelPreanalisis.tsx",
}
_ARCHIVOS_SIN_CONFORME_LITERAL = {
    "features/preanalisis/services/proveedor.py",
    "api/routers/preanalisis.py",
    "frontend/src/lib/preanalisis/cliente.ts",
    "frontend/src/components/preanalisis/ConsentimientoEnvio.tsx",
    "frontend/src/components/preanalisis/PanelPreanalisis.tsx",
}
_CADENAS_TSX = re.compile(r"(?<=>)([^<>{}]+)(?=[<{])|\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\]|\\.)*)`")
_ARTICULO_LEGAL = re.compile(r"\bart\.?\s*\d+", re.IGNORECASE)


def _cadenas_visibles_o_literales(contenido: str) -> str:
    trozos = []
    for match in _CADENAS_TSX.finditer(contenido):
        texto = next((g for g in match.groups() if g is not None), "")
        if texto.strip():
            trozos.append(texto)
    return "\n".join(trozos)


def _buscar_prohibidos_ia09(ruta_relativa: str, contenido: str) -> list[str]:
    bajo = contenido.lower()
    hallazgos: list[str] = []

    for pais in _LITERALES_PAIS:
        if pais in bajo:
            hallazgos.append(f"{ruta_relativa}: país prohibido {pais!r}")

    for frase in _FRASES_ENCUADRE_GENERALES:
        if frase in bajo:
            hallazgos.append(f"{ruta_relativa}: frase prohibida {frase!r}")

    if not ruta_relativa.endswith((".tsx", ".ts")):
        # IA-17 R1: ni el prefijo «servidores» ni una región escrita a mano en el código de la sala.
        if "servidores" in bajo:
            hallazgos.append(f"{ruta_relativa}: encuadre «servidores» escrito a mano")
        if re.search(r"[\"'](?:us|us-central1|europe-west1)[\"']", bajo):
            hallazgos.append(f"{ruta_relativa}: región escrita a mano")

    if "PENDIENTE" in contenido:
        hallazgos.append(f"{ruta_relativa}: marcador provisional 'PENDIENTE'")

    if ruta_relativa in _ARCHIVOS_SIN_CONFORME_LITERAL:
        if "conforme" in bajo:
            hallazgos.append(f"{ruta_relativa}: contiene 'conforme'")
    else:
        # En modelos/tipos/prompt solo existen los valores de estado 'Conforme' y 'No Conforme'.
        sin_estados = re.sub(r"[\"'](?:No )?Conforme[\"']|proponer Conforme", "", contenido)
        if "conforme" in sin_estados.lower():
            hallazgos.append(f"{ruta_relativa}: contiene 'conforme' fuera del estado del dominio")

    if ruta_relativa.endswith(".tsx"):
        cadenas = _cadenas_visibles_o_literales(contenido)
        if "cumple" in cadenas.lower():
            hallazgos.append(f"{ruta_relativa}: texto visible o literal contiene 'cumple'")
        if "pendiente" in cadenas.lower():
            hallazgos.append(f"{ruta_relativa}: texto visible o literal contiene 'pendiente'")
        if _ARTICULO_LEGAL.search(cadenas):
            hallazgos.append(f"{ruta_relativa}: texto visible cita un artículo legal")
    else:
        if "cumple" in bajo:
            hallazgos.append(f"{ruta_relativa}: contiene 'cumple'")

    if ruta_relativa in _ARCHIVOS_SIN_PROVEEDOR_NI_MODELO:
        for marca in ("vertex", "google", "gemini"):
            if marca in bajo:
                hallazgos.append(f"{ruta_relativa}: literal de proveedor/modelo {marca!r}")

    return hallazgos


def test_sin_ubicacion_ni_encuadre_escritos_a_mano() -> None:
    """M3: ningún archivo de producción de IA-09 escribe países, encuadres legales ni marcadores provisionales."""
    hallazgos: list[str] = []
    contenidos: dict[str, str] = {}
    for rel in ARCHIVOS_PRODUCCION_IA09:
        texto = (RAIZ / rel).read_text(encoding="utf-8")
        contenidos[rel] = texto
        hallazgos.extend(_buscar_prohibidos_ia09(rel, texto))
    assert hallazgos == [], "\n".join(hallazgos)

    # Verificación de mutaciones en memoria: cada cadena prohibida debe hacer saltar la guardia.
    consentimiento = "frontend/src/components/preanalisis/ConsentimientoEnvio.tsx"
    base_tsx = contenidos[consentimiento]
    ancla = "El documento completo no se envía."
    assert ancla in base_tsx
    for mutacion in (
        "Estados Unidos",
        "garantías adecuadas",
        "transferencia conforme",
        "conforme",
        "adecuado",
        "cumple",
        "provisional",
        "por confirmar",
        "PENDIENTE",
        "Google Vertex AI",
        MODELO_GENERACION,
        "art. 60",
    ):
        mutado = base_tsx.replace(ancla, f"{mutacion} {ancla}", 1)
        assert _buscar_prohibidos_ia09(consentimiento, mutado), f"Mutación no detectada: {mutacion!r}"

    proveedor = "features/preanalisis/services/proveedor.py"
    assert _buscar_prohibidos_ia09(proveedor, contenidos[proveedor] + '\n"Estados Unidos"\n')
    assert _buscar_prohibidos_ia09(proveedor, contenidos[proveedor] + '\nf"servidores en {x}"\n')
    assert _buscar_prohibidos_ia09(proveedor, contenidos[proveedor] + '\nREGION = "us"\n')
    router = "api/routers/preanalisis.py"
    assert _buscar_prohibidos_ia09(router, contenidos[router] + '\n"Estados Unidos"\n')
    assert _buscar_prohibidos_ia09(router, contenidos[router] + '\nregion = "us"\n')


def test_ia13_multirregion_us(entorno_limpio: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """IA-13 R2 y R4, M4: `us` llega al SDK y al estado; una ubicación sin etiqueta falla cerrada."""
    capturado: dict = {}

    class _ClienteFalso:
        def __init__(self, **kw):  # noqa: ANN003
            capturado.update(kw)

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", _ClienteFalso)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROYECTO)
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    cliente_vertex.crear_cliente()
    assert capturado["location"] == "us" and "api_key" not in capturado
    e = svc.estado()
    assert e.disponible and e.region == "us" and e.ubicacion == "Estados Unidos"
    assert UBICACION_POR_REGION == {"us": "Estados Unidos", "us-central1": "Estados Unidos"}

    # M4: una ubicación sin etiqueta no se acepta.
    monkeypatch.setenv("VERTEX_LOCATION", "europe-west1")
    assert not svc.estado().disponible
    with pytest.raises(InferenciaNoDisponible):
        svc._region_valida()
