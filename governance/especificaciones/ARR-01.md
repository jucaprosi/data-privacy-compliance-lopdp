# ARR-01 · La imagen del backend lleva el bytecode compilado
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Medido por el CTO en `origin/main` 99e4ecf7. El `Dockerfile` fija `PYTHONDONTWRITEBYTECODE=1` (l. 6) y copia el código en la l. 25. `.dockerignore` excluye `__pycache__` y `*.pyc`, así que cada instancia nueva compila todo `features/`, `app_core/` y `api/`. En local, `import main` tarda 5,7 s sin `.pyc` y 3,9 s con ellos (−32 %).

## 2. API

No aplica.

## 3. Reglas

- **R1 · Bytecode en la imagen.** Tras `COPY . .`, el `Dockerfile` ejecuta `python -m compileall -q -j 0 /app`. El directorio es el `WORKDIR` del `Dockerfile`.
- **R2 · Sin coste.** Misma imagen base, misma CPU y misma memoria.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-01`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el `Dockerfile`, **entonces** hay un `RUN python -m compileall` sobre el directorio de la app y va después del `COPY` del código. Mutación m1: quitarlo, o ponerlo antes de `COPY . .`, da rojo. | `tests/test_arr01_bytecode.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run, medidos con `gcloud run services describe evydentia-backend` (solo lectura): `startup-cpu-boost=true` ya está activo y no hay `execution-environment` fijado. No queda ningún ajuste gratuito que pedir al propietario: no hay brief de nube.
