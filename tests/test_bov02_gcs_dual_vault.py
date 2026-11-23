# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤boveda-cloud ¤conservacion ¤evidencias ¤arbitro
"""BOV-02: enrutamiento de la bóveda dual y URLs firmadas V4 directas a Cloud Storage.

Sin red ni nube: el firmador es un doble que registra lo que se le pide firmar. Las pruebas de base de datos
corren contra la PostgreSQL 16 del arnés con el rol `lopdp_app` y llaman a `exigir_base_de_pruebas()`.
Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from conftest import exigir_base_de_pruebas

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()
from api.errores import ErrorNegocio  # noqa: E402
from features.boveda_cloud import boveda_cloud_service as svc  # noqa: E402
from features.boveda_cloud.services import gcs_dual_vault_engine as motor  # noqa: E402

GB = 1024**3
SHA = "ab" * 32


class FirmadorFalso:
    def __init__(self):
        self.llamadas = []

    def firmar(self, bucket, clave, metodo, cabeceras):
        self.llamadas.append((bucket, clave, metodo, dict(cabeceras)))
        return f"https://storage.invalid/{bucket}/{clave}?X-Goog-Signature=firma"


# Sin base de datos ------------------------------------------------------------------------------
def test_enrutamiento_short_ttl_sin_autoclass_15_dias():
    """Mutación: cambiar el umbral a `<= 15`/`< 10`, o activar Autoclass en el tier corto → rojo."""
    d = motor.resolver_destino(15)
    assert (d.bucket, d.storage_class, d.autoclass, d.object_lock_worm, d.lifecycle_delete_days) == (
        "lopdp360-vault-short-ttl", "STANDARD", False, False, 15)
    assert motor.resolver_destino(29).bucket == motor.BUCKET_CORTO
    assert motor.worm_lock_hasta(15) is None


def test_enrutamiento_long_retention_autoclass_worm():
    """Mutación: quitar `object_lock_worm` o `autoclass` del tier largo, o mover el umbral a `> 30` → rojo."""
    d = motor.resolver_destino(1825)
    assert (d.bucket, d.autoclass, d.object_lock_worm, d.lifecycle_delete_days) == (
        "lopdp360-vault-long-retention", True, True, None)
    assert motor.resolver_destino(30).bucket == motor.BUCKET_LARGO  # justo en el umbral
    ahora = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert motor.worm_lock_hasta(1825, ahora) == ahora + timedelta(days=1825)


def test_retencion_no_positiva_se_rechaza():
    """Mutación: aceptar 0 o negativos → rojo."""
    for dias in (0, -5):
        with pytest.raises(ValueError):
            motor.resolver_destino(dias)


def test_subida_firma_content_length_y_sha256_y_acota_el_prefijo():
    """Mutación: no firmar `Content-Length` o `x-goog-content-sha256`, o salirse de `{tenant}/{categoria}/{objeto}` → rojo."""
    f = FirmadorFalso()
    destino, firma = motor.firmar_subida(f, "org-1", "videovigilancia", "obj-9", 15, 2048, SHA.upper())
    bucket, clave, metodo, cabeceras = f.llamadas[0]
    assert (bucket, clave, metodo) == (destino.bucket, "org-1/videovigilancia/obj-9", "PUT")
    assert cabeceras == {"Content-Length": "2048", "x-goog-content-sha256": SHA}
    assert firma.metodo == "PUT" and firma.cabeceras == cabeceras
    assert motor.clave_pertenece_a_tenant(clave, "org-1")
    assert not motor.clave_pertenece_a_tenant(clave, "org-2")


def test_clave_rechaza_segmentos_que_escapan_del_prefijo():
    """Mutación: aceptar `..`, `/` o vacío en un segmento → rojo (otro tenant podría quedar al alcance)."""
    for tenant, cat, obj in (("org/../x", "c", "o"), ("org", "../c", "o"), ("org", "c", "a/b"), ("", "c", "o"), ("org", "c", "..")):
        with pytest.raises(motor.ClaveInvalida):
            motor.construir_clave(tenant, cat, obj)
    assert not motor.clave_pertenece_a_tenant("org-2/c/o/../../org-1/c/o", "org-1")


def test_descarga_get_sin_cabeceras_y_solo_buckets_de_la_boveda():
    """Mutación: firmar un bucket arbitrario → rojo."""
    f = FirmadorFalso()
    firma = motor.firmar_descarga(f, motor.BUCKET_LARGO, "org-1", "contratos", "obj-1")
    assert f.llamadas == [(motor.BUCKET_LARGO, "org-1/contratos/obj-1", "GET", {})]
    assert firma.metodo == "GET"
    with pytest.raises(ValueError):
        motor.firmar_descarga(f, "otro-bucket", "org-1", "c", "o")


def test_sha256_y_tamano_invalidos_no_firman():
    """Mutación: firmar sin validar la huella o con tamaño cero → rojo."""
    f = FirmadorFalso()
    with pytest.raises(ValueError):
        motor.firmar_subida(f, "org-1", "c", "o", 15, 10, "no-es-sha")
    with pytest.raises(ValueError):
        motor.firmar_subida(f, "org-1", "c", "o", 15, 0, SHA)
    assert f.llamadas == []


def test_fuera_de_la_nube_falla_cerrado(monkeypatch):
    """Mutación: crear un cliente de Cloud Storage fuera de Cloud Run → rojo (no debe intentar conectar)."""
    monkeypatch.setattr(motor, "corre_en_cloud_run", lambda: False)
    with pytest.raises(motor.AlmacenBovedaNoDisponible):
        motor.firmador_por_defecto()
    with pytest.raises(ErrorNegocio) as e:
        svc._firmador()
    assert (e.value.code, e.value.status_code) == ("BOVEDA_ALMACEN_NO_DISPONIBLE", 503)


def test_motor_no_importa_otras_salas():
    """Mutación: importar `features.<otra_sala>` desde el motor → rojo (ADPA: solo pasillos y compuertas)."""
    import ast

    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "features", "boveda_cloud", "services", "gcs_dual_vault_engine.py")
    with open(ruta, encoding="utf-8") as f:
        for nodo in ast.walk(ast.parse(f.read())):
            modulo = getattr(nodo, "module", None) or ""
            assert not modulo.startswith("features."), modulo


# Base de datos ----------------------------------------------------------------------------------
async def _con_lopdp_app(cuerpo):
    """Dos organizaciones con plan INICIAL y una sesión `lopdp_app` en una transacción que se deshace."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    exigir_base_de_pruebas()
    url = os.environ["TEST_DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"bov02-a-{sufijo}", f"bov02-b-{sufijo}"
    try:
        async with engine.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                for t in (a, b):
                    await conexion.execute(
                        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                             "VALUES (:t, :t, :t, :t)"), {"t": t})
                    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t})
                    await conexion.execute(
                        text("INSERT INTO boveda_suscripciones_tenant (tenant_id, paquete_codigo, "
                             "cuota_almacenamiento_bytes, cuota_egress_mensual_bytes) "
                             "VALUES (:t, 'INICIAL', :a, :e)"), {"t": t, "a": 10 * GB, "e": 5000})
                await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as s:
                    await cuerpo(s, a, b)
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()


