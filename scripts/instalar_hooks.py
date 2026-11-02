# ¤arbitro ¤ci-cd
"""Instala el hook pre-push versionado, en un paso, en Windows, Mac y Linux: python scripts/instalar_hooks.py

Cada clon lo instala una vez y vale para todos sus worktrees. Escribe un envoltorio en los hooks comunes del
clon en vez de definir `core.hooksPath=.githooks`, por dos razones: esa ruta se resuelve en cada worktree, y
una rama anterior al hook se quedaría sin el bloqueo de `main`; y con `core.autocrlf=true` el archivo llega con
CRLF, que `sh` no puede ejecutar. El hook anterior, si era otro, queda en `pre-push.anterior`.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ENVOLTORIO = """#!/bin/sh
# Instalado por scripts/instalar_hooks.py; no lo edite. El hook vive en .githooks/pre-push.
versionado="$(git rev-parse --show-toplevel)/.githooks/pre-push"
if [ -f "$versionado" ]; then
  exec sh -c "$(tr -d '\\r' < "$versionado")" pre-push "$@"
fi
# Rama anterior al hook versionado: se conserva el bloqueo del push directo a main.
while read -r local_ref local_sha remote_ref remote_sha; do
  if [ "$remote_ref" = "refs/heads/main" ]; then
    echo "BLOQUEADO: push directo a main. Abre un Pull Request desde una rama." >&2
    exit 1
  fi
done
exit 0
"""


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def instalar() -> int:
    if _git("config", "--get", "core.hooksPath"):
        print("[HOOKS] core.hooksPath está definido y git no leería el hook instalado. Retírelo y repita:")
        print("  git config --unset core.hooksPath")
        return 1
    carpeta = Path.cwd() / _git("rev-parse", "--git-common-dir") / "hooks"
    destino = carpeta / "pre-push"
    if destino.exists():
        if destino.read_bytes() == ENVOLTORIO.encode("utf-8"):
            print("[HOOKS] pre-push ya estaba instalado.")
            return 0
        shutil.copy2(destino, carpeta / "pre-push.anterior")
    carpeta.mkdir(exist_ok=True)
    destino.write_bytes(ENVOLTORIO.encode("utf-8"))
    destino.chmod(0o755)
    print("[HOOKS] pre-push instalado para este clon y todos sus worktrees.")
    return 0


if __name__ == "__main__":
    sys.exit(instalar())
