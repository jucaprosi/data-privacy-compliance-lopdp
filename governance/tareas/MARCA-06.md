+++
id = "MARCA-06"
titulo = "Nombre único EVYDENTIA en los títulos de los documentos normativos y en la tabla de la firma electrónica"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = ["CI-02", "CI-03", "CI-10", "CI-17", "FIRMA-01", "GOB-04"]
propiedad = ["governance/ARQUITECTURA_SOFTWARE.md", "governance/DOCTRINAS.md", "governance/METODOLOGIAS.md", "governance/arquitectura/FIRMA_ELECTRONICA_BOCETO.md"]
crea = []
arbitro = "git diff solo toca la línea 1 de los tres documentos normativos y la fila de la línea 44 de FIRMA_ELECTRONICA_BOCETO.md; verificar_huellas y la guardia de estigmergia sin cambios en tokens ¤, roles ¤¤, candados ¤¬ ni encabezados"
rastros = ["¤doctrinas"]
+++

# MARCA-06 · Nombre único EVYDENTIA en los títulos de los documentos normativos y en la tabla de la firma electrónica

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Regla común de las fichas MARCA
- Se renombra el **texto visible** «JUBYS» a «EVYDENTIA»; comentarios y docstrings también. La plataforma se llama solo EVYDENTIA.
- **No se renombran** las claves de `localStorage` (`jubys-audit-storage`, `jubys-proyectos-v1`: renombrarlas borra lo guardado del usuario en cada navegador; decisión del CTO 2026-11-11: no renombrar ahora y revisar al final del trabajo si hace falta una migración de lectura, en ficha aparte) ni los nombres de logger (`jubys.arranque`, `jubys_lopdp_json_logger`: posible contrato con Cloud Logging y alertas; el propietario mide primero con `gcloud logging metrics list` y `gcloud alpha monitoring policies list`, solo lectura).
- «Dominio JUBYS G01-G16» pasa a «dominio G01-G16» sin cambiar identificadores.
- Quedan como historia, sin tocar: `APORTES_INEDITOS.md`, la auditoría, `governance/tareas/DIAG-01.md`, `PRD.md`, `TASKS.md` y los títulos de obras citadas («Guía de Diseño JUBYS v1.1», «Blueprint JUBYS»).
- Las pruebas que fijan el texto cambian en el mismo PR que su fuente. Antes de cambiar, `git grep` de los specs y pruebas que buscan el texto viejo; si una ajena lo fija y no es tuya, para y avisa al Tech Lead.
- Sin guardia global «no aparece JUBYS»: solo sobre una lista cerrada.

## Entrega
- `ARQUITECTURA_SOFTWARE.md:1`, `DOCTRINAS.md:1` y `METODOLOGIAS.md:1`: **solo el nombre del producto dentro del título**; es la única excepción en los `.md` normativos y la regla de estigmergia aplica (no se tocan tokens `¤`, roles ni la estructura de encabezados).
- `FIRMA_ELECTRONICA_BOCETO.md:44`: la fila «JUBYS / Plataforma SaaS propia».
- Rutas medidas con `git ls-files` sobre origin/main.
