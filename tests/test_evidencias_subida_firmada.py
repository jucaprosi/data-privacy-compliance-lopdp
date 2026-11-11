# ¤evidencias ¤arbitro
"""EVI-01: URL firmada de subida con escritura única, almacén que falla cerrado y reglas del archivo (sin base).

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- En `AlmacenGcs.firmar_subida`, quitar `CABECERA_ESCRITURA_UNICA` de `headers`
  -> test_la_url_de_subida_firma_la_cabecera_de_escritura_unica y test_una_segunda_subida_de_la_misma_clave_se_rechaza.
- En `almacen_por_defecto`, no comprobar `corre_en_cloud_run()` -> test_fuera_de_la_nube_falla_cerrado_sin_conectar.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from app_core.errors import ErrorNegocio  # noqa: E402
from app_core.storage import gcs  # noqa: E402
from app_core.storage.gcs import CABECERA_ESCRITURA_UNICA, AlmacenGcs, AlmacenNoDisponible  # noqa: E402
from features.evidencias.services import evidencias_engine as motor  # noqa: E402


class _Retencion:
    mode = None
    retain_until_time = None


class BlobFalso:
    def __init__(self, bucket, clave: str) -> None:
        self.bucket, self.clave, self.retention = bucket, clave, _Retencion()

    def generate_signed_url(self, **parametros) -> str:
        self.bucket.firmas.append(parametros)
        return f"https://storage.invalid/{self.clave}?firma=simulada"

    def reload(self) -> None:
        self.bucket.llamadas.append("reload")

    def patch(self) -> None:
        self.bucket.llamadas.append("patch")
        self.bucket.retenciones[self.clave] = (self.retention.mode, self.retention.retain_until_time)

    # Sin `delete`: el backend no tiene ese permiso y ningún código debe pedirlo.


class BucketFalso:
    def __init__(self) -> None:
        self.firmas: list[dict] = []
        self.llamadas: list[str] = []
        self.retenciones: dict = {}

    def blob(self, clave: str) -> BlobFalso:
        self.llamadas.append("blob")
        return BlobFalso(self, clave)


class ClienteFalso:
    def __init__(self) -> None:
        self.el_bucket = BucketFalso()

    def bucket(self, nombre: str) -> BucketFalso:
        return self.el_bucket


class CredencialesFalsas:
    service_account_email = "backend@proyecto.invalid"
    token = "token-simulado"

    def __init__(self) -> None:
        self.refrescos = 0

    def refresh(self, peticion) -> None:
        self.refrescos += 1


def _almacen():
    cliente, credenciales = ClienteFalso(), CredencialesFalsas()
    return AlmacenGcs(cliente, "bucket-pruebas", credenciales, peticion=object()), cliente.el_bucket, credenciales


def test_la_url_de_subida_firma_la_cabecera_de_escritura_unica():
    almacen, bucket, credenciales = _almacen()
    firma = almacen.firmar_subida("org/abc", "application/pdf")
    parametros = bucket.firmas[0]
    assert parametros["version"] == "v4" and parametros["method"] == "PUT"
    assert parametros["headers"][CABECERA_ESCRITURA_UNICA] == "0"
    assert firma.cabeceras[CABECERA_ESCRITURA_UNICA] == "0"
    assert parametros["content_type"] == "application/pdf"
    # Sin claves: firma por IAM con la cuenta y el token por defecto.
    assert parametros["service_account_email"] == credenciales.service_account_email
    assert parametros["access_token"] == credenciales.token and credenciales.refrescos == 1


def test_el_almacen_real_no_pide_delete_y_fija_la_retencion_desbloqueada():
    almacen, bucket, _ = _almacen()
    hasta = datetime.now(timezone.utc) + timedelta(days=10)
    almacen.fijar_retencion("org/abc", hasta)
    assert bucket.retenciones["org/abc"] == ("Unlocked", hasta)
    assert not [x for x in bucket.llamadas if "delete" in x]
    assert not hasattr(BlobFalso, "delete")


class AlmacenFalsoConEscrituraUnica:
    """Hace lo que el almacén: si la subida lleva la cabecera firmada, una clave existente se rechaza."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def firmar_subida(self, clave, tipo_mime):
        almacen, bucket, _ = _almacen()
        return almacen.firmar_subida(clave, tipo_mime)

    def subir(self, firma, contenido: bytes) -> None:
        if firma.cabeceras.get(CABECERA_ESCRITURA_UNICA) == "0" and firma.clave in self.objetos:
            raise FileExistsError("412 Precondition Failed")
        self.objetos[firma.clave] = contenido


