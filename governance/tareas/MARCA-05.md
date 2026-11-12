+++
id = "MARCA-05"
titulo = "Nombre único EVYDENTIA en los lanzadores de Windows"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["iniciar_backend.bat", "iniciar_frontend.bat", "iniciar_todo.bat", "tests/test_marca_lanzadores.py"]
crea = ["tests/test_marca_lanzadores.py"]
arbitro = "pytest tests/test_marca_lanzadores.py (los tres .bat no contienen JUBYS y contienen EVYDENTIA); mutación documentada: JUBYS vuelve en un .bat y la prueba falla (no hay árbitro más fuerte: es texto de consola)"
rastros = ["¤observabilidad"]
+++

# MARCA-05 · Nombre único EVYDENTIA en los lanzadores de Windows

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md`, `PRD.md`, `TASKS.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- Los tres `.bat` de la raíz, en sus títulos y su `echo`; prueba nueva que los lee.
- `ejecutar_arnes_*.bat` son gobernanza reservada: no se tocan.
