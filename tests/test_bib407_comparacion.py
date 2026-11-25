# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada ¤arbitro
"""BIB-407: comparación de una versión con la publicada del mismo código.

Árbitro sin base: la comparación es pura y el servicio se prueba con una sesión simulada que solo
responde lecturas. Cada mutación m1 a m3 de la especificación §5 tiene su prueba.
"""
import json
from datetime import date
from pathlib import Path

import pytest

from app_core.errors import ErrorNegocio
from features.biblioteca.domain import comparacion as dominio

ROOT = Path(__file__).resolve().parents[1]
CITAS = json.loads((ROOT / "data/biblioteca/pmv/citas.json").read_bytes().decode("utf-8"))
CLAVE = "LOPDP-art-7"  # verificada en citas.json
BASE = "---\nversion: 0.1.0\n---\n# Título\n\n## 1. Objeto\nTexto igual.\n\n## 2. Plazos\nQuince días.\n\n## 3. Fin\nSe va.\n"
NUEVA = ("---\nversion: 0.1.1\n---\n# Título\n\n## 1. Objeto\nTexto igual.\n\n## 2. Plazos\nQuince días hábiles.\n\n"
         "## 4. Nueva\nLlega.\n")
CAMBIOS_IA = [{"seccion": "2. Plazos", "antes": "Quince días.", "despues": "Quince días hábiles.", "cita": CLAVE}]


# --- Guardias ---

def guardia_secciones(comparar) -> list[str]:
    resultado = comparar(BASE, NUEVA, None, CITAS)
    por_titulo = {s.titulo: s for s in resultado.secciones}
    fallos = []
    if por_titulo["1. Objeto"].cambiada:
        fallos.append("una sección igual sale cambiada")
    if not por_titulo["2. Plazos"].cambiada:
        fallos.append("una sección distinta no sale cambiada")
    nueva, eliminada = por_titulo.get("4. Nueva"), por_titulo.get("3. Fin")
    if not (nueva and nueva.cambiada and nueva.cambios[0].antes == ""):
        fallos.append("la sección nueva no cuenta con «antes» vacío")
    if not (eliminada and eliminada.cambiada and eliminada.cambios[0].despues == ""):
        fallos.append("la sección eliminada no cuenta con «despues» vacío")
    return fallos


def guardia_cita(comparar) -> list[str]:
    resultado = comparar(BASE, NUEVA, CAMBIOS_IA, CITAS, lambda url: date(2026, 5, 22))
    cambio = next(s for s in resultado.secciones if s.titulo == "2. Plazos").cambios[0]
    cita = cambio.cita
    fallos = []
    if cita is None or cita.clave != CLAVE:
        return ["el cambio de la IA no lleva su cita"]
    fuente = CITAS["fuente_de"][CLAVE]
    if cita.verificada is not True or cita.norma != fuente or cita.url != CITAS["fuentes"][fuente]["url"]:
        fallos.append("la cita no se resuelve contra citas.json")
    if cita.articulo != "7" or cita.fecha_vigencia != date(2026, 5, 22):
        fallos.append("la cita no lleva artículo o fecha de vigencia")
    a_mano = comparar(BASE, NUEVA, None, CITAS)
    if any(c.cita is not None for s in a_mano.secciones for c in s.cambios):
        fallos.append("una versión cargada a mano lleva cita")
    return fallos


VERSIONES = [
    {"id": "v-retirada", "estado": "retirada", "cuerpo_md": "x"},
    {"id": "v-revision", "estado": "en_revision", "cuerpo_md": NUEVA},
]


def guardia_base(elegir) -> list[str]:
    fallos = []
    if elegir(VERSIONES, "v-revision") is not None:
        fallos.append("se compara contra una versión que no está publicada")
    con_publicada = VERSIONES + [{"id": "v-pub", "estado": "publicada", "cuerpo_md": BASE}]
    if (elegir(con_publicada, "v-revision") or {}).get("id") != "v-pub":
        fallos.append("no se compara contra la publicada")
    return fallos


# --- Reglas y mutaciones ---

def test_r2_solo_cambian_las_secciones_distintas_y_cuentan_nuevas_y_eliminadas():
    assert guardia_secciones(dominio.comparar) == []


def test_m1_marcar_todas_como_cambiadas_da_rojo():
    def todas(base, cuerpo, cambios, citas, vigencia=lambda u: None):
        r = dominio.comparar(base, cuerpo, cambios, citas, vigencia)
        return dominio.Comparacion(primera_version=False, secciones=[
            s.model_copy(update={"cambiada": True}) for s in r.secciones])
    assert "una sección igual sale cambiada" in guardia_secciones(todas)


