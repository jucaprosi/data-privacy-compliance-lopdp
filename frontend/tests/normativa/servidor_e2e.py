# ¤inteligencia-normativa ¤vigilancia-spdp ¤arbitro
"""Backend real para el Playwright de NORM-02: siembra datos en la base local y arranca la API con un lector de originales.

Uso (desde la raíz del repositorio, con DATABASE_URL de la base local del arnés y AUTH_MODE=headers):

    python frontend/tests/normativa/servidor_e2e.py [puerto]

Sin datos simulados en el navegador: lo que ve la pantalla sale de esta base y de esta API. El lector de originales
es el único doble (el adaptador real llega con EVI-04) y sirve un PDF mínimo válido.
"""
import asyncio
import os
import sys
import uuid

import uvicorn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" \
      b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
OPERADOR = {"email": "operador@plataforma.test", "id": "n02-e2e-operador"}
MIEMBRO = {"u": "n02-e2e-miembro", "t": "n02-e2e-org"}


class LectorDeArchivo:
    def leer(self, clave):
        return PDF if clave.startswith("spdp/") else None


async def sembrar() -> None:
    url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
    motor = create_async_engine(url)
    async with async_sessionmaker(motor)() as s:
        await s.execute(text("TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
        await s.execute(text("DELETE FROM operadores_plataforma WHERE id = :i"), {"i": OPERADOR["id"]})
        await s.execute(text("INSERT INTO operadores_plataforma (id, email, nombre, activo, created_at, updated_at) "
                             "VALUES (:id, :email, 'Operador E2E', TRUE, NOW(), NOW())"), OPERADOR)
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": MIEMBRO["t"]})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": MIEMBRO["u"]})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": MIEMBRO["t"]})
        await s.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                             "VALUES (:t, 'Org E2E NORM', 'Org E2E NORM SA', 'RUCN02E2E')"), MIEMBRO)
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, 'miembro-n02@test.local', 'Miembro')"), MIEMBRO)
        await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                             "VALUES (:i, :u, :t, 'implementador')"), {"i": f"r-{uuid.uuid4().hex[:8]}", **MIEMBRO})
        for numero, anio, titulo in (("SPDP-SPD-2024-0001-R", 2024, "Instructivo de consentimiento"),
                                     ("SPDP-SPD-2025-0002-R", 2025, "Guía de evaluaciones de impacto"),
                                     ("SPDP-SPD-2026-0005-R", 2026, "Normas sobre videovigilancia")):
            await s.execute(text(
                "INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, organo_emisor, materia, url_fuente, "
                "seccion_fuente, archivo_sha256, ruta_original, tamano_bytes) VALUES (:n, :a, :t, 'SPDP', 'General', "
                "'https://spdp.example.invalid/x.pdf', 'resoluciones', :h, :r, :b)"),
                {"n": numero, "a": anio, "t": titulo, "h": uuid.uuid4().hex + uuid.uuid4().hex,
                 "r": f"spdp/{numero}.pdf", "b": len(PDF)})
        await s.commit()
    await motor.dispose()


def main() -> None:
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(sembrar())
    from features.inteligencia_normativa import inteligencia_normativa_service as svc
    from main import app

    svc.inyectar_lector_de_prueba(LectorDeArchivo())

    async def corrida_sin_red(origen):  # el disparo manual no sale a la red real de la SPDP
        from datetime import datetime, timezone

        from features.inteligencia_normativa.schemas import ResumenCorrida
        ahora = datetime.now(timezone.utc)
        async with svc._sesion() as s:
            id_ = (await s.execute(text(
                "INSERT INTO normativa_monitoreo_logs (inicio, fin, origen, estado, nuevos) "
                "VALUES (:i, :f, :o, 'ok', 1) RETURNING id::text"), {"i": ahora, "f": ahora, "o": origen})).scalar_one()
            await s.commit()
        return ResumenCorrida(id=id_, origen=origen, estado="ok", inicio=ahora, fin=ahora, nuevos=1)

    svc.ejecutar_monitoreo = corrida_sin_red
    config = uvicorn.Config(app, host="127.0.0.1", port=puerto, loop="none")
    # psycopg asíncrono no corre en el bucle Proactor de Windows: se pide el Selector.
    import selectors
    asyncio.run(uvicorn.Server(config).serve(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


if __name__ == "__main__":
    main()
