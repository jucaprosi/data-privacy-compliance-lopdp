+++
id = "NORM-02"
titulo = "Centro de Vigilancia Normativa: catálogo de resoluciones SPDP, filtros, visor PDF, disparo manual, bitácora y avisos"
ola = "D"
estado = "pendiente"
sala = "inteligencia_normativa, frontend"
depende_de = ["NORM-01", "NOTIF-01", "FE-22"]
propiedad = ["features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-02", "features/inteligencia_normativa/domain/errores.py#NORM-02", "features/inteligencia_normativa/services/revision.py", "app_core/pasillo/notificaciones.py#NORM-02", "api/routers/inteligencia_normativa.py", "tests/test_norm02_centro_vigilancia.py", "tests/matriz/NORM-02.py", "frontend/src/components/normativa/**", "frontend/src/components/layout/menus/NORM-02.ts", "frontend/src/components/layout/pantallas/NORM-02.tsx", "frontend/tests/normativa/**"]
arbitro = "pytest tests/test_norm02_centro_vigilancia.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/normativa + tsc --noEmit + npm run build"
rastros = ["¤inteligencia-normativa", "¤vigilancia-spdp", "¤navegacion-menus"]
+++
# NORM-02 · Centro de Vigilancia Normativa: catálogo, filtros, visor PDF, disparo manual, bitácora y avisos

**Origen.** `PRD_EVYDENTIA_REVENTA_NUBE.md`, Módulo 6.2 (`RF-06`, `RF-07`) y menú 9 «Conocimiento, Vigilancia SPDP». El tablero `TASKS_EVYDENTIA_REVENTA_NUBE.md` la citaba (BL-188, tanda 45) sin ficha.

**Contrato:** `governance/especificaciones/NORM-02.md`.

## Entrega
- Router `api/routers/inteligencia_normativa.py` con `AUTO_REGISTRO = True`, para:
  - el catálogo con filtros;
  - el detalle de una resolución;
  - la descarga del original por URL firmada de corta vida;
  - el disparo manual del monitoreo;
  - la bitácora de corridas;
  - la revisión humana del estado.
- Revisión humana en `services/revision.py`. Solo el DPO o el administrador cambian el estado de una resolución y queda registrado quién y cuándo (`INV_NORMATIVA_HUMAN_LEGAL_VALIDATION`). El operador de plataforma dispara el monitoreo, pero no homologa.
- Aviso al administrador y al DPO de cada organización cuando hay resoluciones nuevas o modificadas, y aviso técnico al operador cuando una corrida falla. Se envía por la compuerta de notificaciones (NOTIF-01), a través del pasillo.
- Pantalla `layout/pantallas/NORM-02.tsx` en el menú Conocimiento (`menus/NORM-02.ts`), con:
  - el catálogo con filtros por número, año, palabra, órgano, materia y estado;
  - el visor PDF integrado;
  - la bitácora de corridas;
  - el botón «Revisar ahora».
- Fila de la matriz de permisos `tests/matriz/NORM-02.py`.

## Pruebas
- `pytest tests/test_norm02_centro_vigilancia.py` comprueba:
  - los filtros;
  - que la URL de descarga caduca;
  - que solo el DPO o el administrador cambian el estado y que queda la traza;
  - que el operador recibe 403 al homologar;
  - el aviso por organización.
- Playwright de `frontend/tests/normativa` recorre el catálogo, el visor y el disparo manual contra el backend real, sin datos simulados (`API-01`).
