+++
id = "PRD-03"
titulo = "Aviso de inhabilitado en el PRD y los artefactos anteriores, con prueba de que nada los lee"
ola = "backlog"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["PRD-01", "PRD-02", "BIB-105", "GOB-01", "GOB-03", "ORG-00", "ORG-01", "ORG-08"]
propiedad = ["governance/artefactos/PRD.md", "governance/artefactos/INVARIANTS.md", "governance/artefactos/TASKS.md", "governance/artefactos/VPA_MAP.md", "tests/test_prd_inhabilitado.py"]
crea = ["tests/test_prd_inhabilitado.py"]
arbitro = "pytest tests/test_prd_inhabilitado.py: los cuatro archivos llevan el aviso de inhabilitado y ningún script de scripts/ ni prueba de tests/ los abre (git grep de las cuatro rutas vacío salvo la propia prueba y verificar_alcance_pr); mutación documentada: quitar el aviso de uno hace fallar la prueba"
rastros = ["¤triaje"]
+++

# PRD-03 · Aviso de inhabilitado en el PRD y los artefactos anteriores, con prueba de que nada los lee

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Orden
PRD-00 (el CTO, en su PR: apartado `### 7.1 Catálogo de salas` en `PRD_EVYDENTIA_REVENTA_NUBE.md` y decisión sobre los 25 INV heredados) se fusiona antes. PRD-01 y PRD-02 pueden ir en paralelo; PRD-03, al final. **Bloqueante:** `PRD_EVYDENTIA_REVENTA_NUBE.md` no tiene el apartado 7.1 que lee `salas_del_prd`; devuelve 0 salas frente a 35 y cambiar solo la ruta rompería todas las fichas.

## Entrega
- Bloque de cita **debajo** del título y de los tokens, sin tocar la estructura (regla de estigmergia): «Inhabilitado desde 2026-11-11. Rige PRD_EVYDENTIA_REVENTA_NUBE.md y sus artefactos. Se conserva como historia.»
- Si la guardia de estigmergia prohíbe tocar esos `.md`, el aviso va en `governance/artefactos/INHABILITADOS.md` y la prueba lee ese archivo: lo decide el CTO.
- Va al final: si no, la prueba falla mientras los scripts aún los lean.
