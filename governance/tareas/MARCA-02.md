+++
id = "MARCA-02"
titulo = "Nombre único EVYDENTIA en el diagnóstico: informes, descripción del campo y textos con prueba"
ola = "backlog"
estado = "en_curso"
sala = "diagnostico"
depende_de = ["DIAG-02", "DIAG-08", "DIAG-13"]
propiedad = ["features/diagnostico/services/report_generator.py", "api/routers/diagnostico.py", "tests/test_diagnostico_timebox.py"]
crea = []
arbitro = "pytest tests/test_diagnostico_timebox.py con el texto nuevo + suite de diagnóstico; mutación documentada: «JUBYS» vuelve en report_generator.py y la prueba falla"
rastros = ["¤diagnostico"]
+++

# MARCA-02 · Nombre único EVYDENTIA en el diagnóstico: informes, descripción del campo y textos con prueba

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md`, `PRD.md`, `TASKS.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- `features/diagnostico/services/report_generator.py` líneas 93, 173, 258 y 318; `api/routers/diagnostico.py:56` (descripción del campo); `tests/test_diagnostico_timebox.py:79` cambia con su fuente.
- Los comentarios «dominio JUBYS G01-G16» de `diagnostico_service.py:75` y `dimensiones_sgpdp.py:142` van como comentario en la ficha que posea esos archivos o en una sección `#MARCA-02` sembrada: `diagnostico_service.py` tiene muchas dueñas vivas y no se toma entero.
