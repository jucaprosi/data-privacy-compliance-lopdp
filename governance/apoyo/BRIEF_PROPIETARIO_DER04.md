# Brief para el propietario · DER-04: contracción de las solicitudes ARCO

`¤arbitro`

**Qué hace.** La migración `alembic/versions/20261109_derechos_contraccion_tenant.py` (revisión `20261109_der04_contraccion`) retira de `derechos_arco_solicitudes` la columna vieja `tenant_id` (uuid), el disparador `trg_derechos_arco_tenant_texto` y su función. También retira la política antigua `tenant_isolation_policy`, si sigue viva. La columna `tenant_id_texto` queda obligatoria, y la política vigente con RLS forzada queda sobre ella.

**No tiene vuelta atrás.** El `downgrade` lanza un error: un uuid no se reconstruye a partir del texto. La única vuelta atrás es restaurar el respaldo del paso 3.

**Cuándo.** Solo con el PR de DER-04 fusionado en `main` y con los tres criterios de `governance/tareas/DER-04.md` cumplidos:
- (a) el código, que lo comprueba la prueba 7 en el CI;
- (b) el servicio, que se comprueba en el paso 1;
- (c) la ventana de vuelta atrás, que se confirma en el paso 2.

Conviene que sea la última migración de derechos que se aplique.

Todo Google Cloud es tuyo. Quien preparó este brief solo leyó.

## 1. Criterio (b): ninguna revisión anterior a DER-03 tiene tráfico (solo lectura)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$PROYECTO = "evydentia"; $REGION = "us-central1"
foreach ($S in @("evydentia-backend", "evydentia-web", "evydentia-vault-worker")) {
  Write-Host "== $S"
  gcloud run services describe $S --region $REGION --project $PROYECTO --format="table(status.traffic[].revisionName,status.traffic[].percent,status.traffic[].tag)"
  gcloud run revisions list --service $S --region $REGION --project $PROYECTO --limit 3 --format="table(metadata.name,metadata.creationTimestamp)"
}
foreach ($J in @("purga-demo", "evydentia-migrate")) {
  Write-Host "== job $J"
  gcloud run jobs describe $J --region $REGION --project $PROYECTO --format="value(metadata.generation,spec.template.spec.template.spec.containers[0].image)"
}
```

**Se cumple si:**
- En cada servicio, una sola revisión tiene el 100 % del tráfico, ninguna otra tiene tráfico ni etiqueta, y esa revisión se creó después de la publicación que llevó DER-03 (compara su `creationTimestamp` con la fecha de esa corrida de `deploy-gcp.yml`).
- La imagen de cada Job es de una publicación posterior a DER-03.
- Si `evydentia-web` no consulta la base (no hace SSR contra ella), no cuenta para este criterio.

Si algo no se cumple, no sigas.

## 2. Criterio (c): ventana de vuelta atrás cerrada

Confirma por escrito, en el PR o en `REGISTRO_MIGRACIONES_MANUALES.md`, que DER-03 lleva en servicio al menos una publicación completa sin vuelta atrás. Se proponen 7 días o el fin de la demo; el plazo lo decides tú.

## 3. Respaldo antes de migrar (obligatorio)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$PROYECTO = "evydentia"; $INSTANCIA = "evydentia-production"
gcloud sql backups create --instance $INSTANCIA --project $PROYECTO --description "antes de DER-04"
gcloud sql backups list --instance $INSTANCIA --project $PROYECTO --limit 1
```

El último respaldo debe salir con estado `SUCCESSFUL`. Anota su id.

## 4. Migrar, después de fusionar y desde main

Con `MIGRATION_DATABASE_URL` del rol dueño cargada en la sesión y nunca escrita en un archivo, como en `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md`:

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin main
git switch main
git pull --ff-only origin main
$ACTUAL = (python -m alembic current 2>$null | Select-Object -Last 1).Split(" ")[0]
python scripts/verificar_migracion_compatible.py --desde-revision $ACTUAL
python -m alembic upgrade head
python -m alembic current
```

- El verificador debe aceptar la migración, porque lleva `CONTRACCION = True`. Si marca otra como INCOMPATIBLE, detente.
- `alembic current` debe terminar en la cabeza de main, que incluye `20261109_der04_contraccion`.
- **Si aborta con `lock timeout`**, la tabla estaba ocupada y no cambió nada. Reintenta en un momento de menos tráfico.
- **Si aborta con `DER-04: N solicitud(es) ARCO sin tenant válido` o `N política(s) desconocida(s)`**, tampoco cambió nada. El mensaje solo trae números. Qué hacer con esas filas lo deciden tú y el DPO. Avisa al Tech Lead.

## 5. Comprobar (solo lectura)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
python scripts/verificar_cloudsql_conexion.py --rol lopdp_app
```

Debe dar código 0. Después, anota la migración y el id del respaldo en `REGISTRO_MIGRACIONES_MANUALES.md`.