def _solicitud(dias, tamano=1000, categoria="evidencias"):
    return svc.SolicitudUrlSubida(categoria=categoria, retencion_dias=dias, tamano_bytes=tamano, sha256=SHA)


@pytest.mark.asyncio
async def test_registro_de_custodia_por_tier_y_cuota():
    """Mutación: registrar el bucket equivocado, no sumar el uso a la cuota, o `worm_lock_hasta` NULL en el tier largo → rojo."""
    from sqlalchemy import text

    async def cuerpo(s, a, b):
        f = FirmadorFalso()
        corto = await svc.solicitar_url_subida(s, a, _solicitud(15), "u1", f)
        largo = await svc.solicitar_url_subida(s, a, _solicitud(1825, 2000, "contratos"), "u1", f)
        assert corto.bucket_destino == "lopdp360-vault-short-ttl" and largo.bucket_destino == "lopdp360-vault-long-retention"
        assert f.llamadas[0][1] == f"{a}/evidencias/{corto.objeto_id}"
        filas = (await s.execute(text(
            "SELECT retencion_dias, bucket_destino, autoclass_activo, worm_lock_hasta IS NOT NULL "
            "FROM boveda_objetos_custodia ORDER BY retencion_dias"))).all()
        assert [tuple(x) for x in filas] == [
            (15, "lopdp360-vault-short-ttl", False, False), (1825, "lopdp360-vault-long-retention", True, True)]
        assert (await s.execute(text("SELECT uso_almacenamiento_bytes FROM boveda_suscripciones_tenant"))).scalar() == 3000

    await _con_lopdp_app(cuerpo)


