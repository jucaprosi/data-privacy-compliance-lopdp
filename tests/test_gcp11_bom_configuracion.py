"""GCP-11 · `exigir_configuracion_en_la_nube` nombra el BOM al inicio de DATABASE_URL.

`¤versionado-despliegue` `¤arbitro`. Solo URL ficticias (host `.invalid`) y contraseña aleatoria.

Mutación documentada: quitar la comprobación `url.startswith(MARCAS_DE_ORDEN_DE_BYTES)` de
`app_core/config.py#SEC-17` hace fallar `test_el_bom_se_nombra_sin_imprimir_el_valor`.
"""
import secrets

import pytest

from app_core.config import exigir_configuracion_en_la_nube

CORS = "https://app.ejemplo.invalid"


def _entorno(url: str) -> dict:
    return {"K_SERVICE": "evydentia-backend", "DATABASE_URL": url, "CORS_ORIGINS": CORS}


def _url(clave: str) -> str:
    return f"postgresql://lopdp_app:{clave}@bd.ejemplo.invalid/evydentia"


@pytest.mark.parametrize("marca", ["﻿", "ï»¿"])
def test_el_bom_se_nombra_sin_imprimir_el_valor(marca):
    clave = secrets.token_hex(8)
    with pytest.raises(RuntimeError) as error:
        exigir_configuracion_en_la_nube(_entorno(marca + _url(clave)))
    mensaje = str(error.value)
    assert "marca de orden de bytes" in mensaje and "DATABASE_URL" in mensaje
    assert clave not in mensaje and "postgresql://" not in mensaje and "ejemplo.invalid" not in mensaje


def test_una_url_valida_sin_bom_no_lanza():
    exigir_configuracion_en_la_nube(_entorno(_url(secrets.token_hex(8))))


def test_fuera_de_la_nube_no_hace_nada():
    exigir_configuracion_en_la_nube({"DATABASE_URL": "﻿postgresql://x"})
