+++
id = "DEMO-11"
titulo = "Procedimiento del backend y de la migración de la demo, con su job, su secreto y la membresía del rol"
ola = "D"
estado = "hecha"
tanda = 101
sala = "operaciones"
depende_de = ["DEMO-10"]
propiedad = ["governance/operaciones/DEMO_COMERCIAL.md", "governance/operaciones/entornos/demo/secretos.yaml", "governance/operaciones/entornos/demo/cloud_sql.yaml", "governance/operaciones/entornos/demo/job_migracion.yaml", "governance/operaciones/entornos/demo/cloudrun_backend.yaml", "tests/test_demo11_backend_y_migracion.py"]
crea = ["governance/operaciones/entornos/demo/job_migracion.yaml", "tests/test_demo11_backend_y_migracion.py"]
arbitro = "pytest tests/test_demo11_backend_y_migracion.py tests/test_demo09_web_demo.py; mutaciones m1 a m5."
rastros = ["¤demo", "¤arbitro"]
+++

# DEMO-11 · Backend y migración de la demo

**Contrato:** `governance/especificaciones/DEMO-11.md` (manda sobre esta ficha).

**Origen.** Hallazgo del Tech Lead con autorización del propietario (2026-11-24), al preparar la actualización de la demo a dfc82838. `DEMO_COMERCIAL.md` solo describe la web. La demo no tiene job de migración. El secreto `DATABASE_URL` existe pero no está declarado. No consta que `evydentia_demo_app` sea miembro de `lopdp_app`.

## Entrega
- **§6 de `DEMO_COMERCIAL.md`:** backend (imagen del mismo commit que la web, publicación sin tráfico y vuelta atrás) y migración (copia previa, comprobación del rol, job, recuento de cabezas y registro), sin credenciales.
- **Manifiesto:** `entornos/demo/job_migracion.yaml`, el job `migrar-demo`, declarado como el de producción.
- **Declaraciones:** `secretos.yaml` declara `DATABASE_URL`; `cloud_sql.yaml` declara la membresía de `evydentia_demo_app` en `lopdp_app` y deja de listar las cabezas a mano.
- `cloudrun_backend.yaml` declara la imagen que corre el servicio: `evydentia-demo-containers/backend`.
- **Prueba:** `tests/test_demo11_backend_y_migracion.py`, exógena, sin red y sin `import yaml`.

## Límites
- No toca la nube. Crear el job, el secreto y la membresía en GCP es del propietario, por brief.
- `REGISTRO_MIGRACIONES_MANUALES.md` no cambia: es solo para bases de pruebas (su regla 4). La demo lleva su propio registro en la §6.
- La §5 (web) no cambia.
