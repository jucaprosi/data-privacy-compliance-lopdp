# -*- coding: utf-8 -*-
# ¤seguridad ¤arbitro
"""SEC-14: el frontend no publica mapas de fuente ni secretos en variables públicas.

Pruebas estáticas, sin compilar. Prueba de mutación: los tres últimos casos plantan un `.map`,
un `sourceMappingURL`, una cadena `sk-` y una variable `NEXT_PUBLIC_*_SECRET` en carpetas
temporales y exigen que la verificación falle; si el árbitro dejara de detectarlos, fallarían.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "verificar_bundle_frontend.py"
_spec = importlib.util.spec_from_file_location("verificar_bundle_frontend", SCRIPT)
vbf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vbf)

# Valor simulado, construido en partes para que el propio repositorio no contenga la forma.
CLAVE_SIMULADA = "sk-" + "PRUEBA" + "0123456789abcdefXYZ"


def test_configuracion_actual_sin_mapas():
    assert vbf.revisar_configuraciones() == []
    assert vbf.revisar_variables_publicas() == []


def test_detecta_mapas_activados(tmp_path):
    (tmp_path / "next.config.ts").write_text("const c = { reactStrictMode: true };", encoding="utf-8")
    (tmp_path / "next.config.cloudrun.ts").write_text(
        "const c = { productionBrowserSourceMaps:  true };", encoding="utf-8"
    )
    hallazgos = vbf.revisar_configuraciones(tmp_path)
    assert hallazgos == [("next.config.cloudrun.ts", "R1 productionBrowserSourceMaps activado")]


def test_mapas_desactivados_no_es_hallazgo(tmp_path):
    (tmp_path / "next.config.ts").write_text("{ productionBrowserSourceMaps: false }", encoding="utf-8")
    assert vbf.revisar_configuraciones(tmp_path) == []


def test_detecta_secreto_publico(tmp_path):
    (tmp_path / "pago.ts").write_text(
        "const s = process.env.NEXT_PUBLIC_STRIPE_SECRET;\n"
        "const g = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;\n"
        "const u = process.env.NEXT_PUBLIC_USER_EMAIL;\n",
        encoding="utf-8",
    )
    hallazgos = vbf.revisar_variables_publicas(tmp_path)
    assert len(hallazgos) == 1
    assert hallazgos[0][0] == "pago.ts"
    assert "NEXT_PUBLIC_STRIPE_SECRET" in hallazgos[0][1]


def test_nombres_de_secreto():
    for nombre in ("NEXT_PUBLIC_DB_PASSWORD", "NEXT_PUBLIC_API_TOKEN", "NEXT_PUBLIC_PRIVATE_X", "NEXT_PUBLIC_R2_KEY"):
        assert vbf.es_nombre_de_secreto(nombre), nombre
    for nombre in ("NEXT_PUBLIC_GOOGLE_CLIENT_ID", "NEXT_PUBLIC_TENANT_ID", "NEXT_PUBLIC_KEYBOARD"):
        assert not vbf.es_nombre_de_secreto(nombre), nombre


def test_paquete_limpio_termina_en_cero(tmp_path):
    (tmp_path / "chunks").mkdir()
    (tmp_path / "chunks" / "app.js").write_text("console.log('hola');", encoding="utf-8")
    assert vbf.main([str(tmp_path)]) == 0


def test_script_detecta_mapa_y_credencial_sin_imprimirla(tmp_path):
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    (chunks / "app.js.map").write_text("{}", encoding="utf-8")
    (chunks / "app.js").write_text(
        f"const k='{CLAVE_SIMULADA}';\n//# sourceMappingURL=app.js.map\n", encoding="utf-8"
    )
    (chunks / "db.js").write_text("const u='postgresql://usuario:simulada@host/db';", encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True, encoding="utf-8"
    )
    assert resultado.returncode == 1
    salida = resultado.stdout
    assert "chunks/app.js.map: R3 mapa de fuente publicado" in salida
    assert "chunks/app.js: R3 comentario sourceMappingURL" in salida
    assert "clave sk-" in salida
    assert "chunks/db.js" in salida
    assert CLAVE_SIMULADA not in salida
    assert "simulada@" not in salida


def test_sin_carpeta_compilada_falla(tmp_path):
    assert vbf.main([str(tmp_path / "no_existe")]) == 1
