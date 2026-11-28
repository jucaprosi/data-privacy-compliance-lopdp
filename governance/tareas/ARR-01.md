+++
id = "ARR-01"
titulo = "La imagen del backend lleva el bytecode compilado"
ola = "D"
estado = "hecha"
tanda = 121
sala = "operaciones"
depende_de = []
propiedad = ["Dockerfile", "tests/test_arr01_bytecode.py"]
crea = ["tests/test_arr01_bytecode.py"]
arbitro = "pytest tests/test_arr01_bytecode.py; mutación m1."
rastros = ["¤arbitro"]
+++

# ARR-01 · La imagen del backend lleva el bytecode compilado

**Contrato:** `governance/especificaciones/ARR-01.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_ARRANQUE_EN_FRIO_BACKEND.md` (2026-11-27): el arranque en frío tarda hasta 20 s, y casi todo son importaciones de Python. Sin coste nuevo: `min-instances` sigue en 0.

## Entrega
- `RUN python -m compileall -q -j 0 /app` en el `Dockerfile`, después de `COPY . .`.
- Prueba que lee el `Dockerfile`.

## Límites
- En el `Dockerfile`, solo esa línea. `PYTHONDONTWRITEBYTECODE=1` se queda: solo evita escribir en tiempo de ejecución.
- No toca `.dockerignore`, la nube ni `deploy-gcp.yml`.
- Archivo nuevo con el aviso de autor; LF.
