# ¤¤qa-engineer
# ¤arbitro
"""DEP-01: Cloud Storage y Vertex AI (google-genai) en requirements.txt con versión exacta."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REQUISITOS = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
DOCKERFILE_PURGA = (RAIZ / "jobs" / "purga_demo" / "Dockerfile").read_text(encoding="utf-8")


def _linea(paquete: str) -> str:
    coincidencias = re.findall(rf"^{re.escape(paquete)}\s*([^\s#]*)", REQUISITOS, flags=re.MULTILINE)
    assert len(coincidencias) == 1, f"{paquete} debe aparecer una sola vez en requirements.txt"
    return coincidencias[0]


def test_importan_cloud_storage_y_genai():
    from google import genai
    from google.cloud import storage

    assert hasattr(storage, "Client")
    assert hasattr(genai, "Client")


def test_genai_acepta_vertexai_sin_llamar_a_google():
    from google import genai

    cliente = genai.Client(vertexai=True, project="proyecto-simulado", location="us-central1",
                           credentials=_CredencialFalsa())
    assert cliente.vertexai is True


def test_ambas_con_version_exacta():
    for paquete in ("google-cloud-storage", "google-genai"):
        especificador = _linea(paquete)
        assert re.fullmatch(r"==\d+(\.\d+)+", especificador), f"{paquete}: {especificador!r} no es ==x.y.z"
    assert ">=" not in re.findall(r"^google-(?:cloud-storage|genai).*$", REQUISITOS, flags=re.MULTILINE).__str__()


def test_cloud_storage_coincide_con_el_dockerfile_de_demo_05():
    en_dockerfile = re.search(r'google-cloud-storage==([\d.]+)', DOCKERFILE_PURGA)
    assert en_dockerfile, "el Dockerfile de jobs/purga_demo debe fijar google-cloud-storage"
    assert _linea("google-cloud-storage") == f"=={en_dockerfile.group(1)}"


class _CredencialFalsa:
    """Credencial simulada: google-genai la acepta sin contactar con Google al construir el cliente."""
    token = "simulado"
    expired = False
    valid = True
    quota_project_id = None

    def refresh(self, request):  # pragma: no cover
        raise AssertionError("no debe refrescarse en la prueba")

    def before_request(self, request, method, url, headers):  # pragma: no cover
        raise AssertionError("no debe usarse en la prueba")
