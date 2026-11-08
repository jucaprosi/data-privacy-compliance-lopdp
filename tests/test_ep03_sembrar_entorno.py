# ¤entorno-pruebas ¤seguridad-tenant
"""EP-03: siembra idempotente del entorno de pruebas.

La idempotencia corre contra PostgreSQL real (`db_engine`, el contenedor del CI o el local): dos corridas
seguidas dejan los mismos conteos y el mismo hash, y la segunda no crea nada.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from scripts import sembrar_entorno_pruebas as siembra
from scripts.datos_sinteticos import clips, evidencias, organizaciones

RAIZ = Path(__file__).resolve().parents[1]
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
IDS = tuple(o.id for o in organizaciones.ORGANIZACIONES)


# --- Guardia de la huella -------------------------------------------------------------------------

def test_sin_huella_no_corre():
    with pytest.raises(siembra.GuardiaError):
        siembra.validar_destino("postgresql://u:p@localhost/x", None, entorno={})


def test_huella_en_la_url_aborta_sin_mostrarla():
    huella = f"proy-{uuid.uuid4().hex[:6]}"
    url = f"postgresql://u:p@{huella}.invalid/x"
    with pytest.raises(siembra.GuardiaError) as error:
        siembra.validar_destino(url, None, entorno={"HUELLA_PROYECTO_PRODUCCION": huella})
    assert url not in str(error.value) and huella not in str(error.value)


def test_huella_en_el_bucket_aborta():
    huella = f"proy-{uuid.uuid4().hex[:6]}"
    with pytest.raises(siembra.GuardiaError):
        siembra.validar_destino("postgresql://u:p@localhost/x", f"{huella}-evidencias",
                                entorno={"HUELLA_PROYECTO_PRODUCCION": huella})


def test_base_de_produccion_aborta_aunque_la_huella_sea_otra():
    from app_core.huellas_produccion import HUELLA_HOST_PRODUCCION

    with pytest.raises(siembra.GuardiaError):
        siembra.validar_destino(f"postgresql://u:p@{HUELLA_HOST_PRODUCCION}.invalid/x", None,
                                entorno={"HUELLA_PROYECTO_PRODUCCION": "otra-huella"})


def test_destino_de_pruebas_pasa():
    siembra.validar_destino("postgresql://u:p@localhost/x", "bucket-de-pruebas",
                            entorno={"HUELLA_PROYECTO_PRODUCCION": f"proy-{uuid.uuid4().hex[:6]}"})


# --- Datos ficticios -----------------------------------------------------------------------------

def test_tamanos_cubren_micro_mediana_y_gran_escala():
    tamanos = {o.tamano for o in organizaciones.ORGANIZACIONES}
    assert {"micro", "mediana"} <= tamanos
    assert any(o.gran_escala for o in organizaciones.ORGANIZACIONES)
    assert all("FICTICIA" in o.nombre_comercial and o.ruc.startswith("9999") for o in organizaciones.ORGANIZACIONES)


def test_ningun_correo_inventado_sale_de_example_test():
    textos = [p.read_text(encoding="utf-8") for p in (RAIZ / "scripts" / "datos_sinteticos").glob("*.py")]
    textos += [o.datos.decode("utf-8", "ignore") for o in siembra.objetos_sinteticos()]
    hallados = set(organizaciones.correos_ficticios())
    for t in textos:
        hallados |= set(CORREO.findall(t))
    assert hallados
    assert all(c.endswith("@example.test") for c in hallados), sorted(hallados)


def test_los_clips_no_tienen_audio_y_son_avi():
    for objeto in (o for org in IDS for o in clips.clips_de(org)):
        assert objeto.datos[:4] == b"RIFF" and objeto.datos[8:12] == b"AVI "
        assert b"vids" in objeto.datos
        assert not clips.tiene_audio(objeto.datos)


def test_detector_de_audio_reconoce_un_flujo_de_audio():
    falso = b"RIFF\0\0\0\0AVI strh\x04\0\0\0auds"
    assert clips.tiene_audio(falso)


def test_las_evidencias_son_pdf_y_texto_deterministas():
    a = evidencias.evidencias_de("ep-org-micro", "x")
    b = evidencias.evidencias_de("ep-org-micro", "x")
    assert [o.datos for o in a] == [o.datos for o in b]
    assert a[0].datos.startswith(b"%PDF-1.4") and a[0].datos.rstrip().endswith(b"%%EOF")


def test_archivo_de_quienes_prueban_no_esta_en_el_repositorio():
    rastreados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout
    assert "testers-entorno-pruebas" not in rastreados
    assert siembra.ruta_en_repositorio(RAIZ / "scripts" / "crear_organizacion_dev.py")
    assert not siembra.ruta_en_repositorio(siembra.TESTERS_POR_DEFECTO)


def test_lectura_de_cuentas_valida_sin_mostrar_correos():
    correo = f"t-{uuid.uuid4().hex[:6]}@example.invalid"
    cuentas = organizaciones.leer_cuentas(f"# comentario\n{correo},coordinador,ep-org-micro\n")
    assert cuentas == [organizaciones.CuentaDePrueba(correo, "coordinador", "ep-org-micro")]
    with pytest.raises(ValueError) as error:
        organizaciones.leer_cuentas(f"{correo},jefe,ep-org-micro")
    assert correo not in str(error.value)


# --- Idempotencia con PostgreSQL real --------------------------------------------------------------

async def _huella_de_la_base(session) -> tuple[dict, str]:
    consultas = {
        "tenants": "SELECT id, tamano, ruc_identificacion FROM tenants WHERE id = ANY(:ids) ORDER BY id",
        "users": "SELECT u.id, u.email FROM users u WHERE u.id IN (SELECT user_id FROM user_tenant_roles "
                 "WHERE tenant_id = ANY(:ids)) ORDER BY u.id",
        "areas": "SELECT tenant_id, codigo, nivel FROM areas WHERE tenant_id = ANY(:ids) "
                 "AND deleted_at IS NULL ORDER BY tenant_id, codigo",
        "roles": "SELECT r.tenant_id, r.user_id, r.role, a.codigo FROM user_tenant_roles r "
                 "LEFT JOIN areas a ON a.id = r.area_id WHERE r.tenant_id = ANY(:ids) "
                 "AND (r.valid_to IS NULL OR r.valid_to > now()) ORDER BY 1, 2, 3, 4",
    }
    conteos, h = {}, hashlib.sha256()
    for nombre, sql in consultas.items():
        filas = (await session.execute(text(sql), {"ids": list(IDS)})).all()
        conteos[nombre] = len(filas)
        h.update(repr((nombre, [tuple(f) for f in filas])).encode())
    return conteos, h.hexdigest()


def _huella_de_carpeta(carpeta: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(carpeta.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(carpeta).as_posix().encode() + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


@pytest.mark.asyncio
async def test_dos_corridas_dejan_los_mismos_conteos_y_hash(db_engine, tmp_path, capsys):
    correo = f"t-{uuid.uuid4().hex[:8]}@example.invalid"
    cuentas = [organizaciones.CuentaDePrueba(correo, "responsable_area", "ep-org-mediana")]
    almacen = siembra.AlmacenLocal(tmp_path)
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with fabrica() as s:
        primera = await siembra.sembrar(s, cuentas, almacen)
    async with fabrica() as s:
        conteos_1, hash_1 = await _huella_de_la_base(s)
    carpeta_1 = _huella_de_carpeta(tmp_path)

    async with fabrica() as s:
        segunda = await siembra.sembrar(s, cuentas, almacen)
    async with fabrica() as s:
        conteos_2, hash_2 = await _huella_de_la_base(s)

    assert conteos_1 == conteos_2 and hash_1 == hash_2
    assert carpeta_1 == _huella_de_carpeta(tmp_path)
    assert conteos_1["tenants"] == len(IDS)
    assert all(d["creados"] == 0 for d in segunda.values()), segunda
    assert sum(d["existentes"] for d in segunda.values()) == sum(
        d["creados"] + d["existentes"] for d in primera.values()
    )

    salida = siembra.formatear(primera) + siembra.formatear(segunda)
    print(salida)
    impreso = capsys.readouterr().out
    assert not CORREO.search(impreso) and "postgresql" not in impreso

    async with fabrica() as s:
        uid = organizaciones.id_de_usuario(correo)
        await s.execute(text("DELETE FROM user_tenant_roles WHERE user_id = :u"), {"u": uid})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        await s.commit()


def test_la_siembra_se_niega_si_git_rastrea_el_archivo_de_quienes_prueban(monkeypatch, capsys):
    """Decisión del Tech Lead (PR #500): herramientas/ no está en .gitignore; la guardia lo cubre."""
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", f"proy-{uuid.uuid4().hex[:6]}")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://u:p@localhost/x")
    rastreado = RAIZ / "scripts" / "crear_organizacion_dev.py"
    assert siembra.main(["--testers", str(rastreado)]) == 2
    assert "rastreado por git" in capsys.readouterr().err


