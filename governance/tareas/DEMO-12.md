+++
id = "DEMO-12"
titulo = "La demo con las plantillas reales del catálogo: carga en la base de la demo y documentos nacidos de ellas"
ola = "D"
estado = "pendiente"
tanda = 106
sala = "biblioteca"
depende_de = ["BIB-403", "DEMO-11"]
propiedad = ["scripts/cargar_plantillas_pmv.py", "features/biblioteca/services/clon_plantilla_engine.py", "data/demo/cooperativa_demo.json", "tests/test_demo_clon_biblioteca.py", "docs/biblioteca-pmv.md", "features/biblioteca/services/generacion.py", "features/biblioteca/services/generador_docx.py", "features/biblioteca/services/generador_xlsx.py", "tests/test_demo12_plantillas_reales.py"]
crea = ["tests/test_demo12_plantillas_reales.py"]
arbitro = "pytest tests/test_demo12_plantillas_reales.py tests/test_demo_clon_biblioteca.py tests/test_adpa_bulkhead.py; mutaciones m1 a m5."
rastros = ["¤demo", "¤arbitro"]
+++

# DEMO-12 · La demo con las plantillas reales

**Contrato:** `governance/especificaciones/DEMO-12.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_DEMO_PLANTILLAS_REALES` (2026-11-24) y decisión del propietario: «las mismas plantillas originales funcionan tanto para producción como para demo».

## Entrega
- **Cargador:** `cargar_plantillas_pmv.py` reconoce el entorno `demo`, con el mismo `--confirmar-entorno` y sin conectar si la URL no es la de la demo.
- **Siembra:** los documentos de la organización ficticia nacen de plantillas publicadas del catálogo (texto real, datos ficticios de la organización), con estados y orígenes que dan resultados en los filtros «Estado» y «Origen». Falla cerrado si el catálogo no está cargado.
- **Títulos:** los de la plantilla, sin «(borrador ficticio)».
- **Exportación:** en la demo, cada DOCX y XLSX generado lleva en el pie la leyenda «Demostración · datos ficticios».
- **Procedimiento:** `docs/biblioteca-pmv.md` añade la carga en la demo.
- **Prueba:** `tests/test_demo12_plantillas_reales.py`, exógena, con mutaciones.

## Límites
- No toca la nube ni la base. La carga en `evydentia-demo-db` la ejecuta el propietario, desde `main` y tras fusionar.
- En `tests/test_demo_clon_biblioteca.py` (ficha hecha) solo cambia lo que fija el título y el contenido del documento sembrado.
- En `generacion.py`, `generador_docx.py` y `generador_xlsx.py` (fichas hechas) solo cambia el pie de la demo; fuera de la demo la salida es idéntica byte a byte.
- Sin migraciones. `documentos.py` no cambia: la siembra usa el mismo rellenador desde la propia sala.
