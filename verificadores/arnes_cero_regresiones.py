# ¤¤qa-engineer
"""Runner físico determinista del Arnés de Cero Regresiones (Teorema Proaño-Gemini-Dijkstra).
Verifica:
1. Suite completa de pruebas unitarias y de arquitectura (pytest).
2. Codificación estricta UTF-8 sin marcas BOM.
3. Ausencia de huellas abiertas '¦' en código ejecutable.
4. Emisión del certificado notarial .test_verdict.json.
"""
import os
import sys
import json
import time
import hashlib
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERDICT_PATH = os.path.join(PROJECT_ROOT, "governance", "artefactos", ".test_verdict.json")

# ¤archivos-rastreados
# Justificación: recorrer el disco alcanzaba .worktrees/ (otras ramas enteras) y, al comparar subcadenas de la ruta,
#   omitía todo lo que contuviera ".git" o "verificadores" en cualquier nivel. El árbol del repositorio es el que dice git.
def archivos_rastreados(extensiones: tuple[str, ...], excluir_carpetas: tuple[str, ...] = ()) -> list[str]:
    salida = subprocess.run(["git", "ls-files", "-z"], cwd=PROJECT_ROOT, capture_output=True, check=True).stdout
    rutas = salida.decode("utf-8").split("\0")
    return [
        ruta for ruta in rutas
        if ruta.endswith(extensiones)
        and ruta.split("/", 1)[0] not in excluir_carpetas
        and os.path.isfile(os.path.join(PROJECT_ROOT, ruta))
    ]

# ¤verificar-tests
def verificar_tests() -> bool:
    print("[1/3] Ejecutando suite de pruebas unitarias y de arquitectura...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], cwd=PROJECT_ROOT)
    return res.returncode == 0

# ¤verificar-utf8-no-bom
def verificar_utf8_no_bom() -> bool:
    print("\n[2/3] Verificando codificación UTF-8 estricta sin BOM...")
    bom = b'\xef\xbb\xbf'
    fallos = []
    for ruta in archivos_rastreados((".py", ".md")):
        try:
            with open(os.path.join(PROJECT_ROOT, ruta), "rb") as f:
                if f.read(3) == bom:
                    fallos.append(ruta)
        except OSError as e:
            fallos.append(f"{ruta} (Error de lectura: {e})")
    if fallos:
        print(f"❌ Se detectó marca BOM en: {fallos}")
        return False
    print("✅ Todos los archivos .py y .md son UTF-8 sin BOM.")
    return True

# ¤verificar-huellas-selladas
def verificar_huellas_selladas() -> bool:
    target_char = chr(166) # Carácter huella
    print(f"\n[3/3] Verificando ausencia de huellas abiertas no selladas en código .py...")
    fallos = []
    for ruta in archivos_rastreados((".py",), excluir_carpetas=("verificadores",)):
        try:
            with open(os.path.join(PROJECT_ROOT, ruta), "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    if target_char in line:
                        fallos.append(f"{ruta}:L{idx}")
        except (OSError, UnicodeDecodeError) as e:
            fallos.append(f"{ruta} (Error: {e})")
    if fallos:
        print(f"❌ Se detectaron huellas abiertas no selladas: {fallos}")
        return False
    print("✅ Cero huellas abiertas en código ejecutable.")
    return True

# ¤emitir-certificado
def emitir_certificado(exito: bool):
    os.makedirs(os.path.dirname(VERDICT_PATH), exist_ok=True)
    payload = {
        "timestamp": time.time(),
        "status": "PASS" if exito else "FAIL",
        "exit_code": 0 if exito else 1,
        "arbitro": "Teorema Proaño-Gemini-Dijkstra",
        "base": os.environ.get("ARNES_BASE", "test_database_url"),
        "project": "JUBYS Plataforma LOPDP 360",
    }
    with open(VERDICT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    # Copia a raiz del proyecto
    root_verdict = os.path.join(PROJECT_ROOT, ".test_verdict.json")
    with open(root_verdict, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n📜 Certificado notarial emitido en: {os.path.relpath(VERDICT_PATH, PROJECT_ROOT)}")

# ¤main-arnes
def main():
    print("=" * 80)
    print("🏛️ ARNES FISICO DETERMINISTA ZERO-REGRESSION — PLATAFORMA LOPDP 360")
    print("=" * 80)
    
    t_pass = verificar_tests()
    u_pass = verificar_utf8_no_bom()
    h_pass = verificar_huellas_selladas()
    
    exito_total = t_pass and u_pass and h_pass
    emitir_certificado(exito_total)
    
    if exito_total:
        print("=" * 80)
        print("🟢 [EXITO ABSOLUTO]: Cero Regresiones. Todos los arbitros pasaron con Exit Code 0.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("=" * 80)
        print("❌ [FALLO DE REGRESION]: Al menos un arbitro ha fallado. Revisa los registros.")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