def test_git_ignora_el_archivo_de_cuentas_de_quienes_prueban():
    r = subprocess.run(["git", "check-ignore", "-q", siembra.TESTERS_POR_DEFECTO.as_posix()], cwd=RAIZ)
    assert r.returncode == 0


# --- Condiciones del Arquitecto (2026-11-08) ------------------------------------------------------

TABLAS_DIRECTAS = {"tenants", "users"}
ESCRITURA = re.compile(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+([a-z_][a-z0-9_.]*)", re.IGNORECASE)


def _tablas_escritas(codigo: str) -> set[str]:
    return {m.group(1).lower() for m in ESCRITURA.finditer(codigo)}


def _archivos_de_siembra() -> list[Path]:
    return sorted((RAIZ / "scripts" / "datos_sinteticos").rglob("*.py")) + [RAIZ / "scripts" / "sembrar_entorno_pruebas.py"]


def test_la_siembra_solo_escribe_directo_en_tenants_y_users():
    escritas = set().union(*(_tablas_escritas(p.read_text(encoding="utf-8")) for p in _archivos_de_siembra()))
    assert escritas == TABLAS_DIRECTAS, escritas
    ajenas = {
        p.relative_to(RAIZ).as_posix(): sorted(_tablas_escritas(p.read_text(encoding="utf-8")) - TABLAS_DIRECTAS)
        for p in _archivos_de_siembra()
    }
    assert not {k: v for k, v in ajenas.items() if v}, ajenas


def test_el_recorrido_detecta_una_escritura_en_otra_tabla():
    mutante = 'text("INSERT INTO user_tenant_roles (user_id) VALUES (:u)")'
    assert _tablas_escritas(mutante) - TABLAS_DIRECTAS == {"user_tenant_roles"}


@pytest.mark.asyncio
async def test_tenant_sembrado_activo_y_completo_por_la_compuerta_y_correo_en_minusculas(db_engine, tmp_path):
    from features.plataforma import plataforma_service

    local = f"T-{uuid.uuid4().hex[:8]}"
    cuentas = organizaciones.leer_cuentas(f"{local.upper()}@EXAMPLE.INVALID,coordinador,ep-org-micro")
    almacen = siembra.AlmacenLocal(tmp_path)
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    uid = organizaciones.id_de_usuario(f"{local.lower()}@example.invalid")
    try:
        async with fabrica() as s:
            await siembra.sembrar(s, cuentas, almacen)
        async with fabrica() as s:
            segunda = await siembra.sembrar(s, cuentas, almacen)
        assert all(d["creados"] == 0 for d in segunda.values()), segunda
        async with fabrica() as s:
            correo = (await s.execute(text("SELECT email FROM users WHERE id = :u"), {"u": uid})).scalar_one()
            assert correo == correo.lower()
            leidas = {o.id: o for o in await plataforma_service.listar_organizaciones(s, {})}
        for org in organizaciones.ORGANIZACIONES:
            o = leidas[org.id]
            assert o.activo is True
            assert (o.nombre_comercial, o.razon_social, o.ruc_identificacion) == (
                org.nombre_comercial, org.razon_social, org.ruc)
    finally:
        async with fabrica() as s:
            await s.execute(text("DELETE FROM user_tenant_roles WHERE user_id = :u"), {"u": uid})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            await s.commit()


def test_huella_en_migration_database_url_sale_sin_escribir(monkeypatch, tmp_path, capsys):
    huella = f"proy-{uuid.uuid4().hex[:6]}"
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", huella)
    monkeypatch.setenv("MIGRATION_DATABASE_URL", f"postgresql://u:p@{huella}.invalid/x")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    carpeta = tmp_path / "destino"
    codigo = siembra.main(["--testers", str(tmp_path / "no-existe.txt"), "--carpeta", str(carpeta)])
    assert codigo != 0
    assert not carpeta.exists()
    assert "DATABASE_URL" not in __import__("os").environ
    assert huella not in capsys.readouterr().err
