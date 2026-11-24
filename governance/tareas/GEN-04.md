+++
id = "GEN-04"
titulo = "Marca en la interfaz: título EVYDENTIA · LOPDP 360, texto alternativo y logotipos sin la marca del operador"
ola = "backlog"
estado = "pendiente"
tanda = 100
sala = "frontend"
depende_de = ["GEN-01", "FE-19", "FE-28"]
propiedad = ["frontend/src/app/page.tsx", "frontend/src/components/layout/DashboardHeader.tsx", "frontend/public/brand/evydentia-principal.png", "frontend/public/brand/evydentia-negativo.png", "frontend/tests/layout/marca-generica.spec.ts"]
crea = ["frontend/tests/layout/marca-generica.spec.ts"]
arbitro = "Playwright frontend/tests/layout/marca-generica.spec.ts + tsc --noEmit + npm run build; mutación m1; los logotipos nuevos los entrega el propietario (R2)."
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# GEN-04 · Marca en la interfaz: título EVYDENTIA · LOPDP 360, texto alternativo y logotipos sin la marca del operador

**Contrato:** `governance/especificaciones/GEN-04.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- El `<title>` de la portada, «EVYDENTIA · LOPDP 360», y el texto alternativo del logotipo, «EVYDENTIA».
- Los dos logotipos de `frontend/public/brand/` sustituidos por los que entrega el propietario, con el mismo nombre de archivo.

## Límites
- No se lanza sin los dos archivos nuevos del propietario (especificación R2). Pasa por UX/UI.
