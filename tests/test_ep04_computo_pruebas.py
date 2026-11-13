# ¤entorno-pruebas ¤cloud-run-perf
"""EP-04: cómputo, acceso y presupuesto del entorno de pruebas (PRD EVYDENTIA §5.5, invariantes 54, 55 y 56).

Árbitro estático sobre los manifiestos de governance/operaciones/entornos/pruebas/: no toca Google Cloud.
Cada comprobación tiene su mutación: una prueba aplica el cambio dañino a una copia en memoria y exige que
el detector lo vea. Mutaciones de la opción A (Arquitecto, 2026-11-08): `allUsers` en el invoker del backend
rompe la prueba de invocación; `PROXY_AUTH_CLOUD_RUN=ninguna` rompe la del proxy del frontend.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
OPERACIONES = RAIZ / "governance" / "operaciones"
PRUEBAS = OPERACIONES / "entornos" / "pruebas"
ARCHIVOS = ("proyecto", "cloudrun_backend", "cloudrun_frontend", "cloudrun_vault_worker", "acceso_iap", "presupuesto")


def _docs(ruta: Path) -> list[dict]:
    datos = leer_yaml(ruta.read_text(encoding="utf-8"))
    return datos if isinstance(datos, list) else [datos]


def _servicio(nombre: str) -> dict:
    return _docs(PRUEBAS / f"{nombre}.yaml")[0]


def _iam(nombre: str) -> dict:
    return _docs(PRUEBAS / f"{nombre}.yaml")[1]


def _contenedor(servicio: dict) -> dict:
    return servicio["spec"]["template"]["spec"]["containers"][0]


def _env(servicio: dict) -> dict[str, dict]:
    return {e["name"]: e for e in _contenedor(servicio)["env"]}


def _anotaciones(servicio: dict) -> dict:
    return servicio["metadata"]["annotations"]


def _plantilla(servicio: dict) -> dict:
    return servicio["spec"]["template"]["metadata"]["annotations"]


# --- Diferencias con producción ---------------------------------------------------------------------

BASES = {
    "cloudrun_backend": OPERACIONES / "cloudrun_service.yaml",
    "cloudrun_frontend": OPERACIONES / "cloudrun_frontend_service.yaml",
}

# Lo que el §5.5 permite cambiar: proyecto (cuentas, conector, secretos, URL), escala, acceso e identidad de entorno.
CLAVES_ADMITIDAS = (
    "metadata > labels",
    "metadata > annotations > run.googleapis.com/ingress",
    "metadata > annotations > run.googleapis.com/invoker-iam-disabled",
    "metadata > annotations > run.googleapis.com/iap-enabled",
    "spec > template > metadata > annotations > autoscaling.knative.dev/minScale",
    "spec > template > metadata > annotations > autoscaling.knative.dev/maxScale",
    "spec > template > metadata > annotations > run.googleapis.com/vpc-access-connector",
    "spec > template > spec > serviceAccountName",
    "spec > template > spec > containers > [0] > image",
    "spec > template > spec > containers > [0] > env > [APP_ENV]",
    "spec > template > spec > containers > [0] > env > [NEXT_PUBLIC_APP_ENV]",
    "spec > template > spec > containers > [0] > env > [AUTH_MODE]",
    "spec > template > spec > containers > [0] > env > [HUELLA_PROYECTO_PRODUCCION]",
    "spec > template > spec > containers > [0] > env > [ENTORNO_CORREOS_PERMITIDOS]",
    "spec > template > spec > containers > [0] > env > [GOOGLE_CLIENT_ID]",
    "spec > template > spec > containers > [0] > env > [BACKEND_URL]",
    "spec > template > spec > containers > [0] > env > [PROXY_AUTH_CLOUD_RUN]",
    "spec > template > spec > containers > [0] > env > [DATABASE_URL]",
)


def _aplanar(dato, prefijo: str = "") -> dict:
    sep = " > "
    if isinstance(dato, dict):
        plano = {}
        for clave, valor in dato.items():
            plano.update(_aplanar(valor, f"{prefijo}{sep if prefijo else ''}{clave}"))
        return plano
    if isinstance(dato, list):
        plano = {}
        for i, valor in enumerate(dato):
            nombre = valor.get("name") if isinstance(valor, dict) else None
            etiqueta = f"[{nombre}]" if nombre and prefijo.endswith(("env", "ports")) else f"[{i}]"
            plano.update(_aplanar(valor, f"{prefijo}{sep}{etiqueta}"))
        return plano
    return {prefijo: dato}


def _prohibidas(base: dict, pruebas: dict) -> list[str]:
    a, b = _aplanar(base), _aplanar(pruebas)
    distintas = {c for c in a.keys() | b.keys() if a.get(c) != b.get(c)}
    return sorted(c for c in distintas if not any(c == k or c.startswith(k + " > ") for k in CLAVES_ADMITIDAS))


def _base(nombre: str) -> dict:
    return _docs(BASES[nombre])[0]


@pytest.mark.parametrize("nombre", sorted(BASES))
def test_el_manifiesto_solo_difiere_de_produccion_en_lo_permitido(nombre):
    assert _prohibidas(_base(nombre), _servicio(nombre)) == []


def test_mutacion_un_cambio_no_permitido_se_detecta():
    mutado = copy.deepcopy(_servicio("cloudrun_backend"))
    _contenedor(mutado)["resources"]["limits"]["cpu"] = "4"
    assert any("cpu" in c for c in _prohibidas(_base("cloudrun_backend"), mutado))


@pytest.mark.parametrize("nombre", sorted(BASES))
def test_mismo_nombre_de_servicio_que_en_produccion(nombre):
    assert _servicio(nombre)["metadata"]["name"] == _base(nombre)["metadata"]["name"]


# --- Imágenes por digest y escala -------------------------------------------------------------------

POR_DIGEST = re.compile(r"^IMAGEN_POR_DIGEST$|@sha256:[0-9a-f]{64}$")
SERVICIOS = ("cloudrun_backend", "cloudrun_frontend", "cloudrun_vault_worker")


def _por_digest(imagen: str) -> bool:
    return bool(POR_DIGEST.search(imagen)) and not re.search(r":[A-Za-z0-9._-]+$", imagen.split("@")[0])


@pytest.mark.parametrize("nombre", SERVICIOS)
def test_las_imagenes_van_por_digest_y_no_por_etiqueta(nombre):
    assert _por_digest(_contenedor(_servicio(nombre))["image"])


def test_mutacion_una_etiqueta_no_pasa_por_digest():
    assert not _por_digest("us-central1-docker.pkg.dev/PROYECTO_PRUEBAS/repo/evydentia:latest")
    assert _por_digest("us-central1-docker.pkg.dev/PROYECTO_PRUEBAS/repo/evydentia@sha256:" + "a" * 64)


@pytest.mark.parametrize("nombre", SERVICIOS)
def test_minimo_cero_y_maximo_acotado(nombre):
    anot = _plantilla(_servicio(nombre))
    assert anot["autoscaling.knative.dev/minScale"] == "0"
    maximo = int(anot["autoscaling.knative.dev/maxScale"])
    assert 1 <= maximo <= 5
    if nombre in BASES:
        produccion = int(_plantilla(_base(nombre))["autoscaling.knative.dev/maxScale"])
        assert maximo < produccion, "el máximo de pruebas debe ser menor que el de producción (GCP-05)"


# --- Variables de entorno y secretos ----------------------------------------------------------------

def test_el_backend_declara_la_identidad_del_entorno():
    env = _env(_servicio("cloudrun_backend"))
    assert env["APP_ENV"]["value"] == "pruebas"
    assert env["AUTH_MODE"]["value"] == "oidc"
    assert env["HUELLA_PROYECTO_PRODUCCION"]["value"]
    assert "ENTORNO_CORREOS_PERMITIDOS" in env
    assert env["ENTORNO_CORREOS_PERMITIDOS"]["value"] == ""   # el correo queda apagado (decisión del 2026-11-07)


def test_el_frontend_declara_la_identidad_del_entorno():
    env = _env(_servicio("cloudrun_frontend"))
    assert env["APP_ENV"]["value"] == "pruebas"
    assert env["NEXT_PUBLIC_APP_ENV"]["value"] == "pruebas"


def test_el_vault_worker_declara_la_identidad_del_entorno():
    env = _env(_servicio("cloudrun_vault_worker"))
    assert env["APP_ENV"]["value"] == "pruebas"
    assert env["HUELLA_PROYECTO_PRODUCCION"]["value"]
    assert _servicio("cloudrun_vault_worker")["metadata"]["name"] == "evydentia-vault-worker"


# El vault_worker no tiene manifiesto de producción (lo crea GOVW-01). Lista cerrada de excepciones a la paridad:
# solo vale mientras ese manifiesto no exista; si aparece, la prueba falla hasta quitar la excepción y comparar.
EXCEPCIONES_DE_PARIDAD = {"cloudrun_vault_worker": "GOVW-01"}
INVOCADOR_DEL_WORKER = ["serviceAccount:sa-eventarc-pruebas@PROYECTO_PRUEBAS.iam.gserviceaccount.com"]


def _manifiesto_de_produccion_del_worker(carpeta: Path) -> list[Path]:
    return [
        r for r in sorted(carpeta.glob("*.yaml"))
        if "vault_worker" in r.name or "evydentia-vault-worker" in r.read_text(encoding="utf-8")
    ]


def test_el_worker_solo_es_excepcion_mientras_produccion_no_tenga_su_manifiesto():
    assert EXCEPCIONES_DE_PARIDAD == {"cloudrun_vault_worker": "GOVW-01"}
    assert _manifiesto_de_produccion_del_worker(OPERACIONES) == [], (
        "ya existe el manifiesto de producción del vault_worker: quita la excepción y compáralo como los demás"
    )


def test_mutacion_un_manifiesto_de_produccion_del_worker_se_detecta(tmp_path):
    (tmp_path / "cloudrun_vault_worker_service.yaml").write_text("", encoding="utf-8")
    assert _manifiesto_de_produccion_del_worker(tmp_path)


def test_el_worker_coincide_con_el_backend_en_lo_comun():
    worker, backend = _servicio("cloudrun_vault_worker"), _servicio("cloudrun_backend")
    assert _anotaciones(worker)["run.googleapis.com/ingress"] == _anotaciones(backend)["run.googleapis.com/ingress"]
    assert _env(worker)["APP_ENV"]["value"] == _env(backend)["APP_ENV"]["value"]
    assert _env(worker)["HUELLA_PROYECTO_PRODUCCION"] == _env(backend)["HUELLA_PROYECTO_PRODUCCION"]
    assert worker["spec"]["template"]["spec"]["serviceAccountName"].endswith("-pruebas@PROYECTO_PRUEBAS.iam.gserviceaccount.com")
    assert "run.googleapis.com/iap-enabled" not in _anotaciones(worker)


def test_al_worker_solo_lo_invoca_la_cuenta_del_disparador_de_eventarc():
    assert _invocadores(_iam("cloudrun_vault_worker")) == INVOCADOR_DEL_WORKER
    assert "run.googleapis.com/invoker-iam-disabled" not in _anotaciones(_servicio("cloudrun_vault_worker"))


def test_mutacion_allusers_en_el_worker_se_detecta():
    politica = copy.deepcopy(_iam("cloudrun_vault_worker"))
    politica["bindings"][0]["members"].append("allUsers")
    assert _invocadores(politica) != INVOCADOR_DEL_WORKER


def test_ningun_servicio_declara_el_secreto_oauth_y_el_backend_usa_el_cliente_de_pruebas():
    """CONFIGURACION_LOGIN_GOOGLE.md prohíbe GOOGLE_CLIENT_SECRET; el cliente de IAP lo gestiona Google."""
    for nombre in SERVICIOS:
        assert "GOOGLE_CLIENT_SECRET" not in _env(_servicio(nombre)), nombre
    cliente = _env(_servicio("cloudrun_backend"))["GOOGLE_CLIENT_ID"]["value"]
    assert cliente == "CLIENT_ID_OAUTH_DE_PRUEBAS"
    assert not re.search(r"\.apps\.googleusercontent\.com", cliente)


def test_nadie_usa_auth_mode_headers():
    for nombre in SERVICIOS:
        env = _env(_servicio(nombre))
        assert env.get("AUTH_MODE", {}).get("value") != "headers", nombre


def _cuenta(servicio: dict) -> str:
    return servicio["spec"]["template"]["spec"]["serviceAccountName"].split("@")[0]


def _secretos() -> dict[str, list[str]]:
    secretos = leer_yaml((PRUEBAS / "secretos.yaml").read_text(encoding="utf-8"))["secretos"]
    return {s["nombre"]: s["leen"] for s in secretos}


@pytest.mark.parametrize("nombre", SERVICIOS)
def test_los_secretos_son_referencias_a_secretos_del_proyecto_que_la_cuenta_puede_leer(nombre):
    servicio = _servicio(nombre)
    registrados = _secretos()
    for variable in _env(servicio).values():
        if "valueFrom" in variable:
            ref = variable["valueFrom"]["secretKeyRef"]["name"]
            assert ref in registrados, f"{ref} no está en secretos.yaml"
            assert _cuenta(servicio) in registrados[ref], f"{_cuenta(servicio)} no lee {ref}"
        else:
            assert "value" in variable


def test_las_cuentas_de_servicio_existen_y_son_solo_del_proyecto_de_pruebas():
    proyecto = leer_yaml((PRUEBAS / "proyecto.yaml").read_text(encoding="utf-8"))
    definidas = {c["nombre"] for c in proyecto["cuentas_de_servicio"]}
    for nombre in SERVICIOS:
        servicio = _servicio(nombre)
        assert _cuenta(servicio) in definidas
        assert servicio["spec"]["template"]["spec"]["serviceAccountName"].endswith("@PROYECTO_PRUEBAS.iam.gserviceaccount.com")
    for lectoras in _secretos().values():
        assert set(lectoras) <= definidas
    assert proyecto["aislamiento"]["permisos_en_el_proyecto_de_produccion"] == "ninguno"
    assert proyecto["aislamiento"]["produccion_con_permisos_en_pruebas"] == "ninguno"


# --- Opción A del borde -----------------------------------------------------------------------------

def _invocadores(politica: dict) -> list[str]:
    return [m for b in politica["bindings"] if b["role"] == "roles/run.invoker" for m in b["members"]]


def _solo_el_frontend_invoca(servicio: dict, politica: dict) -> bool:
    anot = _anotaciones(servicio)
    miembros = _invocadores(politica)
    return (
        "run.googleapis.com/invoker-iam-disabled" not in anot
        and miembros == ["serviceAccount:sa-frontend-pruebas@PROYECTO_PRUEBAS.iam.gserviceaccount.com"]
        and not any(m in ("allUsers", "allAuthenticatedUsers") for m in miembros)
    )


def test_el_backend_solo_lo_invoca_la_cuenta_del_frontend():
    assert _solo_el_frontend_invoca(_servicio("cloudrun_backend"), _iam("cloudrun_backend"))
    assert "run.googleapis.com/iap-enabled" not in _anotaciones(_servicio("cloudrun_backend"))


def test_mutacion_allusers_en_el_backend_rompe_la_comprobacion():
    politica = copy.deepcopy(_iam("cloudrun_backend"))
    politica["bindings"][0]["members"].append("allUsers")
    assert not _solo_el_frontend_invoca(_servicio("cloudrun_backend"), politica)
    servicio = copy.deepcopy(_servicio("cloudrun_backend"))
    _anotaciones(servicio)["run.googleapis.com/invoker-iam-disabled"] = "true"
    assert not _solo_el_frontend_invoca(servicio, _iam("cloudrun_backend"))


RUN_APP = re.compile(r"^https://[a-z0-9-]+(-[A-Z_]+)?\.[a-z0-9-]+\.run\.app$|^https://[\w.-]+\.run\.app$")


def _proxy_correcto(servicio: dict) -> bool:
    env = _env(servicio)
    return (
        env["PROXY_AUTH_CLOUD_RUN"]["value"] == "token_servicio"
        and bool(RUN_APP.match(env["BACKEND_URL"]["value"]))
        and _anotaciones(servicio).get("run.googleapis.com/iap-enabled") == "true"
    )


def test_el_frontend_tiene_iap_proxy_con_token_y_backend_run_app():
    assert _proxy_correcto(_servicio("cloudrun_frontend"))


def test_mutacion_proxy_sin_token_rompe_la_comprobacion():
    servicio = copy.deepcopy(_servicio("cloudrun_frontend"))
    _env(servicio)["PROXY_AUTH_CLOUD_RUN"]["value"] = "ninguna"
    assert not _proxy_correcto(servicio)


def _iap_valido(acceso: dict) -> bool:
    iap = acceso["iap"]
    return not (iap["servicio"]["habilitado"] and iap["balanceador"]["habilitado"]) and (
        iap["servicio"]["habilitado"] or iap["balanceador"]["habilitado"]
    )


def test_iap_esta_en_el_servicio_y_no_en_el_balanceador():
    acceso = leer_yaml((PRUEBAS / "acceso_iap.yaml").read_text(encoding="utf-8"))
    assert acceso["opcion"] == "A"
    assert acceso["iap"]["servicio"]["habilitado"] is True
    assert acceso["iap"]["balanceador"]["habilitado"] is False
    assert _iap_valido(acceso)
    assert acceso["acceso"]["rol"] == "roles/iap.httpsResourceAccessor"
    assert not any(m in ("allUsers", "allAuthenticatedUsers") for m in acceso["acceso"]["miembros"])


def test_mutacion_iap_en_los_dos_lados_se_detecta():
    acceso = leer_yaml((PRUEBAS / "acceso_iap.yaml").read_text(encoding="utf-8"))
    acceso["iap"]["balanceador"]["habilitado"] = True
    assert not _iap_valido(acceso)


def test_el_frontend_no_declara_balanceador():
    texto = (PRUEBAS / "cloudrun_frontend.yaml").read_text(encoding="utf-8")
    assert "internal-and-cloud-load-balancing" not in texto
    assert _anotaciones(_servicio("cloudrun_frontend"))["run.googleapis.com/ingress"] == "all"


# --- Presupuesto ------------------------------------------------------------------------------------

def test_presupuestos_con_avisos_al_50_90_y_100_y_sin_cortar_el_gasto():
    p = leer_yaml((PRUEBAS / "presupuesto.yaml").read_text(encoding="utf-8"))
    assert [float(u) for u in p["umbrales"]] == [0.5, 0.9, 1.0]   # el lector común devuelve los decimales como texto
    assert p["corta_el_gasto"] is False
    assert {x["nombre"] for x in p["presupuestos"]} == {"pruebas-total", "pruebas-vertex-ai", "pruebas-cloud-storage"}
    assert {x["nombre"]: int(x["monto_mensual"]) for x in p["presupuestos"]} == {
        "pruebas-total": 30, "pruebas-vertex-ai": 15, "pruebas-cloud-storage": 5}
    assert p["canal_de_aviso"]
    texto = (PRUEBAS / "presupuesto.yaml").read_text(encoding="utf-8").lower()
    assert not re.search(r"disable.?billing|desactivar.{0,20}facturaci|pubsub", texto)


# --- Sin valores ni identificadores de producción ---------------------------------------------------

VALOR = re.compile(
    r"(postgres(ql)?(\+\w+)?://|BEGIN [A-Z ]*PRIVATE KEY|GOCSPX-|re_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{20,}|"
    r"ya29\.|AKIA[0-9A-Z]{16})"
)
PRODUCCION = ("app.evydentia.com", "lopdp360-vault-short-ttl", "lopdp360-vault-long-retention", "evydentia-web-pruebas")


@pytest.mark.parametrize("nombre", ARCHIVOS)
def test_ningun_archivo_lleva_claves_urls_de_conexion_ni_identificadores_de_produccion(nombre):
    texto = (PRUEBAS / f"{nombre}.yaml").read_text(encoding="utf-8")
    assert not VALOR.search(texto)
    assert not [p for p in PRODUCCION if p in texto]
    assert not re.search(r"--project\s+(?!PROYECTO_PRUEBAS\b)\S+", texto)
    assert not re.search(r"projects/(?!PROYECTO_PRUEBAS\b)[\w-]+", texto)
    assert not re.search(r"@(?!PROYECTO_PRUEBAS\.iam|gcp-sa-iap)[\w-]+\.iam\.gserviceaccount\.com", texto)


def test_mutacion_una_url_de_conexion_se_detecta():
    assert VALOR.search("DATABASE_URL: postgresql://u:p@h/db")


# --- Documento operativo ----------------------------------------------------------------------------

def test_el_brief_avisa_de_la_anotacion_de_iap_sin_documentar():
    seccion = (OPERACIONES / "ENTORNO_DE_PRUEBAS.md").read_text(encoding="utf-8").split("<!-- === EP-04 === -->")[1]
    assert "iap-enabled" in seccion and "no está documentada" in seccion
    assert "gcloud run services describe evydentia-web" in seccion


def test_la_seccion_ep04_del_documento_operativo_esta_escrita():
    texto = (OPERACIONES / "ENTORNO_DE_PRUEBAS.md").read_text(encoding="utf-8")
    seccion = texto.split("<!-- === EP-04 === -->")[1].split("<!-- === fin EP-04 === -->")[0]
    assert "Pendiente de EP-04" not in seccion
    for archivo in ARCHIVOS:
        assert f"{archivo}.yaml" in seccion, archivo
    assert "Brief para el propietario" in seccion
