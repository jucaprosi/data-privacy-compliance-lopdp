# ¤entorno-pruebas ¤arbitro
"""Verificador del entorno de pruebas de EVYDENTIA (EP-07).

Contrato: PRD_EVYDENTIA_REVENTA_NUBE.md §5.5 («Interfaz pública que comparten las tareas») e
invariante 57. Se programa contra esa interfaz, no contra el código de EP-01.

    python scripts/verificar_entorno_pruebas.py <frontend> [<backend>] --proyecto <id-de-pruebas>

Devuelve 0 solo si se cumplen las seis comprobaciones:
  1. salud: /api/v1/health está sano (criterio de scripts/verificar_despliegue.py, que se importa);
  2. entorno: /api/v1/entorno devuelve entorno = "pruebas" y datos_ficticios = true, con X-Entorno: pruebas;
  3. sin_headers: una ruta con datos de organización, llamada con X-Tenant-ID y X-User-ID y sin
     token de la aplicación, responde 401 (el modo headers no está activo);
  4. iap: sin la identidad de IAP, el frontend no es accesible;
  5. robots: robots.txt contiene «Disallow: /»;
  6. digest: imprime el digest de la revisión que sirve el tráfico del backend, para
     scripts/digest_verificado.py (EP-06).

IAP y la invocación del backend se atraviesan con tokens de identidad de una cuenta de servicio
autorizada (credenciales por defecto de Google). Van en Proxy-Authorization (IAP) y en
X-Serverless-Authorization (Cloud Run), así que nunca llegan a la aplicación como su token.
La salida nunca contiene un token ni una URL: los destinos se nombran «frontend» y «backend».

Salida: 0 todo bien; 1 alguna comprobación falló; 2 uso inválido.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verificar_despliegue  # noqa: E402  (se reutiliza sin modificarlo)

RUTA_DATOS_ORGANIZACION = "/api/v1/organizacion/me/roles"
IDENTIDAD_INVENTADA = {"X-Tenant-ID": "tenant-ep07.invalid", "X-User-ID": "usuario-ep07@example.invalid"}
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TIMEOUT = 15.0


@dataclass
class Respuesta:
    estado: int
    cabeceras: dict = field(default_factory=dict)
    cuerpo: str = ""
    ubicacion: str = ""


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


def pedir(url: str, cabeceras: Optional[dict] = None, timeout: float = TIMEOUT) -> Respuesta:
    """GET sin seguir redirecciones. Un error de red devuelve estado 0 y ningún detalle (sin la URL)."""
    peticion = urllib.request.Request(url, headers={"User-Agent": "EVYDENTIA-VerificadorPruebas/1.0",
                                                    **(cabeceras or {})})
    abridor = urllib.request.build_opener(_SinRedireccion)
    try:
        with abridor.open(peticion, timeout=timeout) as r:
            return Respuesta(r.getcode(), {k.lower(): v for k, v in r.headers.items()},
                             r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return Respuesta(e.code, {k.lower(): v for k, v in (e.headers or {}).items()},
                         e.read().decode("utf-8", errors="replace"), (e.headers or {}).get("Location", ""))
    except Exception:
        return Respuesta(0)


def token_de_identidad(audiencia: str) -> str:
    """Token de identidad de las credenciales por defecto de Google.

    Con google-auth y una cuenta de servicio, lo emite la biblioteca. Si no se puede (sin la biblioteca,
    o con credenciales federadas de Workload Identity, que no emiten tokens de identidad), lo pide a
    gcloud, suplantando VERIFICADOR_CUENTA_SERVICIO si está definida.
    """
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        return google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audiencia)
    except Exception:
        pass
    comando = ["gcloud", "auth", "print-identity-token", f"--audiences={audiencia}"]
    cuenta = os.environ.get("VERIFICADOR_CUENTA_SERVICIO", "").strip()
    if cuenta:
        comando += [f"--impersonate-service-account={cuenta}", "--include-email"]
    r = subprocess.run(comando, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("no se pudo obtener un token de identidad")
    return r.stdout.strip()


def digest_que_sirve(proyecto: str, region: str, servicio: str) -> str:
    """Digest de la revisión que recibe el tráfico del servicio (solo lectura con gcloud)."""
    base = ["--region", region, "--project", proyecto, "--format=json"]
    r = subprocess.run(["gcloud", "run", "services", "describe", servicio, *base], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("no se pudo describir el servicio")
    trafico = [t for t in json.loads(r.stdout).get("status", {}).get("traffic", []) if t.get("percent")]
    if len(trafico) != 1 or trafico[0]["percent"] != 100:
        raise RuntimeError("el tráfico no está al 100 % en una sola revisión")
    r = subprocess.run(["gcloud", "run", "revisions", "describe", trafico[0]["revisionName"], *base],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("no se pudo describir la revisión")
    return json.loads(r.stdout).get("status", {}).get("imageDigest", "")


@dataclass
class Resultado:
    nombre: str
    ok: bool
    motivo: str = ""


def verificar(
    frontend: str,
    backend: str,
    audiencia_iap: str,
    obtener_token: Callable[[str], str] = token_de_identidad,
    obtener_digest: Callable[[], str] = lambda: "",
    cliente: Callable[..., Respuesta] = pedir,
) -> tuple[list[Resultado], str]:
    front = verificar_despliegue.normalizar_url_base(frontend)
    back = verificar_despliegue.normalizar_url_base(backend)
    resultados: list[Resultado] = []
    try:
        cab_iap = {"Proxy-Authorization": f"Bearer {obtener_token(audiencia_iap)}"}
        cab_back = {"X-Serverless-Authorization": f"Bearer {obtener_token(back)}"}
    except Exception:
        return [Resultado("credenciales", False, "no se pudo obtener el token de identidad de la cuenta de servicio")], ""

    # 1. salud
    r = cliente(f"{back}/api/v1/health", {**cab_back, "Accept": "application/json"})
    try:
        cuerpo = json.loads(r.cuerpo) if r.cuerpo else None
    except json.JSONDecodeError:
        cuerpo = None
    ok, motivo = verificar_despliegue.verificar_health(cuerpo, r.estado) if r.estado else (False, "backend sin respuesta")
    resultados.append(Resultado("salud", ok, "" if ok else motivo))

    # 2. entorno
    r = cliente(f"{back}/api/v1/entorno", {**cab_back, "Accept": "application/json"})
    try:
        cuerpo = json.loads(r.cuerpo) if r.cuerpo else {}
    except json.JSONDecodeError:
        cuerpo = {}
    if r.estado != 200:
        resultados.append(Resultado("entorno", False, f"/api/v1/entorno respondió {r.estado}"))
    elif not isinstance(cuerpo, dict) or cuerpo.get("entorno") != "pruebas" or cuerpo.get("datos_ficticios") is not True:
        resultados.append(Resultado("entorno", False, "el cuerpo no es entorno=pruebas con datos_ficticios=true"))
    elif r.cabeceras.get("x-entorno") != "pruebas":
        resultados.append(Resultado("entorno", False, "falta la cabecera X-Entorno: pruebas"))
    else:
        resultados.append(Resultado("entorno", True))

    # 3. sin_headers
    r = cliente(f"{back}{RUTA_DATOS_ORGANIZACION}", {**cab_back, **IDENTIDAD_INVENTADA})
    ok = r.estado == 401
    resultados.append(Resultado("sin_headers", ok, "" if ok else
                                f"la ruta con datos de organización respondió {r.estado} sin token (se esperaba 401)"))

    # 4. iap
    r = cliente(f"{front}/", {})
    redirige_a_google = r.estado in (301, 302, 303, 307) and "accounts.google.com" in r.ubicacion
    ok = r.estado in (401, 403) or redirige_a_google
    resultados.append(Resultado("iap", ok, "" if ok else f"el frontend respondió {r.estado} sin identidad de IAP"))

    # 5. robots
    r = cliente(f"{front}/robots.txt", cab_iap)
    ok = r.estado == 200 and re.search(r"^\s*Disallow:\s*/\s*$", r.cuerpo, re.MULTILINE) is not None
    resultados.append(Resultado("robots", ok, "" if ok else "robots.txt no contiene «Disallow: /»"))

    # 6. digest
    try:
        digest = obtener_digest()
    except Exception as error:
        digest, motivo = "", str(error)
    else:
        motivo = "" if DIGEST.match(digest or "") else "la revisión no informa un digest sha256"
    resultados.append(Resultado("digest", not motivo, motivo))
    return resultados, digest if not motivo else ""


def formatear(resultados: list[Resultado], digest: str) -> str:
    lineas = [f"{'OK   ' if r.ok else 'FALLA'} {r.nombre}" + (f": {r.motivo}" if r.motivo else "") for r in resultados]
    if digest:
        lineas.append(f"DIGEST {digest}")
    return "\n".join(lineas)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verificador del entorno de pruebas (EP-07).")
    parser.add_argument("frontend")
    parser.add_argument("backend", nargs="?")
    parser.add_argument("--proyecto", default=os.environ.get("PROYECTO_PRUEBAS"))
    parser.add_argument("--region", default=os.environ.get("REGION_PRUEBAS", "us-central1"))
    parser.add_argument("--servicio", default=os.environ.get("SERVICIO_BACKEND_PRUEBAS", "evydentia-backend"))
    parser.add_argument("--audiencia-iap", default=os.environ.get("IAP_AUDIENCIA"),
                        help="Audiencia de IAP (id del cliente OAuth); por defecto, la URL del frontend.")
    args = parser.parse_args(argv)
    if not args.proyecto:
        print("Uso: falta --proyecto (o PROYECTO_PRUEBAS).", file=sys.stderr)
        return 2
    huella = os.environ.get("HUELLA_PROYECTO_PRODUCCION", "").strip().lower()
    if huella and huella in args.proyecto.lower():
        print("Rechazado: el proyecto es el de producción.", file=sys.stderr)
        return 2
    backend = args.backend or args.frontend
    resultados, digest = verificar(
        args.frontend, backend, args.audiencia_iap or verificar_despliegue.normalizar_url_base(args.frontend),
        obtener_digest=lambda: digest_que_sirve(args.proyecto, args.region, args.servicio),
    )
    print(formatear(resultados, digest))
    return 0 if all(r.ok for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
