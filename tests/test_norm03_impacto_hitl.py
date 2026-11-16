# ¤inteligencia-normativa ¤copiloto-ia ¤vertex-cache ¤dpo-independencia ¤arbitro
"""NORM-03: análisis de impacto de una resolución con modelo simulado, decidido solo por el DPO.

PostgreSQL local con las migraciones aplicadas; modelo, lector de originales y catálogo, dobles. Sin red real.
Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
import hashlib
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa.services import extraccion

pytestmark = pytest.mark.asyncio

NOTA = "Revisado por el DPO contra el texto."
RUTA = "spdp/norm03.pdf"
SHA = "a" * 64
CATALOGO = [
    {"tipo": "pregunta", "referencia_id": "P12", "nombre": "Aviso de privacidad"},
    {"tipo": "tratamiento", "referencia_id": "rat-uno", "nombre": "RAT-01 Nómina"},
]


def pdf_con_texto(lineas: list[str]) -> bytes:
    """PDF mínimo de una página con Helvetica; pypdf lo lee aunque las posiciones sean aproximadas."""
    flujo = "BT /F1 11 Tf 40 780 Td 14 TL " + " ".join(f"({t}) Tj T*" for t in lineas) + " ET"
    objetos = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(flujo)} >>\nstream\n{flujo}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = b"%PDF-1.4\n"
    posiciones = []
    for i, o in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += b"".join(f"{p:010d} 00000 n \n".encode() for p in posiciones)
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return salida


PDF = pdf_con_texto([
    "Resolucion de prueba sobre avisos de privacidad.",
    "Articulo 5. El responsable publica un aviso de privacidad claro.",
    "Art. 7. El responsable conserva el registro de actividades.",
])


class LectorEnMemoria:
    def __init__(self, objetos):
        self.objetos = objetos

    def leer(self, clave):
        return self.objetos.get(clave)


class CatalogoFijo:
    async def elementos(self, sesion, tenant_id, user_id):
        return CATALOGO


def modelo_simulado(elementos):
    """Doble del modelo: devuelve `elementos` y cuenta las llamadas."""
    llamadas = []

    async def analizar(texto, catalogo, org_id):
        llamadas.append((texto, catalogo, org_id))
        return elementos, None

    analizar.llamadas = llamadas
    return analizar


ELEMENTOS_CON_SUSTENTO = [
    {"tipo": "pregunta", "referencia_id": "P12", "motivo": "El aviso debe ser claro.",
     "articulos_citados": ["Art. 5"]},
    {"tipo": "tratamiento", "referencia_id": "rat-uno", "motivo": "El registro se conserva.",
     "articulos_citados": ["Artículo 7"]},
]


@pytest_asyncio.fixture
async def mundo(db_engine):
    f = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t-n03a-{sufijo}", f"t-n03b-{sufijo}"
    usuarios = {k: f"u-n03-{k}-{sufijo}" for k in ("dpo_a", "adm_a", "dpo_b")}
    resolucion = str(uuid.uuid4())
    async with f() as s:
        for t in (ta, tb):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:t, :t, :t, :ruc)"), {"t": t, "ruc": f"RUC{uuid.uuid4().hex[:12]}"})
        for clave, uid in usuarios.items():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                            {"i": uid, "e": f"{uid}@test.local", "n": clave})
        for clave, tenant, rol in (("dpo_a", ta, "dpo"), ("adm_a", ta, "admin_organizacion"), ("dpo_b", tb, "dpo")):
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                {"i": f"r-{uuid.uuid4().hex[:10]}", "u": usuarios[clave], "t": tenant, "r": rol})
        await s.execute(
            text("INSERT INTO normativa_resoluciones (id, numero_resolucion, anio_emision, titulo, url_fuente, "
                 "seccion_fuente, archivo_sha256, ruta_original, tamano_bytes) VALUES "
                 "(CAST(:i AS uuid), :n, 2026, 'Resolución de prueba', 'https://spdp.test/x', 'resoluciones', "
                 ":h, :r, :b)"),
            {"i": resolucion, "n": f"N03-{sufijo}", "h": SHA, "r": RUTA, "b": len(PDF)})
        await s.commit()
    svc.inyectar_dependencias_de_prueba(sesion_factory=f)
    svc.inyectar_lector_de_prueba(LectorEnMemoria({RUTA: PDF}))
    yield {"f": f, "ta": ta, "tb": tb, "u": usuarios, "resolucion": resolucion}
    svc.inyectar_dependencias_de_prueba()
    svc.inyectar_lector_de_prueba()
    svc.inyectar_dependencias_de_impacto_de_prueba()
    async with f() as s:
        ids = [ta, tb]
        for t in ids:
            await fijar_contexto_rls(s, t)
            await s.execute(text("DELETE FROM hallazgos WHERE tenant_id = :t"), {"t": t})
            await s.execute(text("DELETE FROM normativa_analisis_impacto WHERE tenant_id = :t"), {"t": t})
            await s.commit()
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id = ANY(:i)"), {"i": ids})
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = ANY(:i)"), {"i": ids})
        await s.execute(text("DELETE FROM users WHERE id = ANY(:i)"), {"i": list(usuarios.values())})
        await s.execute(text("DELETE FROM tenants WHERE id = ANY(:i)"), {"i": ids})
        await s.execute(text("DELETE FROM normativa_versiones WHERE resolucion_id = CAST(:r AS uuid)"),
                        {"r": resolucion})
        await s.execute(text("DELETE FROM normativa_resoluciones WHERE id = CAST(:r AS uuid)"), {"r": resolucion})
        await s.commit()


@pytest_asyncio.fixture
async def cliente(mundo):
    from app_core.db.session import get_session
    from main import app

    async def _sesion():
        async with mundo["f"]() as s:
            yield s

    app.dependency_overrides[get_session] = _sesion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


def cab(mundo, usuario, tenant, rol):
    return {"X-User-ID": mundo["u"][usuario], "X-Tenant-ID": mundo[tenant], "X-Role": rol}


async def foto_de_la_organizacion(mundo, tenant):
    """Cuántas filas tiene la organización en lo que la propuesta NO debe tocar."""
    async with mundo["f"]() as s:
        await fijar_contexto_rls(s, tenant)
        consultas = {
            "hallazgos": "SELECT count(*) FROM hallazgos",
            "tareas_mitigacion": "SELECT count(*) FROM tareas_mitigacion",
            "rat_actividades": "SELECT count(*) FROM rat_actividades",
        }
        cuentas = {}
        for tabla, consulta in consultas.items():
            cuentas[tabla] = (await s.execute(text(consulta))).scalar()
        await s.rollback()
    return cuentas


async def contar_hallazgos(mundo, tenant):
    async with mundo["f"]() as s:
        await fijar_contexto_rls(s, tenant)
        n = (await s.execute(text("SELECT count(*) FROM hallazgos WHERE origen_ref LIKE 'norm03:%'"))).scalar()
        await s.rollback()
    return n


def inyectar(elementos, **extra):
    modelo = modelo_simulado(elementos)
    svc.inyectar_dependencias_de_impacto_de_prueba(analizar=modelo, catalogo=CatalogoFijo(), **extra)
    return modelo


async def pedir(cliente, mundo, usuario="adm_a", tenant="ta", rol="admin_organizacion"):
    return await cliente.post(
        f"/api/v1/normativa/resoluciones/{mundo['resolucion']}/impacto", headers=cab(mundo, usuario, tenant, rol))


async def test_extraccion_lee_el_pdf_y_reconoce_los_articulos():
    """Mutación: extraer_texto devuelve "" o normalizar_cita no reconoce «Art. 5» y «Artículo 7»."""
    texto = extraccion.extraer_texto(PDF)
    assert "aviso de privacidad" in texto
    assert {"art5", "art7"} <= extraccion.articulos_del_texto(texto)
    assert extraccion.normalizar_cita("Artículo 7") == extraccion.normalizar_cita("art. 7") == "art7"
    assert extraccion.extraer_texto(b"no es un pdf") == ""


async def test_fragmentar_cubre_el_texto_con_solape():
    """Mutación: el solape o el corte rompen la cobertura (el último fragmento no llega al final)."""
    texto = " ".join(f"palabra{i}" for i in range(800))
    fragmentos = extraccion.fragmentar(texto, largo=400, solape=50)
    assert len(fragmentos) > 5
    assert fragmentos[0].texto.startswith("palabra0")
    assert fragmentos[-1].texto.endswith("palabra799")
    assert all(len(f.texto) <= 400 for f in fragmentos)


async def test_indexacion_usa_text_embedding_005(mundo, cliente):
    """Mutación: se indexa con otro modelo o no se indexa."""
    pedidos = []

    class Indexador:
        async def vectorizar(self, textos, modelo):
            pedidos.append((len(textos), modelo))
            return [[0.0] for _ in textos]

    inyectar(ELEMENTOS_CON_SUSTENTO, indexador=Indexador())
    r = await pedir(cliente, mundo)
    assert r.status_code == 202, r.text
    assert pedidos and pedidos[0][1] == "text-embedding-005"


async def test_propuesta_cita_articulos_y_no_modifica_nada(mundo, cliente):
    """Mutación: solicitar() escribe hallazgos o toca tablas de la organización; o deja pasar una cita inexistente."""
    antes = await foto_de_la_organizacion(mundo, mundo["ta"])
    modelo = inyectar(ELEMENTOS_CON_SUSTENTO + [
        {"tipo": "pregunta", "referencia_id": "P99", "motivo": "No está en el catálogo.",
         "articulos_citados": ["Art. 5"]},
        {"tipo": "pregunta", "referencia_id": "P12", "motivo": "Cita un artículo que no existe.",
         "articulos_citados": ["Art. 99"]},
    ])
    r = await pedir(cliente, mundo)
    assert r.status_code == 202, r.text
    cuerpo = r.json()
    assert cuerpo["estado"] == "propuesta" and cuerpo["sin_base_normativa"] is False
    assert cuerpo["modelo"] == "gemini-2.5-pro"
    assert {(e["tipo"], e["referencia_id"]) for e in cuerpo["propuesta"]} == {("pregunta", "P12"), ("tratamiento", "rat-uno")}
    assert all(e["articulos_citados"] for e in cuerpo["propuesta"])
    assert modelo.llamadas[0][2] == mundo["ta"]
    assert await foto_de_la_organizacion(mundo, mundo["ta"]) == antes


async def test_sin_base_normativa(mundo, cliente):
    """Mutación: una propuesta sin cita válida se guarda como si tuviera base."""
    inyectar([{"tipo": "pregunta", "referencia_id": "P12", "motivo": "Sin sustento.", "articulos_citados": []}])
    r = await pedir(cliente, mundo)
    assert r.status_code == 202, r.text
    assert r.json()["sin_base_normativa"] is True and r.json()["propuesta"] == []
    assert r.json()["estado"] == "propuesta"


async def test_aceptacion_genera_hallazgos(mundo, cliente):
    """Mutación: aceptar no crea un hallazgo por elemento, o rechazar sí los crea."""
    inyectar(ELEMENTOS_CON_SUSTENTO)
    analisis = (await pedir(cliente, mundo)).json()
    assert await contar_hallazgos(mundo, mundo["ta"]) == 0
    r = await cliente.post(f"/api/v1/normativa/impacto/{analisis['id']}/decision",
                           json={"decision": "aceptar", "nota": NOTA}, headers=cab(mundo, "dpo_a", "ta", "dpo"))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "aceptada" and r.json()["hallazgos_generados"] == 2
    assert r.json()["decidida_por"] == mundo["u"]["dpo_a"]
    assert await contar_hallazgos(mundo, mundo["ta"]) == 2
    otra = await cliente.post(f"/api/v1/normativa/impacto/{analisis['id']}/decision",
                              json={"decision": "rechazar", "nota": NOTA}, headers=cab(mundo, "dpo_a", "ta", "dpo"))
    assert otra.status_code == 409


async def test_rechazar_no_genera_hallazgos_y_exige_nota(mundo, cliente):
    """Mutación: la nota deja de ser obligatoria o rechazar crea hallazgos."""
    inyectar(ELEMENTOS_CON_SUSTENTO)
    analisis = (await pedir(cliente, mundo)).json()
    url = f"/api/v1/normativa/impacto/{analisis['id']}/decision"
    h = cab(mundo, "dpo_a", "ta", "dpo")
    assert (await cliente.post(url, json={"decision": "rechazar", "nota": "corta"}, headers=h)).status_code == 422
    r = await cliente.post(url, json={"decision": "rechazar", "nota": NOTA}, headers=h)
    assert r.status_code == 200 and r.json()["estado"] == "rechazada"
    assert await contar_hallazgos(mundo, mundo["ta"]) == 0


async def test_solo_dpo_decide(mundo, cliente):
    """Mutación: el router de la decisión acepta el rol de administrador."""
    inyectar(ELEMENTOS_CON_SUSTENTO)
    analisis = (await pedir(cliente, mundo)).json()
    r = await cliente.post(f"/api/v1/normativa/impacto/{analisis['id']}/decision",
                           json={"decision": "aceptar", "nota": NOTA},
                           headers=cab(mundo, "adm_a", "ta", "admin_organizacion"))
    assert r.status_code == 403
    assert await contar_hallazgos(mundo, mundo["ta"]) == 0
    listado = await cliente.get("/api/v1/normativa/impacto", headers=cab(mundo, "adm_a", "ta", "admin_organizacion"))
    assert listado.json()[0]["estado"] == "propuesta"


async def test_impacto_aislamiento_rls(mundo, cliente):
    """Mutación: la política RLS de normativa_analisis_impacto no filtra por tenant_id."""
    inyectar(ELEMENTOS_CON_SUSTENTO)
    assert (await pedir(cliente, mundo)).status_code == 202
    assert (await pedir(cliente, mundo, "dpo_b", "tb", "dpo")).status_code == 202
    para_b = await cliente.get(f"/api/v1/normativa/impacto?resolucion_id={mundo['resolucion']}",
                               headers=cab(mundo, "dpo_b", "tb", "dpo"))
    assert para_b.status_code == 200 and len(para_b.json()) == 1
    async with mundo["f"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        assert (await s.execute(text("SELECT count(*) FROM normativa_analisis_impacto"))).scalar() == 0
        await fijar_contexto_rls(s, mundo["ta"])
        filas = (await s.execute(text("SELECT DISTINCT tenant_id FROM normativa_analisis_impacto"))).all()
        assert [f.tenant_id for f in filas] == [mundo["ta"]]
        await s.rollback()
    async with mundo["f"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, mundo["ta"])
        with pytest.raises(Exception):  # WITH CHECK: no se inserta a nombre de otra organización
            await s.execute(text(
                "INSERT INTO normativa_analisis_impacto (tenant_id, resolucion_id, modelo, corpus_sha256, "
                "sin_base_normativa, solicitada_por) VALUES (:t, CAST(:r AS uuid), 'gemini-2.5-pro', :h, TRUE, 'x')"),
                {"t": mundo["tb"], "r": mundo["resolucion"], "h": SHA})
        await s.rollback()


async def test_tabla_con_rls_habilitada_y_forzada(db_engine):
    """Mutación: la migración omite ENABLE o FORCE ROW LEVEL SECURITY."""
    async with db_engine.connect() as c:
        fila = (await c.execute(text(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE relname = 'normativa_analisis_impacto' AND relnamespace = 'public'::regnamespace"))).first()
    assert fila is not None and fila.relrowsecurity and fila.relforcerowsecurity


async def test_regenera_cache_al_cambiar_estado(mundo):
    """Mutación: revisar_estado no pide la caché, o la pide con una huella que no cambia con el estado."""
    pedidos = []
    svc.inyectar_dependencias_de_impacto_de_prueba(solicitar_cache=pedidos.append)
    await svc.revisar_estado(mundo["resolucion"], "vigente", NOTA, "operador-n03")
    esperado = hashlib.sha256(f"{mundo['resolucion']}:{SHA}".encode()).hexdigest()
    assert pedidos == [esperado]
    assert svc.ultima_regeneracion_de_cache().pedida is True
    await svc.revisar_estado(mundo["resolucion"], "observada", NOTA, "operador-n03")
    assert len(pedidos) == 1 and svc.ultima_regeneracion_de_cache().pedida is False
    await svc.revisar_estado(mundo["resolucion"], "derogada", NOTA, "operador-n03")
    assert len(pedidos) == 2 and pedidos[1] != esperado


async def test_ia_no_disponible_falla_cerrada(mundo, cliente):
    """Mutación: ante un fallo del modelo se guarda una propuesta inventada en lugar de un 503."""
    async def roto(texto, catalogo, org_id):
        raise RuntimeError("sin Vertex")

    svc.inyectar_dependencias_de_impacto_de_prueba(analizar=roto, catalogo=CatalogoFijo())
    r = await pedir(cliente, mundo)
    assert r.status_code == 503 and r.json()["detail"]["codigo"] == "NORMATIVA_IMPACTO_IA_NO_DISPONIBLE"
    listado = await cliente.get("/api/v1/normativa/impacto", headers=cab(mundo, "adm_a", "ta", "admin_organizacion"))
    assert listado.json() == []
