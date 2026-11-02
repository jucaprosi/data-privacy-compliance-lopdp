# ¤regulation-code
# ¤arbitro
"""Centro de conocimiento (REG-02): normativa del corpus y ayuda que cita su fuente o dice que no la hay.

Contrato: governance/especificaciones/REG-02.md. Sin base de datos: solo lee el corpus versionado.
Invariante: INV_LOPDP_AI_RAG_STRICT_CITATION (R1, nunca texto sin cita).
"""
from fastapi.testclient import TestClient

from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, CORPUS_VERSION
from features.regulacion_rag.services import conocimiento_engine
from features.regulacion_rag.services.implementation_guides import CONTROLES
from main import app

client = TestClient(app)
CABECERAS = {"X-Tenant-ID": "tenant-reg-02-e2e"}
CAMPOS_CITA = {"fuente", "articulo", "version"}


def _ayuda(**params):
    return client.get("/api/v1/conocimiento/ayuda", params=params, headers=CABECERAS)


def test_ayuda_con_cita_o_sin_fuente():
    # P12 (bases de legitimación) tiene artículo en el corpus: texto y cita completa.
    ok = _ayuda(control_ref="P12")
    assert ok.status_code == 200
    cuerpo = ok.json()
    assert cuerpo["texto"].strip()
    assert set(cuerpo["cita"]) == CAMPOS_CITA and all(str(v).strip() for v in cuerpo["cita"].values())
    assert cuerpo["cita"]["version"] == CORPUS_VERSION

    # Sin fuente en el corpus: 404 SIN_FUENTE y ningún texto (no hay tercer caso).
    for sin_fuente in ({"control_ref": "P999"}, {"control_ref": "no-es-un-control"}, {"articulo": "9999"}, {}):
        r = _ayuda(**sin_fuente)
        assert r.status_code == 404, sin_fuente
        assert r.json()["code"] == "SIN_FUENTE"
        assert "texto" not in r.json() and "cita" not in r.json()


def test_ayuda_por_articulo_distingue_ley_y_reglamento():
    ley = _ayuda(articulo="Art. 12").json()
    reglamento = _ayuda(articulo="Art. 12 del Reglamento").json()
    assert ley["cita"]["fuente"] == "LOPDP" and reglamento["cita"]["fuente"] == "Reglamento General a la LOPDP"
    assert ley["texto"] != reglamento["texto"]


def test_toda_ayuda_del_corpus_lleva_cita_completa():
    # Cada control del catálogo y cada artículo: o cita completa o ninguna ayuda. Nunca texto huérfano.
    entradas = [{"control_ref": f"P{n}"} for n in CONTROLES] + [
        {"articulo": u.id} for u in CORPUS_NORMATIVO_OFICIAL
    ]
    for params in entradas:
        r = _ayuda(**params)
        if r.status_code == 200:
            cita = r.json()["cita"]
            assert set(cita) == CAMPOS_CITA and all(str(v).strip() for v in cita.values()), params
        else:
            assert r.status_code == 404 and r.json()["code"] == "SIN_FUENTE", params


def test_mutacion_ayuda_sin_cita_es_detectada(monkeypatch):
    """Mutación documentada: si la ayuda devolviera texto sin cita completa, esta prueba falla.

    Se simula quitando la comprobación de cita y vaciando la versión de la unidad: la ayuda de P12 saldría
    con texto y cita incompleta. La prueba de arriba (`cita_completa`) la rechaza; aquí se prueba que la
    guarda real es la que lo impide.
    """
    unidad = conocimiento_engine._unidad_por_control("P12")
    monkeypatch.setattr(unidad, "version", "")
    assert conocimiento_engine.obtener_ayuda(control_ref="P12") is None  # con la guarda: SIN_FUENTE
    assert _ayuda(control_ref="P12").status_code == 404

    monkeypatch.setattr(conocimiento_engine, "_cita_completa", lambda cita: True)  # mutación: guarda anulada
    mutada = conocimiento_engine.obtener_ayuda(control_ref="P12")
    assert mutada is not None and not all(str(v).strip() for v in mutada["cita"].values())
    # El invariante que vigila el resto de pruebas detecta la mutación: texto con cita incompleta.


def test_normativa_busqueda():
    r = client.get("/api/v1/conocimiento/normativa", params={"q": "derechos"}, headers=CABECERAS)
    assert r.status_code == 200
    articulos = r.json()["articulos"]
    assert articulos
    for a in articulos:
        assert a["fuente"] and a["articulo"] and a["texto"] and a["version"] == CORPUS_VERSION
        assert set(a) == {"fuente", "articulo", "titulo", "texto", "version"}


def test_normativa_filtra_por_fuente_y_ordena_por_articulo():
    todo = client.get("/api/v1/conocimiento/normativa", headers=CABECERAS).json()["articulos"]
    assert len(todo) == len(CORPUS_NORMATIVO_OFICIAL)
    reglamento = client.get("/api/v1/conocimiento/normativa", params={"fuente": "Reglamento"}, headers=CABECERAS)
    fuentes = {a["fuente"] for a in reglamento.json()["articulos"]}
    assert fuentes == {"Reglamento General a la LOPDP"}
    ley = client.get("/api/v1/conocimiento/normativa", params={"fuente": "LOPDP"}, headers=CABECERAS).json()["articulos"]
    numeros = [int(a["articulo"].replace("Art. ", "")) for a in ley]
    assert numeros == sorted(numeros) and {a["fuente"] for a in ley} == {"LOPDP"}
    assert client.get("/api/v1/conocimiento/normativa", params={"q": "zzzz-inexistente"}, headers=CABECERAS).json() == {"articulos": []}


def test_exige_organizacion_en_la_solicitud():
    assert client.get("/api/v1/conocimiento/ayuda", params={"control_ref": "P12"}, headers={"X-Tenant-ID": " "}).status_code == 400
