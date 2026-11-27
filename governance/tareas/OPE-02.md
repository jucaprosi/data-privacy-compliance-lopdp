+++
id = "OPE-02"
titulo = "La plataforma expone en la base si alguien es operador activo"
ola = "D"
estado = "pendiente"
tanda = 112
sala = "plataforma"
depende_de = []
propiedad = ["alembic/versions/20261126_ope02_operador_activo_bd.py", "tests/test_ope02_operador_activo_bd.py"]
crea = ["alembic/versions/20261126_ope02_operador_activo_bd.py", "tests/test_ope02_operador_activo_bd.py"]
arbitro = "pytest tests/test_ope02_operador_activo_bd.py tests/test_adpa_bulkhead.py; mutaciones m1 a m3."
rastros = ["¤arbitro"]
+++

# OPE-02 · La plataforma expone en la base si alguien es operador activo

**Contrato:** `governance/especificaciones/OPE-02.md` (manda sobre esta ficha).

**Origen.** Revisión de seguridad del CTO sobre BIB-411 (2026-11-26): las funciones de escritura de capacidades se ejecutan como `lopdp_app`, el rol de todas las peticiones de todos los tenants, y deben comprobar en la base que actor y destino son operadores activos, sin SQL entre salas.

## Entrega
- Una función de solo lectura en la rama de Alembic de plataforma.

## Límites
- Solo los archivos de la propiedad. No toca el pasillo Python ni la nube.
