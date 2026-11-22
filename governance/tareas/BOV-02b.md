+++
id = "BOV-02b"
titulo = "Montaje de los routers de objetos y del orquestador de la bóveda por su compuerta"
ola = "backlog"
estado = "en_curso"
sala = "boveda_cloud"
depende_de = ["BOV-01", "BOV-02", "BOV-04", "ORG-22c", "RM-25b"]
propiedad = ["features/boveda_cloud/boveda_cloud_service.py#BOV-01", "tests/matriz/BOV-02b.py", "tests/matriz/roles/auditor.py#BOV-02b", "tests/test_bov02b_montaje_routers.py", "tests/test_matriz_permisos.py", "tests/test_bov01_paquetes_cuotas.py"]
crea = ["tests/matriz/BOV-02b.py", "tests/test_bov02b_montaje_routers.py"]
arbitro = "pytest tests/test_bov02b_montaje_routers.py tests/test_matriz_permisos.py tests/test_bov04_orquestador_diez_dimensiones.py; mutación m1."
rastros = ["¤rbac-tenant", "¤arbitro"]
+++

# BOV-02b · Montaje de los routers de objetos y del orquestador de la bóveda por su compuerta

**Contrato:** `governance/especificaciones/BOV-02b.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-21), aviso de `BRIEFS_TAREAS_LIBRES.md` §2. Medido en `origin/main` 60b8a5e0: en el OpenAPI solo aparece `/api/v1/boveda-cloud/suscripcion`. No están montados ni los dos POST de objetos (BOV-02) ni `GET /orquestador-10d` (BOV-04).

## Entrega
- El `router` de la compuerta `boveda_cloud_service` reúne los tres routers de la sala. `main.py` no cambia: ya registra `features.boveda_cloud.boveda_cloud_service` en su sección `BOV-01`.
- Filas de la matriz para las tres rutas nuevas y la decisión del auditor.

## Límites
- La migración `bov02_boveda_objetos_custodia.py` en Cloud SQL la aplica el propietario.
