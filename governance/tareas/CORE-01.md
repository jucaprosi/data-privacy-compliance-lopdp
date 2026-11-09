+++
id = "CORE-01"
titulo = "Una sola zona de negocio: control periódico y recordatorios importan de app_core/zona_negocio.py"
ola = "backlog"
estado = "en_curso"
sala = "auditoria_capa, roadmap"
depende_de = ["BIB-120"]
propiedad = ["features/auditoria_capa/domain/control_periodico.py", "features/roadmap/services/recordatorios_engine.py", "tests/test_core01_zona_unica.py"]
crea = ["tests/test_core01_zona_unica.py"]
arbitro = "pytest tests/test_core01_zona_unica.py + suites de CAPA-02 y RM-23 + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤arbitro"]
+++

# CORE-01 · Una sola zona de negocio

Diseño del Arquitecto ADPA (2026-11-08). BIB-120 crea `app_core/zona_negocio.py`. Esta ficha retira las dos copias de `ZONA_GUAYAQUIL` (`control_periodico.py:17` y `recordatorios_engine.py:23`) para que importen `ZONA_NEGOCIO` de allí. Sus dueñas, CAPA-02 y RM-23, están hechas, así que no hay choque de propiedad.

## Prueba
`test_core01_zona_unica.py` comprueba que, fuera de `app_core/zona_negocio.py`, no aparecen `ZONA_GUAYAQUIL =` ni `timedelta(hours=-5)` en `features/` ni en `app_core/`. Las suites de CAPA-02 y RM-23 siguen en verde. Sin `import yaml` en las pruebas.
