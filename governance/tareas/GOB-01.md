+++
id = "GOB-01"
titulo = "Promover los rastros nuevos al VPA"
ola = "indep"
estado = "pendiente"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/artefactos/VPA_MAP.md", "tests/test_vpa_map.py"]
arbitro = "figuran en VPA_MAP.md y git grep los encuentra (tests/test_vpa_map.py)"
rastros = ["¤vpa"]
+++

# GOB-01 · Promover los rastros nuevos al VPA

**Objetivo.** Indexar `¤roadmap` y `¤rbac-tenant` en `governance/artefactos/VPA_MAP.md`.

**Decisión del propietario (2026-10-22): manda el repositorio.** El mapa de rastros es el versionado; el servidor de ZERAG no lo lee y no se espera de él ni un alta directa ni una herramienta de lectura. `governance/artefactos/data/CANDIDATOS_VPA.json` es un residuo que el servidor no lee.

## Entrega
- Añadir los dos rastros a `VPA_MAP.md`.
- `tests/test_vpa_map.py`: todo rastro declarado en una ficha figura en el mapa y `git grep` lo encuentra fuera de `governance/tareas/`; los pendientes van en una lista declarada con su motivo.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
