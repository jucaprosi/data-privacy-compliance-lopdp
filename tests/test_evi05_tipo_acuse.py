# ¤evidencias ¤arbitro
"""EVI-05: el tipo de evidencia «acuse» en la custodia de documentos generados, contra PostgreSQL 16.

Sin TEST_DATABASE_URL se omite. Reutiliza el doble de almacén y el contexto de EVI-04.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- m1 quitar `acuse` de `TIPOS_EVIDENCIA` -> test_acuse_se_custodia_y_devuelve_el_sha256_de_los_bytes
  y test_la_tupla_incluye_acuse_despues_de_exportacion.
- m2 admitir cualquier tipo (quitar la comprobación de pertenencia a la tupla) -> test_un_tipo_fuera_de_la_tupla_sigue_rechazado.
"""
import hashlib

import pytest

from features.evidencias.services.custodia_generados_engine import TIPOS_EVIDENCIA, CustodiaInvalida
from test_evi04_custodia_generados import AlmacenDoble, _custodiar, _leer, ctx  # noqa: F401

PDF_ACUSE = b"%PDF-1.7\nacuse de aceptacion\n"


def test_la_tupla_incluye_acuse_despues_de_exportacion():
    assert TIPOS_EVIDENCIA[-2:] == ("exportacion", "acuse")


@pytest.mark.asyncio
async def test_acuse_se_custodia_y_devuelve_el_sha256_de_los_bytes(ctx):  # noqa: F811
    almacen = AlmacenDoble()
    r = await _custodiar(ctx, ctx["a"], almacen, contenido=PDF_ACUSE, tipo_evidencia="acuse")
    huella = hashlib.sha256(PDF_ACUSE).hexdigest()
    assert r == {"evidencia_id": r["evidencia_id"], "sha256": huella, "tipo_evidencia": "acuse"}
    filas = await _leer(ctx, ctx["a"], "SELECT sha256 FROM evidencias_documentos WHERE tenant_id = :t")
    assert [f[0] for f in filas] == [huella]
    assert almacen.objetos == {f"{ctx['a']}/{huella}": PDF_ACUSE}


@pytest.mark.asyncio
async def test_un_tipo_fuera_de_la_tupla_sigue_rechazado(ctx):  # noqa: F811
    almacen = AlmacenDoble()
    with pytest.raises(CustodiaInvalida):
        await _custodiar(ctx, ctx["a"], almacen, contenido=PDF_ACUSE, tipo_evidencia="inventado")
    assert almacen.subidas == 0
