# ¤seguridad-tenant
"""SEC-23: el frontend del asistente envía la identidad de la sesión y no inventa la organización.

Árbitro estático sobre el código TypeScript (no necesita base de datos ni navegador). Mutaciones:
volver a poner un X-Tenant-ID fijo en el proxy, dejar de reenviar Authorization, o llamar al proxy con
`fetch` sin identidad desde el cliente → rojo.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROXY = (RAIZ / "frontend" / "src" / "lib" / "copilotProxy.ts").read_text(encoding="utf-8")
CLIENTE = (RAIZ / "frontend" / "src" / "lib" / "copilotClient.ts").read_text(encoding="utf-8")


def test_proxy_sin_organizacion_fija():
    assert "tenant-corp-demo" not in PROXY
    assert not re.search(r'"X-Tenant-ID"\s*:\s*"', PROXY)


def test_proxy_reenvia_la_identidad_de_quien_llama():
    assert '"authorization"' in PROXY and '"x-tenant-id"' in PROXY
    assert "...identidadDe(request)" in PROXY


def test_proxy_descarta_x_user_id_en_la_nube():
    assert re.search(r"x-user-id.*\n.*K_SERVICE", PROXY)


def test_cliente_llama_con_fetch_autenticado():
    llamadas = re.findall(r"await (\w+)\(\"/api/ai-copilot/(\w+)\"", CLIENTE)
    assert {r for _, r in llamadas} == {"consulta", "estado"}
    assert all(f == "fetchAutenticado" for f, _ in llamadas)
