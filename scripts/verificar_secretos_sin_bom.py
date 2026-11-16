# ¤¤backend-developer
# ¤versionado-despliegue
"""GCP-11 · Árbitro de secretos sin BOM. LO EJECUTA EL PROPIETARIO; ninguna IA ni el CI lo corre.

    python scripts/verificar_secretos_sin_bom.py --proyecto evydentia [--version latest] [SECRETO ...]

Para cada secreto de Secret Manager lee el valor con `gcloud secrets versions access` (solo lectura),
conserva únicamente los TRES primeros bytes y comprueba que no sean la marca de orden de bytes UTF-8
(EF BB BF). Nunca imprime ni registra ningún valor: escribe el nombre del secreto y «sin BOM», «CON BOM»,
«vacío» o «no se pudo leer». Salida: 0 si todos están sin BOM; 1 si alguno tiene BOM, está vacío o no se
pudo leer.

Un BOM al inicio de DATABASE_URL hace que el esquema `postgresql://` no se reconozca y que el backend
muera al importar (INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED, app_core/config.py#SEC-17).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Callable

BOM_UTF8 = b"\xef\xbb\xbf"
SECRETOS_POR_DEFECTO = ("DATABASE_URL_APP", "JWT_SECRET", "SESSION_SECRET", "INVENTARIO_CLAVE_CIFRADO")


def leer_tres_bytes(proyecto: str, nombre: str, version: str) -> bytes | None:
    """Los tres primeros bytes del secreto, o None si no se pudo leer. El resto del valor se descarta."""
    try:
        corrida = subprocess.run(
            ["gcloud", "secrets", "versions", "access", version, f"--secret={nombre}", f"--project={proyecto}"],
            capture_output=True, timeout=60, check=False, shell=sys.platform == "win32",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if corrida.returncode != 0:
        return None
    return bytes(corrida.stdout[:3])


def estado(tres_bytes: bytes | None) -> str:
    if tres_bytes is None:
        return "no se pudo leer"
    if not tres_bytes:
        return "vacío"
    return "CON BOM" if tres_bytes == BOM_UTF8 else "sin BOM"


def verificar(proyecto: str, secretos, version: str = "latest",
              lector: Callable[[str, str, str], bytes | None] = leer_tres_bytes) -> tuple[int, list[str]]:
    lineas, malos = [], 0
    for nombre in secretos:
        resultado = estado(lector(proyecto, nombre, version))
        lineas.append(f"{nombre}: {resultado}")
        malos += resultado != "sin BOM"
    return (1 if malos else 0), lineas


def main(argv: list[str] | None = None, lector: Callable[[str, str, str], bytes | None] = leer_tres_bytes) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--proyecto", required=True)
    ap.add_argument("--version", default="latest")
    ap.add_argument("secretos", nargs="*", default=list(SECRETOS_POR_DEFECTO))
    args = ap.parse_args(argv)
    codigo, lineas = verificar(args.proyecto, args.secretos or SECRETOS_POR_DEFECTO, args.version, lector)
    print("\n".join(lineas))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
