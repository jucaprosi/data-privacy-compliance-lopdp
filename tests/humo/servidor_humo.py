# -*- coding: utf-8 -*-
# ¤arbitro ¤seguridad
"""Arrancador de la API para las pruebas de humo: OIDC real con una clave temporal.

Solo existe en pruebas. No hay variable de entorno que lo active en la aplicación: nada fuera de `tests/`
lo importa (`tests/test_servidor_humo.py`), así que `app_core/security.py` no gana ningún interruptor.

Corre el camino `oidc` entero (firma RS256, emisor, audiencia, vigencia, correo verificado, `users` y
membresía). Lo único que cambia es de dónde sale la clave pública: un RSA generado al arrancar, cuya parte
privada se escribe en HUMO_CLAVE_PRIVADA para que Playwright firme los tokens y muere con la corrida.

Se detiene ante Vercel o el host de producción, antes de generar nada.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping

HOST_PRODUCCION = "ep-late-hall"
PUERTO_POR_DEFECTO = 5200


def rechazo_de_entorno(entorno: Mapping[str, str]) -> str | None:
    """Motivo para no arrancar, o None. Pura: la prueba la ejercita sin levantar nada."""
    if entorno.get("HUMO_E2E") != "1":
        return "falta HUMO_E2E=1: este arrancador solo lo lanza frontend/playwright.humo.config.ts"
    if any(clave == "VERCEL" or clave.startswith("VERCEL_") for clave in entorno):
        return "corre en Vercel: un despliegue nunca usa este arrancador"
    urls = [entorno.get(clave, "") for clave in ("DATABASE_URL", "TEST_DATABASE_URL", "MIGRATION_DATABASE_URL")]
    if any(HOST_PRODUCCION in url for url in urls):
        return "la base apunta al host de producción"
    if not entorno.get("DATABASE_URL", "").strip():
        return "falta DATABASE_URL"
    if not entorno.get("GOOGLE_CLIENT_ID", "").strip():
        return "falta GOOGLE_CLIENT_ID"
    if not entorno.get("HUMO_CLAVE_PRIVADA", "").strip():
        return "falta HUMO_CLAVE_PRIVADA"
    return None


def generar_clave(ruta: Path):
    """Crea el RSA de esta corrida, deja la parte privada en `ruta` y devuelve la pública."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ruta.write_bytes(clave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    ruta.chmod(0o600)
    return clave.public_key()


def main() -> int:
    motivo = rechazo_de_entorno(os.environ)
    if motivo:
        print(f"[HUMO] No arranca: {motivo}.", file=sys.stderr)
        return 1

    os.environ.pop("AUTH_MODE", None)  # sin definir: modo oidc, el de producción
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    import uvicorn

    from app_core import security
    from main import app

    publica = generar_clave(Path(os.environ["HUMO_CLAVE_PRIVADA"]))
    security._clave_de_firma = lambda _token: publica

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("HUMO_PUERTO_API", PUERTO_POR_DEFECTO)), loop="none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
