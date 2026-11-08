# ¤entorno-pruebas ¤boveda-cloud
"""EP-05: Cloud SQL, buckets y secretos del entorno de pruebas (PRD EVYDENTIA §5.5, invariantes 53, 55 y 56).

Árbitro estático sobre los manifiestos de governance/operaciones/entornos/pruebas/: no toca Google Cloud.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
OPERACIONES = RAIZ / "governance" / "operaciones"
PRUEBAS = OPERACIONES / "entornos" / "pruebas"


def _cargar(ruta: Path) -> dict:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def produccion() -> dict:
    return _cargar(OPERACIONES / "cloud_sql_instance.yaml")


@pytest.fixture(scope="module")
def pruebas() -> dict:
    return _cargar(PRUEBAS / "cloud_sql.yaml")


@pytest.fixture(scope="module")
def buckets() -> list[dict]:
    return _cargar(PRUEBAS / "buckets.yaml")["buckets"]


# Diferencias admitidas por el §5.5: tamaño (tier, disponibilidad), horario y proyecto (nombres,
# red, base, socket y URL). Toda otra clave debe ser idéntica a la de producción.
CLAVES_ADMITIDAS = {
    "name", "databases", "conexion", "horario", "extensiones",
    "settings.tier", "settings.availabilityType", "settings.activationPolicy",
    "settings.ipConfiguration.privateNetwork",
}


def _aplanar(datos, prefijo: str = "") -> dict:
    if isinstance(datos, dict):
        plano = {}
        for clave, valor in datos.items():
            plano.update(_aplanar(valor, f"{prefijo}{clave}."))
        return plano
    return {prefijo.rstrip("."): datos}


def _admitida(clave: str) -> bool:
    return any(clave == c or clave.startswith(c + ".") for c in CLAVES_ADMITIDAS)


# --- Cloud SQL ------------------------------------------------------------------------------------

def test_cloud_sql_solo_difiere_en_tamano_horario_y_proyecto(produccion, pruebas):
    prod, prue = _aplanar(produccion), _aplanar(pruebas)
    distintas = {c for c in prod.keys() | prue.keys() if prod.get(c) != prue.get(c)}
    assert sorted(c for c in distintas if not _admitida(c)) == []


def test_cloud_sql_conserva_motor_rol_y_rls(produccion, pruebas):
    assert pruebas["databaseVersion"] == produccion["databaseVersion"] == "POSTGRES_16"
    assert pruebas["rls"] == produccion["rls"]
    assert pruebas["rls"]["force_row_level_security"] is True
    assert pruebas["users"] == produccion["users"]
    app = next(u for u in pruebas["users"] if u["name"] == "lopdp_app")
    assert "NOBYPASSRLS" in app["atributos"]
    assert "vector" in pruebas["extensiones"]
    assert pruebas["settings"]["backupConfiguration"]["enabled"] is True


def test_cloud_sql_es_mas_pequena_y_tiene_horario(produccion, pruebas):
    assert pruebas["settings"]["tier"] != produccion["settings"]["tier"]
    assert pruebas["name"] != produccion["name"]
    assert "--activation-policy=NEVER" in pruebas["horario"]["fuera_de_horario"]
    assert all("--project PROYECTO_PRUEBAS" in pruebas["horario"][k] for k in ("fuera_de_horario", "al_empezar"))


# --- Buckets --------------------------------------------------------------------------------------

def test_hay_los_dos_tiers_de_la_boveda(buckets):
    assert sorted(b["tier"] for b in buckets) == ["long-retention", "short-ttl"]


def test_ningun_bucket_de_pruebas_declara_una_retencion_bloqueada(buckets):
    for bucket in buckets:
        assert bucket["retentionPolicy"]["locked"] is False, bucket["nombre"]
    texto = (PRUEBAS / "buckets.yaml").read_text(encoding="utf-8")
    assert not re.search(r"locked:\s*true|isLocked:\s*true|--lock|lock-retention", texto, re.IGNORECASE)


# Producción todavía no versiona su manifiesto de buckets: la referencia es BOV-02 (R1) y el PRD EVYDENTIA.
CICLO_PRODUCCION = {
    "short-ttl": {"autoclass": False, "retencion": 15, "borrado": 15},
    "long-retention": {"autoclass": True, "retencion": 1825, "borrado": None},
}


@pytest.mark.parametrize("tier", sorted(CICLO_PRODUCCION))
def test_ciclos_de_vida_coinciden_con_produccion(buckets, tier):
    bucket = next(b for b in buckets if b["tier"] == tier)
    esperado = CICLO_PRODUCCION[tier]
    assert bucket["autoclass"] is esperado["autoclass"]
    assert bucket["retentionPolicy"]["retentionPeriodDias"] == esperado["retencion"]
    borrados = [r["condition"]["age"] for r in bucket["lifecycle"]["rule"] if r["action"]["type"] == "Delete"]
    assert borrados == ([esperado["borrado"]] if esperado["borrado"] else [])
    assert bucket["notificacion"]["eventarc"]["destino"] == "vault_worker"


def test_los_nombres_de_bucket_no_son_los_de_produccion(buckets):
    produccion = {"lopdp360-vault-short-ttl", "lopdp360-vault-long-retention"}
    assert not produccion & {b["nombre"] for b in buckets}


# --- Secretos -------------------------------------------------------------------------------------

def _secretos() -> list[dict]:
    return _cargar(PRUEBAS / "secretos.yaml")["secretos"]


def _buscar(nodo, clave):
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k == clave:
                yield v
            yield from _buscar(v, clave)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from _buscar(v, clave)


def _secretos_de_produccion() -> set[str]:
    nombres = set()
    for manifiesto in ("cloudrun_service.yaml", "cloudrun_frontend_service.yaml"):
        texto = (OPERACIONES / manifiesto).read_text(encoding="utf-8")
        for doc in yaml.safe_load_all(texto):
            for ref in _buscar(doc, "secretKeyRef"):
                nombres.add(ref["name"])
    return nombres


CAMPOS_SECRETO = {"nombre", "contenido", "leen", "condicional"}
VALOR = re.compile(r"(postgres(ql)?(\+\w+)?://|BEGIN [A-Z ]*PRIVATE KEY|GOCSPX-|re_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{20,})")


def test_secretos_sin_valores():
    texto = (PRUEBAS / "secretos.yaml").read_text(encoding="utf-8")
    assert not VALOR.search(texto)
    for secreto in _secretos():
        assert set(secreto) <= CAMPOS_SECRETO, secreto["nombre"]
        assert secreto["leen"], secreto["nombre"]


def test_ningun_secreto_coincide_con_uno_de_produccion():
    produccion = _secretos_de_produccion()
    assert produccion, "no se leyeron los secretos de producción"
    nombres = {s["nombre"] for s in _secretos()}
    assert not {n.lower() for n in nombres} & {n.lower() for n in produccion}
    assert all(n.startswith("evydentia-pruebas-") for n in nombres)


def test_no_hay_secretos_de_correo():
    """Decisión del propietario del 2026-11-07: el correo queda apagado y sin proveedor."""
    nombres = " ".join(s["nombre"] for s in _secretos()).lower()
    assert not re.search(r"resend|smtp|correo|mail", nombres)
