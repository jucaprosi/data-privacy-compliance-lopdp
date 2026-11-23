+++
id = "LEG-07"
titulo = "Finales de línea CRLF en los .bat para que cmd lea el aviso de autor"
ola = "backlog"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["ENT-01", "LEG-06", "MARCA-05", "QA-02"]
propiedad = [".gitattributes", "ejecutar_arnes_tres_pilares.bat", "ejecutar_arnes_verificacion.bat", "iniciar_backend.bat", "iniciar_frontend.bat", "iniciar_todo.bat", "scripts/entorno.bat", "tests/test_leg06_aviso_de_autor.py"]
crea = []
arbitro = "pytest tests/test_leg06_aviso_de_autor.py; git ls-files --eol muestra i/crlf en los seis .bat; cada .bat arranca en cmd sin «no se reconoce como un comando»; reparto, índice y especificaciones con código 0; mutaciones m1 y m2."
rastros = ["¤ip", "¤arbitro"]
+++

# LEG-07 · Finales de línea CRLF en los .bat para que cmd lea el aviso de autor

**Contrato:** `governance/especificaciones/LEG-07.md` (manda sobre esta ficha).

**Origen.** Defecto de LEG-06 (#959), reportado por su ingeniero y comprobado por el CTO el 2026-11-23.

## Entrega
- `*.bat` y `*.cmd` con `-text` en `.gitattributes` (el índice guarda CRLF tal cual; `text eol=crlf` lo guarda en LF).
- Los seis `.bat` renormalizados a CRLF.
- Una prueba que exige CRLF en todo `.bat` y `.cmd` versionado.

## Límites
- El texto del aviso y `scripts/poner_aviso_de_autor.py` no cambian.
- Puede ir en paralelo con FE-29, que no toca `.bat`.
