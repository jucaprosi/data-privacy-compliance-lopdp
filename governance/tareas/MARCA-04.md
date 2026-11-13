+++
id = "MARCA-04"
titulo = "Nombre único EVYDENTIA en el frontend: paleta, reporte, página de la plataforma y configuración del proyecto"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["DIAG-07", "BIB-118", "FE-28", "DER-07"]
propiedad = ["frontend/src/components/CommandPalette.tsx", "frontend/src/lib/reportes/generarReporteAssessment.ts", "frontend/src/app/plataforma/page.tsx", "frontend/src/components/ProjectConfig.tsx", "frontend/src/types/index.ts", "frontend/tests/marca/marca.spec.ts"]
crea = ["frontend/tests/marca/marca.spec.ts"]
arbitro = "Playwright frontend/tests/marca/marca.spec.ts (la paleta muestra EVYDENTIA y no JUBYS) + tsc --noEmit + npm run build; antes, git grep de los specs que buscan esos textos (lección de FE-27); mutación documentada: JUBYS vuelve en CommandPalette.tsx y el spec falla"
rastros = ["¤navegacion-menus"]
+++

# MARCA-04 · Nombre único EVYDENTIA en el frontend: paleta, reporte, página de la plataforma y configuración del proyecto

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- `PRD.md` y `TASKS.md` son los artefactos vigentes únicos desde #732, #733 y #734 (un solo bloque: PRD, INVARIANTS, TASKS y VPA_MAP; el PMV antiguo vive fuera del repositorio, en el respaldo del propietario). No se renombran ni se tocan salvo por su propia ficha (corrección autorizada por el propietario, 2026-11-13).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- `CommandPalette.tsx` (líneas 210 y 742), `generarReporteAssessment.ts:124`, `plataforma/page.tsx:183-184` (valores de ejemplo «JUBYS Consultores»: se cambian por un ejemplo neutro), `ProjectConfig.tsx:257` (placeholder), `types/index.ts:2` (comentario).
- Va **después de DIAG-07** (comparte `types/index.ts` y quizá specs). Mide antes las dueñas vivas de `CommandPalette.tsx` (DER-07 lo toma) y de los demás; las rutas con dueña viva van como sección `#MARCA-04` sembrada o la ficha depende de la dueña.
- El comentario «dominio JUBYS G01-G16» de `dimensionesSGPDP.ts:113` queda fuera si el archivo tiene dueñas vivas.
