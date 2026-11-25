+++
id = "NOTIF-02"
titulo = "Avisos en la plataforma y recordatorios para quienes revisan versiones de plantillas"
ola = "D"
estado = "pendiente"
tanda = 111
sala = "notificaciones"
depende_de = ["BIB-406", "NORM-07"]
propiedad = ["alembic/versions/20261125_notif02_avisos.py", "alembic/salas.py", "features/notificaciones/domain/avisos.py", "features/notificaciones/services/avisos_plataforma.py", "features/notificaciones/notificaciones_service.py", "app_core/pasillo/notificaciones.py", "app_core/pasillo/biblioteca.py#NOTIF-02", "api/routers/avisos.py", "main.py#NOTIF-02", "frontend/src/components/layout/menus/NOTIF-02.ts", "frontend/src/components/layout/menus/index.ts#NOTIF-02", "frontend/src/components/layout/pantallas/NOTIF-02.tsx", "frontend/src/components/layout/pantallas/index.tsx#NOTIF-02", "frontend/src/components/layout/DashboardHeader.tsx#NOTIF-02", "frontend/src/components/avisos/BandejaAvisos.tsx", "frontend/tests/avisos/bandeja.spec.ts", "tests/test_notif02_avisos.py"]
crea = ["alembic/versions/20261125_notif02_avisos.py", "features/notificaciones/domain/avisos.py", "features/notificaciones/services/avisos_plataforma.py", "api/routers/avisos.py", "frontend/src/components/layout/menus/NOTIF-02.ts", "frontend/src/components/layout/pantallas/NOTIF-02.tsx", "frontend/src/components/avisos/BandejaAvisos.tsx", "frontend/tests/avisos/bandeja.spec.ts", "tests/test_notif02_avisos.py"]
arbitro = "pytest tests/test_notif02_avisos.py tests/test_alembic_cabeza_por_sala.py tests/test_adpa_bulkhead.py; npx playwright test frontend/tests/avisos/bandeja.spec.ts; mutaciones m1 a m7."
rastros = ["¤arbitro"]
+++

# NOTIF-02 · Avisos en la plataforma y recordatorios para quienes revisan versiones de plantillas

**Contrato:** `governance/especificaciones/NOTIF-02.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS` v1, v2 y v3 (2026-11-25), base `origin/main` ed575cd2, con las decisiones D1 a D7 del CTO y la propuesta de pantallas y textos del UX/UI (2026-11-25).

## Entrega
- Tabla `avisos_plataforma`, primera migración de la sala.
- Sincronización de avisos y recordatorios desde las versiones en revisión de la biblioteca.
- API de la bandeja y botón de la cabecera.
- Pantalla Inicio › Avisos.
- Pruebas de backend y de frontend.

## Límites
- El correo no entra: queda en una ficha aparte, con su brief al propietario (D7), porque `main` no tiene proveedor de correo activo.
- En `app_core/pasillo/biblioteca.py` (BIB-406, tanda anterior) solo se añade `versiones_en_revision()`, en su sección marcada.
- En `alembic/salas.py` (CI-28, hecha) solo se añade la tabla nueva.
- La ejecución programada sale como brief al propietario; esta ficha no toca la nube.