def test_r3_cada_cambio_de_la_ia_lleva_su_cita_resuelta():
    assert guardia_cita(dominio.comparar) == []


def test_m2_devolver_la_cita_sin_resolver_da_rojo():
    def sin_resolver(base, cuerpo, cambios, citas, vigencia=lambda u: None):
        r = dominio.comparar(base, cuerpo, cambios, {}, vigencia)
        return r
    assert "la cita no se resuelve contra citas.json" in guardia_cita(sin_resolver)


def test_r1_base_publicada_y_primera_version():
    assert guardia_base(dominio.elegir_base) == []
    primera = dominio.comparar(None, NUEVA, CAMBIOS_IA, CITAS)
    assert primera.primera_version is True
    assert all(not s.cambiada and s.cambios == [] for s in primera.secciones)
    assert any(s.texto == "Quince días hábiles." for s in primera.secciones)


def test_m3_comparar_contra_una_version_retirada_da_rojo():
    def cualquiera(versiones, identificador):
        return next((v for v in versiones if v["id"] != identificador and v["estado"] != "en_revision"), None)
    assert "se compara contra una versión que no está publicada" in guardia_base(cualquiera)


# --- Servicio con sesión simulada (R4: solo lectura) ---

class _Resultado:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None

    def all(self):
        return self._filas


class SesionDeLectura:
    def __init__(self, version, del_codigo):
        self.version, self.del_codigo, self.sentencias = version, del_codigo, []

    async def execute(self, sentencia, parametros=None):
        sql = str(sentencia)
        self.sentencias.append(sql)
        if "WHERE id=:id" in sql:
            return _Resultado([self.version])
        return _Resultado(self.del_codigo)


@pytest.fixture
def servicio(monkeypatch):
    from features.biblioteca.services import comparacion_versiones as svc

    async def autorizar(session, actor, requerida=None):
        return ["revisor_tecnico"]
    monkeypatch.setattr(svc, "autorizar", autorizar)
    return svc


@pytest.mark.asyncio
async def test_r4_la_lectura_compara_la_version_de_la_ia_sin_escribir(servicio):
    version = {"id": "v-ia", "codigo": "BIB-003", "estado": "en_revision", "cuerpo_md": NUEVA,
               "redactada_por": "ia", "cambios_ia": CAMBIOS_IA}
    sesion = SesionDeLectura(version, [{"id": "v-pub", "estado": "publicada", "cuerpo_md": BASE},
                                       {"id": "v-ret", "estado": "retirada", "cuerpo_md": "otro"}, version])
    resultado = await servicio.comparar_version(sesion, "persona", "v-ia", vigencias={})
    plazos = next(s for s in resultado.secciones if s.titulo == "2. Plazos")
    assert plazos.cambiada and plazos.cambios[0].cita.verificada is True
    assert plazos.cambios[0].cita.fecha_vigencia is None  # sin NORM-07 la fecha va nula
    assert all(s.lstrip().upper().startswith("SELECT") for s in sesion.sentencias)


@pytest.mark.asyncio
async def test_sin_capacidad_no_compara(monkeypatch, servicio):
    async def sin(session, actor, requerida=None):
        return ["revisor_juridico"]
    monkeypatch.setattr(servicio, "autorizar", sin)
    with pytest.raises(ErrorNegocio) as exc:
        await servicio.comparar_version(SesionDeLectura({}, []), "p", "v")
    assert exc.value.code == "BIB_SIN_CAPACIDAD"


@pytest.mark.asyncio
async def test_sin_norm07_la_vigencia_va_nula_sin_importar_la_sala_normativa(servicio):
    import sys
    antes = {m for m in sys.modules if m.startswith("features.inteligencia_normativa")}
    fechas = await servicio._vigencias({"https://ejemplo.invalid/a.pdf"})
    assert fechas.get("https://ejemplo.invalid/a.pdf") is None
    nuevos = {m for m in sys.modules if m.startswith("features.inteligencia_normativa")} - antes
    assert nuevos == set()


def test_api_expone_la_comparacion():
    api = (ROOT / "api/routers/biblioteca_editorial.py").read_bytes().decode("utf-8")
    assert '@router.get("/versiones/{identificador}/comparacion", response_model=biblioteca.Comparacion)' in api
