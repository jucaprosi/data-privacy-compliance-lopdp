+++
id = "NOTIF-05"
titulo = "La bandeja nombra cada enlace por su destino"
ola = "D"
estado = "en_curso"
tanda = 116
sala = "notificaciones"
depende_de = ["NOTIF-02", "NOTIF-04"]
propiedad = ["frontend/src/components/avisos/BandejaAvisos.tsx", "frontend/tests/avisos/bandeja.spec.ts"]
crea = []
arbitro = "npx playwright test frontend/tests/avisos/bandeja.spec.ts; tsc --noEmit; mutaciones m1 y m2."
rastros = ["¤arbitro"]
+++

# NOTIF-05 · La bandeja nombra cada enlace por su destino

**Contrato:** `governance/especificaciones/NOTIF-05.md` (manda sobre esta ficha).

**Origen.** Revisión del Tech Lead de #1104 (NOTIF-04, 2026-11-27): la bandeja escribe «Revisar la versión» en todo enlace, y los avisos de capacidad llevan a `/plataforma/capacidades`.

## Entrega
- El texto del enlace de cada aviso sale de su destino.

## Límites
- En `frontend/src/components/avisos/BandejaAvisos.tsx`, solo el texto del enlace. Sin cambios en la API ni en la base.
- En `frontend/tests/avisos/bandeja.spec.ts`, solo los casos de §5.