def test_una_segunda_subida_de_la_misma_clave_se_rechaza():
    falso = AlmacenFalsoConEscrituraUnica()
    firma = falso.firmar_subida("org/clave", "text/plain")
    falso.subir(firma, b"uno")
    with pytest.raises(FileExistsError):
        falso.subir(firma, b"dos")
    assert falso.objetos["org/clave"] == b"uno"


def test_fuera_de_la_nube_falla_cerrado_sin_conectar(monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setenv(gcs.VARIABLE_BUCKET, "bucket-pruebas")
    conocidos = {m for m in sys.modules if m.startswith("google.cloud")}
    with pytest.raises(AlmacenNoDisponible):
        gcs.almacen_por_defecto()
    with pytest.raises(ErrorNegocio) as info:
        motor.almacen_de_evidencias()
    assert info.value.code == "EVI_ALMACEN_NO_DISPONIBLE" and info.value.status_code == 503
    assert {m for m in sys.modules if m.startswith("google.cloud")} == conocidos


def test_en_la_nube_sin_bucket_tambien_falla_cerrado(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "evydentia-api")
    monkeypatch.delenv(gcs.VARIABLE_BUCKET, raising=False)
    with pytest.raises(AlmacenNoDisponible):
        gcs.almacen_por_defecto()


class AlmacenSoloFirma:
    def firmar_subida(self, clave, tipo_mime):
        return gcs.FirmaSubida(clave=clave, url="https://storage.invalid/x", cabeceras={})


@pytest.mark.parametrize(
    "nombre,tipo,tamano,codigo",
    [
        ("virus.exe", "application/x-msdownload", 10, "EVIDENCE_TYPE_NOT_ALLOWED"),
        ("a.png", "application/pdf", 10, "EVIDENCE_TYPE_NOT_ALLOWED"),
        ("grande.pdf", "application/pdf", 11 * 1024 * 1024, "EVIDENCE_TOO_LARGE"),
    ],
)
def test_pedir_la_subida_valida_nombre_tipo_y_tamano_con_las_reglas_de_sec05(nombre, tipo, tamano, codigo):
    with pytest.raises(ErrorNegocio) as info:
        motor.pedir_subida(AlmacenSoloFirma(), "org-a", "dpo", False, nombre, tipo, tamano)
    assert info.value.code == codigo


def test_la_clave_lleva_el_prefijo_de_la_organizacion_y_un_identificador_aleatorio():
    claves = {
        motor.pedir_subida(AlmacenSoloFirma(), "org-a", "dpo", False, "a.pdf", "application/pdf", 10).clave
        for _ in range(3)
    }
    assert len(claves) == 3
    assert all(c.startswith("org-a/") and len(c.split("/")[1]) == 32 for c in claves)


@pytest.mark.parametrize(
    "tipo,contenido,esperado",
    [
        ("application/pdf", b"%PDF-1.4 ...", True),
        ("application/pdf", b"PK\x03\x04", False),
        ("image/png", b"\x89PNG\r\n\x1a\n....", True),
        ("image/jpeg", b"\xff\xd8\xff\xe0....", True),
        ("image/jpeg", b"\x89PNG\r\n\x1a\n", False),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK\x03\x04..", True),
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"%PDF-", False),
        ("text/plain", "texto con ñ".encode("utf-8"), True),
        ("text/csv", b"a,b\x00c", False),
        ("text/plain", b"\xff\xfe\xfa", False),
        ("application/x-otro", b"%PDF-", False),
    ],
)
def test_la_firma_del_formato_debe_corresponder_al_tipo(tipo, contenido, esperado):
    assert motor.firma_de_formato_valida(tipo, contenido) is esperado
