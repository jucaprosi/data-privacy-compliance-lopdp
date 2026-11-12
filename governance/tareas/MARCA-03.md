+++
id = "MARCA-03"
titulo = "Nombre único EVYDENTIA en las notificaciones: plantilla de correo"
ola = "backlog"
estado = "en_curso"
sala = "notificaciones"
depende_de = ["NOTIF-01"]
propiedad = ["features/notificaciones/services/plantillas_engine.py", "tests/test_marca_notificaciones.py"]
crea = ["tests/test_marca_notificaciones.py"]
arbitro = "pytest tests/test_marca_notificaciones.py (la plantilla contiene EVYDENTIA y no JUBYS) + suite de notificaciones; mutación documentada: JUBYS vuelve y la prueba falla"
rastros = ["¤interfaz"]
+++

# MARCA-03 · Nombre único EVYDENTIA en las notificaciones: plantilla de correo

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md`, `PRD.md`, `TASKS.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- `features/notificaciones/services/plantillas_engine.py:88` y su prueba nueva.
