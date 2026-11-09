"""GCP-04 · Cloud SQL PostgreSQL 16 con RLS forzado y balanceador unificado.

`¤cloud-run-perf` `¤seguridad-tenant` `¤ci-cd` — INV_LOPDP_CLOUD_SQL_AUTOPROXY
"""

import os
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import verificar_cloudsql_conexion as vc  # noqa: E402

INSTANCIA = (RAIZ / "governance/operaciones/cloud_sql_instance.yaml").read_text(encoding="utf-8")
BALANCEADOR = (RAIZ / "governance/operaciones/cloud_load_balancer.yaml").read_text(encoding="utf-8")


def test_cloud_sql_especificacion_segura():
    assert re.search(r"^databaseVersion:\s*POSTGRES_16\s*$", INSTANCIA, flags=re.M)
    respaldo = INSTANCIA.split("backupConfiguration:", 1)[1].split("ipConfiguration:", 1)[0]
    assert re.search(r"enabled:\s*true", respaldo) and "pointInTimeRecoveryEnabled: true" in respaldo
    assert "ipv4Enabled: false" in INSTANCIA and "privateNetwork:" in INSTANCIA
    assert "sslMode: ENCRYPTED_ONLY" in INSTANCIA and "requireSsl: true" in INSTANCIA
    assert "force_row_level_security: true" in INSTANCIA
    app = INSTANCIA.split("- name: lopdp_app", 1)[1].split("\n  - name:", 1)[0]
    assert "NOBYPASSRLS" in app and "NOSUPERUSER" in app and "BYPASSRLS]" not in app.replace("NOBYPASSRLS", "")
    # Sin contraseñas ni URLs de conexión en el archivo.
    assert not re.search(r"password\s*:|://[^/\s]*:[^@\s]+@", INSTANCIA, flags=re.I)


def test_load_balancer_enrutamiento_unificado():
    url_map = BALANCEADOR.split("url_map:", 1)[1]
    assert re.search(r"defaultService:\s*evydentia-web-bs", url_map)
    regla = re.search(r'paths:\s*\["/api/v1/\*"\]\s*\n\s*service:\s*(\S+)', url_map)
    assert regla and regla.group(1) == "evydentia-backend-bs"
    assert re.search(r"name: evydentia-backend-bs\s*\n\s*neg_serverless: evydentia-backend", BALANCEADOR)
    assert re.search(r"name: evydentia-web-bs\s*\n\s*neg_serverless: evydentia-web", BALANCEADOR)
    assert "certificado_administrado:" in BALANCEADOR and "politica_cloud_armor:" in BALANCEADOR
    assert BALANCEADOR.count("politica_seguridad: evydentia-waf") == 2
    assert "redireccion_http_a_https: true" in BALANCEADOR


def test_guia_de_carga_viable_en_cloud_sql():
    """Sin superusuario: no hay --disable-triggers; FORCE se quita para cargar y se vuelve a poner."""
    guia = (RAIZ / "governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md").read_text(encoding="utf-8")
    assert "--disable-triggers" not in guia
    assert "pg_dump -Fc" in guia
    assert "NO FORCE ROW LEVEL SECURITY" in guia
    guardar = guia.index("> tablas_force.txt")  # la lista se guarda antes de quitar FORCE
    quitar = guia.index("NO FORCE ROW LEVEL SECURITY")
    assert guardar < quitar
    volver = guia.index("ALTER TABLE <tabla> FORCE ROW LEVEL SECURITY")
    verificar = guia.index("Verificación notarial, obligatoria antes del corte")
    corte = guia.index("**Corte.**")
    assert quitar < volver < verificar < corte


def _estado(**cambios):
    base = dict(version_num=160004, rol="lopdp_app", superusuario=False, bypassrls=False, ssl=True)
    base.update(cambios)
    return vc.Estado(**base)


def test_verificador_acepta_lopdp_app_y_rechaza_bypassrls():
    assert vc.evaluar(_estado()) == []
    assert any("BYPASSRLS" in f for f in vc.evaluar(_estado(bypassrls=True)))
    assert any("superusuario" in f for f in vc.evaluar(_estado(superusuario=True)))
    assert any("PostgreSQL 16" in f for f in vc.evaluar(_estado(version_num=150008)))
    assert any("SSL" in f for f in vc.evaluar(_estado(ssl=False)))
    assert vc.evaluar(_estado(ssl=False), exigir_ssl=False) == []
    assert any("public.t" in f for f in vc.evaluar(_estado(tablas_sin_rls=["public.t"])))
    assert any("lopdp_beta_owner" in f for f in vc.evaluar(_estado(rol="lopdp_beta_owner")))


