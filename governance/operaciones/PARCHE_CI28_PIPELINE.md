# Parche del pipeline para CI-28 (lo aplica el propietario)

`.github/workflows/zero-regression-pipeline.yml` no es de la ficha CI-28 (decisión del CTO, R6b): este documento entrega el parche. El propietario lo aplica en `main` **antes** de fusionar CI-28. Con una sola cabeza funciona igual que hoy; con una cabeza por sala es obligatorio, porque `alembic upgrade head` falla si hay más de una.

`tests/test_alembic_cabeza_por_sala.py::test_despliegue_usa_heads` falla mientras el pipeline contenga `alembic upgrade head` sin la `s`; por eso CI-28 no se fusiona sin este parche.

## Cambio

Un solo paso, el ancla `&migrar_contenedor` (los demás trabajos lo reutilizan con `*migrar_contenedor`):

```diff
       - &migrar_contenedor
         name: Migrar el contenedor a la cabeza de Alembic
         env:
           # Literal a proposito: solo puede apuntar al servicio local del runner, nunca a un secreto externo.
           MIGRATION_DATABASE_URL: postgresql://lopdp_beta_owner:solo-en-este-runner@localhost:5432/lopdp
-        run: python -m alembic upgrade head
+        run: python -m alembic upgrade heads
```

Opcionalmente, el nombre del paso puede pasar a «Migrar el contenedor a las cabezas de Alembic»; `tests/test_ci_migrar_contenedor.py` no depende del nombre del paso, sí del texto `alembic upgrade` y del literal de la URL.

## Comprobación tras aplicarlo

```bash
git grep -n "alembic upgrade head[^s]" -- .github scripts
python -m pytest tests/test_alembic_cabeza_por_sala.py::test_despliegue_usa_heads tests/test_ci_migrar_contenedor.py -q --noconftest
```

La primera no debe imprimir nada; la segunda debe dar verde.

## Fuera de este parche

Nada queda para otra ficha. `backend.Dockerfile`, los dos `.ps1` de entorno de pruebas y los cuatro briefs (`BRIEF_PROPIETARIO_BOV-01.md`, `BRIEF_PROPIETARIO_DER04.md`, `PRUEBAS_EN_FISICO.md`, `entornos/produccion/MIGRAR_PRODUCCION.md`) ya usan `upgrade heads` en el PR de CI-28, y `test_despliegue_usa_heads` los vigila (flujos, scripts, Dockerfile y esos briefs). Lo único que el PR de CI-28 no puede cambiar es el workflow (arriba) y el Cloud Run Job (abajo), ambos del propietario.

## Cloud Run Job

El job `evydentia-migrate` (proyecto `evydentia`, región `us-central1`) tiene hoy `command` «alembic» y `args` «upgrade,head» (lectura con `gcloud` de solo lectura). Con una cabeza por sala debe pasar a `heads`. Lo cambia el propietario, antes de fusionar CI-28; la sesión de CI-28 no lo ejecuta.

```bash
gcloud run jobs update evydentia-migrate --region us-central1 --project evydentia --args=upgrade,heads
```

Comprobación (debe dar «upgrade;heads» o equivalente):

```bash
gcloud run jobs describe evydentia-migrate --region us-central1 --project evydentia --format="value(spec.template.spec.template.spec.containers[0].args)"
```
