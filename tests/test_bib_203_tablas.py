# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-203: tablas de captura (INV, RAT, LEG) y PLA de solo lectura.

Reglas puras siempre. La persistencia (RLS, atomicidad, referencias del mismo tenant) corre contra la base
local del arnés o una rama Neon propia, con la fixture de BIB-201 (transacción que se revierte).

Mutación decisiva: en `features/biblioteca/services/filas.py`, `validar_fila`, cambiar
``valor not in tratamientos`` por ``False`` (aceptar un tratamiento de otro tenant) hace fallar
``test_tratamiento_de_otro_tenant_se_rechaza`` y ``test_confirmar_con_una_fila_mala_no_inserta_nada``
(observado el 2026-11-04: 2 fallos; restaurado, 0). En la base, el disparador de la migración es el respaldo.
"""
import importlib.util
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import filas
from tests.test_bib_201_formularios import CUERPO, CAMARAS, FINALIDAD, db_bib, fuentes, plantilla, publicar  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261114_biblioteca_filas.py"
PROPIO, AJENO = "rat-propio", "rat-ajeno"


def fila(codigo="INV-1", **datos):
    base = {"nombre": "Base de clientes", "categoria": "CONTACTO"}
    return filas.FilaEntrada(codigo=codigo, datos={**base, **datos})


# --------------------------------------------------------------------------- reglas puras

def test_fila_valida_y_catalogo_permitido():
    datos, errores = filas.validar_fila("INV", fila(tratamiento_id=PROPIO), {PROPIO})
    assert errores == [] and datos["tratamiento_id"] == PROPIO
    _, errores = filas.validar_fila("INV", fila(categoria="INVENTADA"), set())
    assert any("catálogo" in e for e in errores)


def test_tratamiento_de_otro_tenant_se_rechaza():
    _, errores = filas.validar_fila("INV", fila(tratamiento_id=AJENO), {PROPIO})
    assert any("tratamiento" in e for e in errores)


def test_columnas_ajenas_obligatorias_y_codigo():
    _, errores = filas.validar_fila("INV", fila(codigo="mal código", estado="En plazo", nombre=""), set())
    assert any(e.startswith("codigo") for e in errores)
    assert any(e.startswith("estado") for e in errores)  # columnas calculadas no se escriben
    assert any(e.startswith("nombre") for e in errores)


def test_fechas_reales():
    assert filas.fecha_real("2026-02-28") == date(2026, 2, 28)
    for mala in ("2026-02-30", "30/01/2026", "2026-13-01", ""):
        assert filas.fecha_real(mala) is None
    _, errores = filas.validar_fila("INV", fila(fecha_revision="2026-02-30"), set())
    assert any("fecha real" in e for e in errores)


def test_pla_no_se_captura():
    with pytest.raises(ErrorNegocio) as e:
        filas.validar_fila("PLA", fila(), set())
    assert e.value.code == "BIB_FILA_TABLA_INVALIDA"


def test_fecha_invalida_nunca_aparece_en_plazo():
    hoy = date(2026, 11, 4)
    assert filas.estado_plan("2026-11-01", "2026-12-01", "pendiente", hoy) == "En plazo"
    assert filas.estado_plan("2026-10-01", "2026-10-31", "en_progreso", hoy) == "Vencida"
    assert filas.estado_plan(None, "2026-10-01", "completada", hoy) == "Completada"
    for inicio, fin in ((None, None), (None, "2026-02-30"), ("2026-12-02", "2026-12-01"), ("x", "2026-12-01")):
        assert filas.estado_plan(inicio, fin, "pendiente", hoy) == "Sin fecha válida"


def test_pla_solo_lectura_desde_el_plan():
    plan = {"waves": [{"tasks": [{"id": "t1", "title": "Política", "control_ref": "P1", "status": "pendiente",
                                  "start_date": date(2026, 11, 1), "end_date": None}]}]}
    [p] = filas.filas_del_plan(plan, date(2026, 11, 4))
    assert p.estado == "Sin fecha válida" and p.editable is False
    assert filas.filas_del_plan(None) == []


def test_mas_de_cien_filas_se_rechaza_en_el_contrato():
    with pytest.raises(Exception):
        bib.PegarFilas(tabla="INV", filas=[fila(f"I{i}") for i in range(101)])
    assert len(bib.PegarFilas(tabla="INV", filas=[fila(f"I{i}") for i in range(100)]).filas) == 100


@pytest.mark.asyncio
async def test_confirmar_con_una_fila_mala_no_inserta_nada(monkeypatch):
    llamadas = []

    async def execute(consulta, parametros=None):
        llamadas.append(str(consulta))
        if "FROM biblioteca_borradores" in str(consulta):
            return SimpleNamespace(first=lambda: ("b1",))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))

    async def tratamientos(session, tenant):
        return [PROPIO]
    session = SimpleNamespace(execute=execute)
    entrada = bib.PegarFilas(tabla="INV", filas=[fila("A"), fila("B", tratamiento_id=AJENO), fila("A")])
    previa = await bib.validar_filas(session, tratamientos, "t", "u", "b1", entrada)
    assert not previa.valida and [bool(r.errores) for r in previa.filas] == [False, True, True]
    with pytest.raises(ErrorNegocio) as e:
        await bib.confirmar_filas(session, tratamientos, "t", "u", "b1", entrada)
    assert e.value.code == "BIB_FILAS_INVALIDAS"
    assert not any("INSERT" in c for c in llamadas)


def test_contratos_rutas_y_errores():
    from api.routers import biblioteca_filas as router
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/filas/esquemas"), ("GET", "/biblioteca/filas/plan/{roadmap_id}"),
        ("GET", "/biblioteca/filas/{borrador_id}/{tabla}"), ("POST", "/biblioteca/filas/{borrador_id}/validar"),
        ("POST", "/biblioteca/filas/{borrador_id}"), ("PUT", "/biblioteca/filas/fila/{fila_id}")}
    for codigo, estado in (("BIB_FILA_TABLA_INVALIDA", 422), ("BIB_FILAS_DEMASIADAS", 422),
                           ("BIB_FILAS_INVALIDAS", 422), ("BIB_FILA_NO_ENCONTRADA", 404),
                           ("BIB_FILA_REVISION_DESFASADA", 409)):
        assert CATALOGO_ERRORES[codigo].status_code == estado
    assert set(bib.esquemas_filas()) == {"INV", "RAT", "LEG"}


def test_migracion_rls_forzada_permisos_minimos_y_una_cabeza():
    spec = importlib.util.spec_from_file_location("bib203_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert len(guion.get_heads()) == 1 and guion.get_revision(migracion.revision) is not None
    sql = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "UNIQUE (tenant_id,tabla,codigo)" in texto and "rat_actividades" in texto
    assert "ENABLE ROW LEVEL SECURITY" in texto and "FORCE ROW LEVEL SECURITY" in texto
    assert "WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))" in texto
    assert "GRANT SELECT,INSERT ON" in texto and "DELETE" not in texto.split("REVOKE")[1]
    assert "GRANT ALL" not in texto


# --------------------------------------------------------------------------- persistencia

async def _preparar(sesion, ids, tenant, otro):
    """Borrador del tenant y un tratamiento en cada organización."""
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    borrador = await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    rats = {}
    for tid in (tenant, otro):
        rid = "bib203-rat-" + uuid4().hex
        await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tid})
        await sesion.execute(text(
            "INSERT INTO rat_actividades (id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal, "
            "medio_soporte, pais_transferencia, plazo_conservacion, nivel_riesgo, observaciones_dpo, origen, "
            "categorias_titulares, categorias_datos, encargados, destinatarios, medidas_seguridad, datos_sensibles, "
            "transferencia_internacional, requiere_eipd, es_gran_escala, decisiones_automatizadas, "
            "volumen_titulares_estimado, volumen_titulares_12_meses, version) VALUES (:id, :t, 'A-1', 'Act', '', "
            "'', 'CONSENTIMIENTO', '', '', '', '', '', 'manual', '[]', '[]', '[]', '[]', '[]', false, false, false, "
            "false, false, 0, 0, 1)"), {"id": rid, "t": tid})
        rats[tid] = rid

    async def tratamientos(session, tid):
        return [rats[tid]]
    return borrador.id, rats, tratamientos


@pytest.mark.asyncio
async def test_db_pegar_valida_confirma_y_lista(db_bib):
    sesion, ids, tenant, otro = db_bib
    borrador, rats, puerto = await _preparar(sesion, ids, tenant, otro)
    entrada = bib.PegarFilas(tabla="INV", filas=[fila("I1", tratamiento_id=rats[tenant]), fila("I2")])
    assert (await bib.validar_filas(sesion, puerto, tenant, ids["miembro"], borrador, entrada)).valida
    guardadas = await bib.confirmar_filas(sesion, puerto, tenant, ids["miembro"], borrador, entrada)
    assert len({f.id for f in guardadas}) == 2 and all(len(f.id) == 36 for f in guardadas)
    listadas = await bib.listar_filas(sesion, tenant, ids["miembro"], borrador, "INV")
    assert [f.codigo for f in listadas] == ["I1", "I2"]
    previa = await bib.validar_filas(sesion, puerto, tenant, ids["miembro"], borrador,
                                     bib.PegarFilas(tabla="INV", filas=[fila("I1")]))
    assert not previa.valida and "ya existe" in previa.filas[0].errores[0]
    editada = await bib.editar_fila(sesion, puerto, tenant, ids["miembro"], guardadas[1].id,
                                    bib.EditarFila(datos={"nombre": "Otra", "categoria": "SALUD"}, revision=1))
    assert editada.revision == 2 and editada.datos["categoria"] == "SALUD"
    with pytest.raises(ErrorNegocio) as e:
        await bib.editar_fila(sesion, puerto, tenant, ids["miembro"], guardadas[1].id,
                              bib.EditarFila(datos={"nombre": "X", "categoria": "SALUD"}, revision=1))
    assert e.value.code == "BIB_FILA_REVISION_DESFASADA"


@pytest.mark.asyncio
async def test_db_tratamiento_de_otra_organizacion_no_se_guarda(db_bib):
    sesion, ids, tenant, otro = db_bib
    borrador, rats, puerto = await _preparar(sesion, ids, tenant, otro)
    entrada = bib.PegarFilas(tabla="LEG", filas=[
        filas.FilaEntrada(codigo="L1", datos={"norma": "LOPDP", "base_legal": "CONSENTIMIENTO", "tratamiento_id": rats[tenant]}),
        filas.FilaEntrada(codigo="L2", datos={"norma": "LOPDP", "base_legal": "CONSENTIMIENTO", "tratamiento_id": rats[otro]}),
    ])
    with pytest.raises(ErrorNegocio) as e:
        await bib.confirmar_filas(sesion, puerto, tenant, ids["miembro"], borrador, entrada)
    assert e.value.code == "BIB_FILAS_INVALIDAS"
    assert await bib.listar_filas(sesion, tenant, ids["miembro"], borrador, "LEG") == []  # nada a medias


@pytest.mark.asyncio
async def test_db_otra_organizacion_no_ve_el_borrador_ni_sus_filas(db_bib):
    sesion, ids, tenant, otro = db_bib
    borrador, rats, puerto = await _preparar(sesion, ids, tenant, otro)
    await bib.confirmar_filas(sesion, puerto, tenant, ids["miembro"], borrador,
                              bib.PegarFilas(tabla="INV", filas=[fila("I9")]))
    with pytest.raises(ErrorNegocio) as e:
        await bib.listar_filas(sesion, otro, ids["ajeno"], borrador, "INV")
    assert e.value.code == "BIB_BORRADOR_NO_ENCONTRADO"
    cuenta = (await sesion.execute(text("SELECT count(*) FROM biblioteca_filas"))).scalar()
    assert cuenta == 0  # la RLS forzada oculta las filas del otro tenant