# CI-18 · comprobación 5 (Alembic): pruebas 1, 2, 5 y 6 sobre la función pura.
def test_ci18_01_revision_en_la_unica_cabeza_da_0():
    assert vc.comprobar_revision("abc123", {"abc123"}) == 0
    assert vc.comprobar_revision({"abc123"}, ["abc123"]) == 0


def test_ci18_02_revision_atrasada_da_1():
    assert vc.comprobar_revision("anterior", {"cabeza"}) == 1
    assert "atrasada" in vc.motivo_revision("anterior", {"cabeza"})


def test_ci18_05_varias_cabezas_sin_fusionar_da_1():
    cabezas = {"rama_a", "rama_b"}
    assert vc.comprobar_revision("rama_a", cabezas) == 1
    assert vc.comprobar_revision({"rama_a", "rama_b"}, cabezas) == 1
    assert "cabezas sin fusionar" in vc.motivo_revision("rama_a", cabezas)


def test_ci18_06_base_sin_alembic_version_da_1():
    assert vc.comprobar_revision(None, {"cabeza"}) == 1
    assert vc.comprobar_revision(set(), {"cabeza"}) == 1


def test_ci18_02b_main_falla_con_la_base_atrasada(monkeypatch, capsys):
    """La comprobación 5 entra en main: un estado sano pero atrasado sale con 1."""
    monkeypatch.setenv("CLOUDSQL_DATABASE_URL", "postgresql://u:p@127.0.0.1:1/x")
    monkeypatch.setattr(vc, "leer_estado", lambda url, rol=None: _estado(revision={"anterior"}))
    monkeypatch.setattr(vc, "cabezas_del_repositorio", lambda: {"cabeza"})
    assert vc.main([]) == 1
    assert "atrasada" in capsys.readouterr().out


def test_ci18_03_sin_cloudsql_url_sale_con_2_aunque_haya_database_url(monkeypatch, capsys):
    monkeypatch.delenv("CLOUDSQL_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/x")
    monkeypatch.setattr(vc, "leer_estado", lambda url, rol=None: _estado(revision={"cabeza"}))
    monkeypatch.setattr(vc, "cabezas_del_repositorio", lambda: {"cabeza"})
    assert vc.main([]) == 2
    salida = capsys.readouterr()
    assert "CLOUDSQL_DATABASE_URL" in salida.out + salida.err


def test_ci18_04_la_url_no_aparece_en_la_salida(monkeypatch, capsys):
    url = "postgresql://usuario-generado:clave-generada@host-generado:1/base-generada?connect_timeout=1"
    monkeypatch.setenv("CLOUDSQL_DATABASE_URL", url)

    def falla(_url, rol=None):
        raise RuntimeError(url)

    monkeypatch.setattr(vc, "leer_estado", falla)
    assert vc.main(["--sin-ssl"]) == 2
    salida = capsys.readouterr()
    for parte in ("usuario-generado", "clave-generada", "host-generado", "base-generada"):
        assert parte not in salida.out + salida.err


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="sin TEST_DATABASE_URL")
def test_verificador_contra_postgres_16_con_lopdp_app(monkeypatch):
    """Contra la base de prueba migrada (contenedor PostgreSQL 16 local o del CI)."""
    estado = vc.leer_estado(os.environ["TEST_DATABASE_URL"], rol="lopdp_app")
    assert estado.rol == "lopdp_app" and not estado.bypassrls and not estado.superusuario
    assert estado.tablas_sin_rls == [], estado.tablas_sin_rls
    assert vc.evaluar(estado, exigir_ssl=False) == []
    # CI-18: la base migrada del CI está en la cabeza del repositorio.
    assert vc.comprobar_revision(estado.revision, vc.cabezas_del_repositorio()) == 0


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="sin TEST_DATABASE_URL")
def test_ci18_07_la_revision_no_se_lee_bajo_set_role_lopdp_app(monkeypatch):
    """Opción b: lopdp_app no lee alembic_version; la revisión se lee con el rol de la conexión (el dueño)."""
    from sqlalchemy import text

    roles = []
    original = vc._leer_revision

    def espia(conexion):
        roles.append(conexion.execute(text("SELECT current_user")).scalar_one())
        return original(conexion)

    monkeypatch.setattr(vc, "_leer_revision", espia)
    estado = vc.leer_estado(os.environ["TEST_DATABASE_URL"], rol="lopdp_app")
    assert estado.rol == "lopdp_app" and estado.revision
    assert roles and "lopdp_app" not in roles, roles
