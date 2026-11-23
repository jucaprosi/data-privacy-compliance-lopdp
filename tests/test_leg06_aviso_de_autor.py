# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤ip
"""LEG-06 §5: licencia propietaria y aviso de derechos de autor en todo archivo de código versionado."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("poner_aviso_de_autor", RAIZ / "scripts" / "poner_aviso_de_autor.py")
aviso = importlib.util.module_from_spec(_spec)
sys.modules["poner_aviso_de_autor"] = aviso
_spec.loader.exec_module(aviso)

SHA256_LICENCIA = "f814709c25412c5863eec4c284303f790c04b6063356907468f964b73ee3a7db"
TEXTO = ("© 2026 Juan Carlos Proaño. Todos los derechos reservados. "
         "Uso, copia o distribución prohibidos sin autorización escrita.")


def faltan_aviso(raiz: Path) -> list[str]:
    """Un mensaje por archivo de R1 sin el aviso en su sitio, con la línea exacta que hay que pegar (R3)."""
    mensajes = []
    for ruta in aviso.archivos_de_r1(raiz):
        archivo = raiz / ruta
        if archivo.is_file() and not aviso.tiene_aviso(archivo.read_bytes().decode("utf-8"), aviso.extension_de(ruta)):
            mensajes.append(f"{ruta}: pega como primera línea de contenido «{aviso.linea_de_aviso(aviso.extension_de(ruta))}»")
    return mensajes


def test_todo_archivo_de_codigo_lleva_el_aviso():
    faltan = faltan_aviso(RAIZ)
    assert not faltan, "Archivos sin aviso de autor (R1, R2):\n" + "\n".join(faltan)


def _repo(tmp_path: Path, archivos: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for ruta, texto in archivos.items():
        destino = tmp_path / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(texto.encode("utf-8"))
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    return tmp_path


def test_m1_quitar_el_aviso_de_un_archivo_da_rojo_con_la_linea(tmp_path):
    raiz = _repo(tmp_path, {"a.py": "import os\n", "web/b.tsx": "export {}\n", ".github/w.yml": "on: push\n",
                            "datos.json": "{}\n"})
    assert aviso.main(["--raiz", str(raiz)]) == 0
    assert faltan_aviso(raiz) == []
    (raiz / "a.py").write_text("import os\n", encoding="utf-8")  # m1: se quita el aviso
    assert faltan_aviso(raiz) == [f"a.py: pega como primera línea de contenido «# {TEXTO}»"]
    assert aviso.main(["--raiz", str(raiz), "--verificar"]) == 1
    assert (raiz / ".github/w.yml").read_text(encoding="utf-8") == "on: push\n"  # R1: .github/ queda fuera
    assert (raiz / "datos.json").read_text(encoding="utf-8") == "{}\n"


def test_r1_excluye_github_y_json():
    assert aviso.AVISO == TEXTO
    assert aviso.es_de_r1("scripts/x.py") and aviso.es_de_r1("frontend/src/a.tsx")
    assert not aviso.es_de_r1(".github/workflows/ci.yml") and not aviso.es_de_r1("frontend/package.json")


def test_posicion_y_idempotencia():
    py, ts, bat = aviso.linea_de_aviso(".py"), aviso.linea_de_aviso(".ts"), aviso.linea_de_aviso(".bat")
    casos = [
        ("a.py", "﻿import os\n", f"﻿{py}\nimport os\n"),
        ("a.py", "#!/usr/bin/env python\nimport os\n", f"#!/usr/bin/env python\n{py}\nimport os\n"),
        ("a.py", "# -*- coding: utf-8 -*-\nx = 1\n", f"# -*- coding: utf-8 -*-\n{py}\nx = 1\n"),
        ("a.py", "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nx = 1\n",
         f"#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n{py}\nx = 1\n"),
        ("a.bat", "@echo off\r\nset X=1\r\n", f"@echo off\r\n{bat}\r\nset X=1\r\n"),
        ("a.tsx", '"use client";\nexport {}\n', f'{ts}\n"use client";\nexport {{}}\n'),
        ("a.ts", '"use server";\n', f'{ts}\n"use server";\n'),
        ("vacio.py", "", f"{py}\n"),
        ("a.mjs", "#!/usr/bin/env node\nconsole.log(1)\n", f"#!/usr/bin/env node\n{ts}\nconsole.log(1)\n"),
        ("a.css", "a{}\n", f"{aviso.linea_de_aviso('.css')}\na{{}}\n"),
    ]
    for ruta, antes, despues in casos:
        extension = aviso.extension_de(ruta)
        puesto = aviso.poner_aviso(antes, extension)
        assert puesto == despues, ruta
        assert aviso.poner_aviso(puesto, extension) == puesto, f"{ruta}: la segunda pasada cambió el archivo"
        assert aviso.tiene_aviso(puesto, extension) and not aviso.tiene_aviso(antes, extension)


def test_m2_el_aviso_antes_del_shebang_da_rojo():
    py = aviso.linea_de_aviso(".py")
    assert not aviso.tiene_aviso(f"{py}\n#!/usr/bin/env python\nimport os\n", ".py")
    assert not aviso.tiene_aviso(f"﻿{py}\n", ".py") is False  # tras el BOM sí está en su sitio
    assert not aviso.tiene_aviso(f"{py}\n@echo off\n".replace(py, aviso.linea_de_aviso(".bat")), ".bat")
    assert not aviso.tiene_aviso(f"{py}\n# -*- coding: utf-8 -*-\n", ".py")


def _package_json_declara_unlicensed(datos: dict) -> bool:
    return datos.get("license") == "UNLICENSED"


def test_licencia_y_package_json():
    licencia = RAIZ / "LICENSE"
    assert licencia.is_file(), "falta LICENSE en la raíz"
    assert hashlib.sha256(licencia.read_bytes()).hexdigest() == SHA256_LICENCIA
    datos = json.loads((RAIZ / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert _package_json_declara_unlicensed(datos)
    sin_campo = {k: v for k, v in datos.items() if k != "license"}  # m3: quitar el campo da rojo
    assert not _package_json_declara_unlicensed(sin_campo)


def test_bat_y_cmd_en_crlf():
    """LEG-07 §5: cada .bat y .cmd versionado guarda CRLF en el índice, sin ningún LF suelto."""
    rutas = subprocess.run(["git", "ls-files", "--", "*.bat", "*.cmd"], cwd=RAIZ, capture_output=True,
                           text=True, check=True).stdout.split()
    assert len(rutas) >= 6, "faltan los .bat de LEG-07 en el índice"
    malos = []
    for ruta in rutas:
        datos = subprocess.run(["git", "show", f":{ruta}"], cwd=RAIZ, capture_output=True, check=True).stdout
        if datos.count(b"\n") != datos.count(b"\r\n"):
            malos.append(f"{ruta}: tiene LF sin CR en el índice")
    assert not malos, "\n".join(malos)


def test_gitattributes_crlf_y_biblioteca():
    """LEG-07 §5: .gitattributes declara -text para .bat y .cmd y conserva data/biblioteca/** -text."""
    lineas = {linea.strip() for linea in (RAIZ / ".gitattributes").read_text(encoding="utf-8").splitlines()}
    assert "*.bat -text" in lineas and "*.cmd -text" in lineas, "falta *.bat -text o *.cmd -text"
    assert "data/biblioteca/** -text" in lineas
    assert not any("eol=crlf" in linea for linea in lineas), "text eol=crlf guarda LF en el índice"
