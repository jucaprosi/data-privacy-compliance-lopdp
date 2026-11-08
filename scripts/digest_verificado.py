# ¤entorno-pruebas ¤ci-cd
"""Digest que pasó el verificador del entorno de pruebas (EP-06).

Guarda y lee, en un archivo local fuera del repositorio, cada digest probado con su fecha y el código de
salida del verificador (EP-07). Quien promueve a producción por el despliegue progresivo (GCP-07) pide
aquí el digest: solo sale uno cuyo último registro tiene código 0.

    python scripts/digest_verificado.py guardar --digest sha256:<hex> --codigo 0
    python scripts/digest_verificado.py leer
    python scripts/digest_verificado.py comprobar --digest sha256:<hex>

Salida: 0 bien; 1 el digest no pasó el verificador o no hay ninguno; 2 uso o archivo inválido.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_POR_DEFECTO = Path.home() / ".evydentia" / "digest_verificado.json"
PATRON = re.compile(r"^sha256:[0-9a-f]{64}$")


class DigestError(ValueError):
    pass


def normalizar(digest: str) -> str:
    valor = digest.strip().lower()
    if not valor.startswith("sha256:"):
        valor = "sha256:" + valor
    if not PATRON.match(valor):
        raise DigestError("El digest debe ser sha256:<64 hexadecimales>.")
    return valor


def _en_repositorio(archivo: Path) -> bool:
    try:
        archivo.resolve().relative_to(RAIZ)
    except ValueError:
        return False
    return True


def _validar_archivo(archivo: Path) -> Path:
    if _en_repositorio(archivo):
        raise DigestError("El registro de digests debe vivir fuera del repositorio.")
    return archivo


def _leer_registros(archivo: Path) -> list[dict]:
    if not archivo.exists():
        return []
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise DigestError("Registro de digests con formato inválido.")
    return datos


def guardar(digest: str, codigo: int, archivo: Path = ARCHIVO_POR_DEFECTO, ahora: datetime | None = None) -> dict:
    archivo = _validar_archivo(archivo)
    registro = {
        "digest": normalizar(digest),
        "codigo_salida": int(codigo),
        "fecha": (ahora or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }
    registros = _leer_registros(archivo) + [registro]
    archivo.parent.mkdir(parents=True, exist_ok=True)
    temporal = archivo.with_suffix(".tmp")
    temporal.write_text(json.dumps(registros, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporal, archivo)
    return registro


def _ultimo_de(registros: list[dict], digest: str) -> dict | None:
    propios = [r for r in registros if r.get("digest") == digest]
    return propios[-1] if propios else None


def comprobar(digest: str, archivo: Path = ARCHIVO_POR_DEFECTO) -> dict:
    """Devuelve el registro si el último resultado de ese digest es 0; si no, lanza DigestError."""
    valor = normalizar(digest)
    registro = _ultimo_de(_leer_registros(_validar_archivo(archivo)), valor)
    if registro is None:
        raise DigestError("Ese digest no pasó por el verificador del entorno de pruebas.")
    if registro.get("codigo_salida") != 0:
        raise DigestError(f"Ese digest falló el verificador (código {registro.get('codigo_salida')}).")
    return registro


def leer(archivo: Path = ARCHIVO_POR_DEFECTO) -> dict:
    """El último digest registrado, solo si pasó el verificador."""
    registros = _leer_registros(_validar_archivo(archivo))
    if not registros:
        raise DigestError("No hay ningún digest registrado.")
    ultimo = registros[-1]
    return comprobar(ultimo["digest"], archivo)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Digest que pasó el verificador del entorno de pruebas (EP-06).")
    parser.add_argument("--archivo", default=str(ARCHIVO_POR_DEFECTO))
    sub = parser.add_subparsers(dest="accion", required=True)
    g = sub.add_parser("guardar")
    g.add_argument("--digest", required=True)
    g.add_argument("--codigo", required=True, type=int)
    sub.add_parser("leer")
    c = sub.add_parser("comprobar")
    c.add_argument("--digest", required=True)
    args = parser.parse_args(argv)
    archivo = Path(args.archivo)
    try:
        if args.accion == "guardar":
            r = guardar(args.digest, args.codigo, archivo)
            print(f"Registrado {r['digest']} con código {r['codigo_salida']} ({r['fecha']}).")
            return 0
        r = leer(archivo) if args.accion == "leer" else comprobar(args.digest, archivo)
        print(r["digest"])
        return 0
    except DigestError as error:
        print(f"Rechazado: {error}", file=sys.stderr)
        return 1 if "verificador" in str(error) or "ningún" in str(error) else 2
    except (OSError, json.JSONDecodeError) as error:
        print(f"Registro ilegible: {error.__class__.__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
