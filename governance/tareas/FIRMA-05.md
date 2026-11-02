+++
id = "FIRMA-05"
titulo = "Matrices de aceptación deterministas de FIRMA-03 y FIRMA-04"
ola = "backlog"
estado = "en_curso"
sala = "firma_electronica"
depende_de = ["FIRMA-03", "FIRMA-04"]
propiedad = ["tests/matriz/FIRMA-03.py", "tests/matriz/FIRMA-04.py"]
arbitro = "pytest tests/matriz/FIRMA-03.py tests/matriz/FIRMA-04.py contra la rama Neon de la persona (incluido RLS con lopdp_app) + suite completa + scripts/generar_indice_tareas.py --verificar"
rastros = ["¤firma-electronica", "¤arbitro"]
+++

# FIRMA-05 · Matrices de aceptación deterministas de FIRMA-03 y FIRMA-04

**Objetivo.** Añadir los archivos de la carpeta `tests/matriz/` que exige `test_matriz_permisos.py` para FIRMA-03 y FIRMA-04: cada archivo exporta `FILAS = []` (los endpoints resuelven por tenant, no por rol) y define los casos de aceptación completos de la sala `firma_electronica` para la suite de tres pilares.

**Contrato:** `governance/especificaciones/FIRMA-05.md` (manda sobre esta ficha en casos y aceptación).

## Entrega
- `tests/matriz/FIRMA-03.py` — 10 casos F03-01..F03-10 que cubren la persistencia de `firma_sessions`, RLS, auditoría e inmutabilidad, ejecutados con el rol restringido `lopdp_app`.
- `tests/matriz/FIRMA-04.py` — 11 casos F04-01..F04-11 que cubren los cuatro endpoints HTTP y el webhook HMAC-SHA256, sin mocks de BD.
- `FILAS = []` en ambos archivos: los endpoints de firma resuelven la organización por identidad o por HMAC, no por rol de la matriz de permisos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad.
