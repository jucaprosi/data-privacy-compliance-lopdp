+++
id = "NOTIF-04"
titulo = "Aviso a los operadores de cada concesión y retiro de capacidades editoriales"
ola = "D"
estado = "hecha"
tanda = 115
sala = "notificaciones"
depende_de = ["NOTIF-02", "BIB-411", "OPE-01"]
propiedad = ["alembic/versions/20261127_notif04_tipo_capacidad.py", "tests/test_db_notif04_tipo_capacidad.py", "features/notificaciones/services/avisos_capacidades.py", "api/routers/avisos_capacidades.py", "main.py#NOTIF-04", "features/notificaciones/notificaciones_service.py#NOTIF-04", "tests/test_notif04_avisos_capacidades.py"]
crea = ["alembic/versions/20261127_notif04_tipo_capacidad.py", "tests/test_db_notif04_tipo_capacidad.py", "features/notificaciones/services/avisos_capacidades.py", "api/routers/avisos_capacidades.py", "tests/test_notif04_avisos_capacidades.py"]
arbitro = "pytest tests/test_notif04_avisos_capacidades.py tests/test_db_notif04_tipo_capacidad.py tests/test_alembic_cabeza_por_sala.py tests/test_adpa_bulkhead.py; mutaciones m1 a m4."
rastros = ["¤arbitro"]
+++

# NOTIF-04 · Aviso a los operadores de cada concesión y retiro de capacidades editoriales

**Contrato:** `governance/especificaciones/NOTIF-04.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_UXUI_BIBLIOTECA_OPERADORES` (2026-11-25) y parte de pantalla del UX/UI `UXUI_PARTE_PANTALLA_BIBLIOTECA_OPERADORES` (2026-11-25). El propietario decidió que el equipo editorial de la biblioteca (Aleczandra, José y Juan Carlos) trabaja como operadores de la plataforma, sin organización, «desde el código». El CTO aprobó el corte y la identidad: una fila en `users` por operador, enlazada por `operadores_plataforma.usuario_id`.

**Decisión C del CTO (2026-11-25).** Cada concesión y cada retiro avisan a todos los operadores activos. Va en esta ficha, que depende de NOTIF-02 y BIB-411, para que ninguna de las dos espere a la otra.

## Entrega
- Tipo de aviso `capacidad_editorial`, con su sincronización en un servicio y un router propios.

## Límites
- En `features/notificaciones/notificaciones_service.py`, solo su sección marcada: importa `avisos_capacidades` y lo añade a `__all__`. El router entra por esa compuerta (`tests/test_adpa_bulkhead.py`).
- No toca los archivos de NOTIF-02 ni de NOTIF-03: escribe en `avisos_plataforma` con su propio servicio. Sin migración: `tipo` es texto sin CHECK.
- El router se registra en la sección `main.py#NOTIF-04`.
- No toca la nube.