@pytest.mark.asyncio
async def test_aislamiento_de_prefijos_y_rls_entre_tenants():
    """Mutación: consultar el objeto sin `tenant_id`, o quitar la política RLS → rojo (b vería el objeto de a)."""
    async def cuerpo(s, a, b):
        f = FirmadorFalso()
        subida = await svc.solicitar_url_subida(s, a, _solicitud(30), "u1", f)
        with pytest.raises(ErrorNegocio) as e:
            await svc.solicitar_url_descarga(s, b, subida.objeto_id, "u2", f)
        assert (e.value.code, e.value.status_code) == ("BOVEDA_OBJETO_NO_ENCONTRADO", 404)
        descarga = await svc.solicitar_url_descarga(s, a, subida.objeto_id, "u1", f)
        assert descarga.metodo == "GET" and f.llamadas[-1][1] == f"{a}/evidencias/{subida.objeto_id}"

    await _con_lopdp_app(cuerpo)


@pytest.mark.asyncio
async def test_cuota_de_almacenamiento_y_egress_bloquean_la_firma():
    """Mutación: firmar antes de validar la cuota → rojo (el firmador no debe recibir llamadas rechazadas)."""
    async def cuerpo(s, a, b):
        f = FirmadorFalso()
        with pytest.raises(ErrorNegocio) as e:
            await svc.solicitar_url_subida(s, a, _solicitud(15, 11 * GB), "u1", f)
        assert (e.value.code, e.value.status_code) == ("BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA", 409)
        ok = await svc.solicitar_url_subida(s, a, _solicitud(15, 4000), "u1", f)
        n = len(f.llamadas)
        with pytest.raises(ErrorNegocio) as e:
            await svc.solicitar_url_descarga(s, a, ok.objeto_id, "u1", f)  # 4000 de 5000: cabe
            await svc.solicitar_url_descarga(s, a, ok.objeto_id, "u1", f)  # 8000 de 5000: rechazada
        assert e.value.code == "BOVEDA_CUOTA_EGRESS_EXCEDIDA"
        assert len(f.llamadas) == n + 1

    await _con_lopdp_app(cuerpo)


@pytest.mark.asyncio
async def test_tabla_inmutable_para_lopdp_app():
    """Mutación: conceder UPDATE o DELETE a lopdp_app sobre boveda_objetos_custodia → rojo."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    async def cuerpo(s, a, b):
        subida = await svc.solicitar_url_subida(s, a, _solicitud(15), "u1", FirmadorFalso())
        for sentencia in ("UPDATE boveda_objetos_custodia SET retencion_dias = 1",
                          "DELETE FROM boveda_objetos_custodia"):
            with pytest.raises(DBAPIError):
                async with s.begin_nested():
                    await s.execute(text(sentencia))
        assert subida.objeto_id

    await _con_lopdp_app(cuerpo)
