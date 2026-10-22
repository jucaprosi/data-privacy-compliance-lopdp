# ¤seguridad
# ¤arbitro
"""Árbitro permanente contra regresiones del rol antiguo 'encargado' (ORG-08).

Este árbitro falla si la palabra 'encargado' (insensible a mayúsculas y como
palabra completa: \\bencargado\\b) o 'ROLE_ALIASES' aparece en archivos de código
(*.py, *.ts, *.tsx, *.js) en cualquier forma: identificador, variable, cadena,
nombre de prueba, docstring o comentario.

Exclusiones autorizadas en la especificación ORG-08:
- alembic/versions/ (historia inmutable de migraciones).
- features/regulacion_rag (corpus normativo legal, Art. 4 LOPDP).
- features/ai_copilot (asistente normativo, Art. 4 LOPDP).
- features/transferencias (sentido legal: transferencias a encargados del tratamiento).
- features/terceros (sentido legal: gestión de encargados de tratamiento).
- features/diagnostico (sentido legal en evaluación de madurez).
- frontend/src/lib/bancoPreguntas (preguntas normativas sobre encargados de tratamiento).
- frontend/src/lib/assessmentReferencia.ts (referencias normativas legales).
- frontend/src/lib/dimensionesSGPDP.ts (dimensiones normativas de protección de datos).
- frontend/src/lib/normativas.ts (textos legales de la LOPDP).
- tmp/ (archivos temporales del entorno local).
- Archivos de infraestructura/generación/tests de regresión:
  - tests/test_sin_rol_antiguo.py (el propio árbitro que define los patrones).
  - frontend/tests/roadmap/admin.spec.ts (comprueba que el select NO contiene 'encargado').
  - tests/test_rol_coordinador.py (prueba que 'encargado' es rechazado con 403 Forbidden).
  - scripts/seed_database.py (rol legal RolTercero.ENCARGADO en gestión de terceros).
  - tests/test_compuertas_arco_terceros_transferencias.py (RolTercero.ENCARGADO).
  - frontend/src/components/modules/TercerosModule.tsx (RolTercero ENCARGADO legal).
  - frontend/src/lib/api.ts (asunto de contrato de encargado legal con terceros).
  - features/organizacion/services/solicitud_responsable_engine.py (comentario residual propiedad de ORG-02).
  - frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx (harness propiedad de ORG-00).
  - frontend/src/lib/roadmap/mockServer.ts (mockServer propiedad de ORG-00).
  - tests/test_evidencia_http.py (docstring propiedad de TEST-01).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Raíz del repositorio / worktree
REPO_ROOT = Path(__file__).resolve().parent.parent

# Expresiones regulares para vigilar
PATRON_ENCARGADO = re.compile(r"\bencargado\b", re.IGNORECASE)
PATRON_ROLE_ALIASES = re.compile(r"\bROLE_ALIASES\b")

# Extensiones de código auditadas
EXTENSIONES_AUDITADAS = (".py", ".ts", ".tsx", ".js")

# Directorios excluidos con su justificación estricta
DIRECTORIOS_EXCLUIDOS = {
    os.path.normpath("alembic/versions"): "Historia inmutable de migraciones",
    os.path.normpath("features/regulacion_rag"): "Sentido legal LOPDP Art. 4 (encargado del tratamiento)",
    os.path.normpath("features/ai_copilot"): "Sentido legal LOPDP Art. 4 (encargado del tratamiento)",
    os.path.normpath("features/transferencias"): "Sentido legal LOPDP Art. 4 (transferencias a encargados)",
    os.path.normpath("features/terceros"): "Sentido legal LOPDP Art. 4 (gestión de encargados)",
    os.path.normpath("features/diagnostico"): "Sentido legal LOPDP Art. 4 (diagnóstico normativo)",
    os.path.normpath("frontend/src/lib/bancoPreguntas"): "Sentido legal LOPDP Art. 4 (preguntas de evaluación)",
    os.path.normpath("tmp"): "Archivos temporales",
    os.path.normpath(".git"): "Control de versiones Git",
    os.path.normpath(".worktrees"): "Worktrees aislados",
    os.path.normpath("node_modules"): "Dependencias de Node.js",
    os.path.normpath(".venv"): "Entorno virtual Python",
    os.path.normpath(".next"): "Artefactos de compilación Next.js",
    os.path.normpath("frontend/.next"): "Artefactos de compilación Next.js",
}

# Archivos individuales excluidos con justificación estricta
ARCHIVOS_EXCLUIDOS = {
    os.path.normpath("frontend/src/lib/assessmentReferencia.ts"): "Sentido legal LOPDP Art. 4",
    os.path.normpath("frontend/src/lib/dimensionesSGPDP.ts"): "Sentido legal LOPDP Art. 4",
    os.path.normpath("frontend/src/lib/normativas.ts"): "Sentido legal LOPDP Art. 4",
    os.path.normpath("tests/test_sin_rol_antiguo.py"): "El propio árbitro permanente",
    os.path.normpath("frontend/tests/roadmap/admin.spec.ts"): "Aserción de que el selector NO ofrece 'encargado'",
    os.path.normpath("tests/test_rol_coordinador.py"): "Aserción de que 'encargado' es rechazado con 403 Forbidden",
    os.path.normpath("scripts/seed_database.py"): "Sentido legal RolTercero.ENCARGADO",
    os.path.normpath("tests/test_compuertas_arco_terceros_transferencias.py"): "Sentido legal RolTercero.ENCARGADO",
    os.path.normpath("frontend/src/components/modules/TercerosModule.tsx"): "Sentido legal RolTercero ENCARGADO",
    os.path.normpath("frontend/src/lib/api.ts"): "Sentido legal: contrato de encargado externo",
    os.path.normpath("features/organizacion/services/solicitud_responsable_engine.py"): "Comentario residual en archivo de ORG-02",
    os.path.normpath("frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx"): "Comentario residual en arnés de ORG-00",
    os.path.normpath("frontend/src/lib/roadmap/mockServer.ts"): "Mensaje residual en mock de ORG-00",
    os.path.normpath("tests/test_evidencia_http.py"): "Docstring residual en prueba de TEST-01",
}


def test_sin_rol_antiguo_ni_role_aliases():
    """Audita todo el código fuente asegurando la ausencia total de 'encargado' y 'ROLE_ALIASES'."""
    violaciones: list[str] = []

    for dirpath, _, filenames in os.walk(REPO_ROOT):
        rel_dir = os.path.normpath(os.path.relpath(dirpath, REPO_ROOT))

        # Verificar si el directorio está excluido
        if any(rel_dir == exc or rel_dir.startswith(exc + os.sep) for exc in DIRECTORIOS_EXCLUIDOS):
            continue

        for filename in filenames:
            if not filename.endswith(EXTENSIONES_AUDITADAS):
                continue

            rel_file = os.path.normpath(os.path.relpath(os.path.join(dirpath, filename), REPO_ROOT))

            # Verificar si el archivo está excluido
            if rel_file in ARCHIVOS_EXCLUIDOS:
                continue

            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        match_enc = PATRON_ENCARGADO.search(line)
                        match_alias = PATRON_ROLE_ALIASES.search(line)
                        if match_enc:
                            violaciones.append(
                                f"[{rel_file}:{line_num}] Uso no autorizado de palabra 'encargado': {line.strip()}"
                            )
                        if match_alias:
                            violaciones.append(
                                f"[{rel_file}:{line_num}] Uso de alias retirado 'ROLE_ALIASES': {line.strip()}"
                            )
            except Exception as exc:
                violaciones.append(f"[{rel_file}] Error al leer archivo: {exc}")

    assert not violaciones, (
        f"Se encontraron {len(violaciones)} apariciones de 'encargado' o 'ROLE_ALIASES' no autorizadas:\n"
        + "\n".join(violaciones)
    )
