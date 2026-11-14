# Brief del propietario · Catálogo de paquetes de Bóveda Cloud (BOV-01)

Fecha: 2026-11-13. Redactado por la sesión de BOV-01. Lo ejecuta el propietario. **Ninguna IA toca la base de producción, la facturación ni los buckets.**

## Qué cambia
La migración `bov01_boveda_paquetes_cuotas` crea:
- `boveda_paquetes`, el catálogo global con los cuatro paquetes del PRD §2.2 y §2.3 (INICIAL, PROFESIONAL, CORPORATIVO y ENTERPRISE).
- `boveda_suscripciones_tenant`, con RLS forzado por organización.
- El rol `lopdp_operador_boveda` (NOLOGIN), el único que puede editar el catálogo. `lopdp_app` solo lo lee.

**Qué no hace este brief:**
- no crea buckets;
- no toca la facturación de Google Cloud;
- no da de alta suscripciones: el alta la hace el operador por `POST /api/v1/boveda-cloud/suscripcion`;
- no reinicia el contador mensual de descargas, que queda para una ficha posterior.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Migrar, tras fusionar y desde `main`
Lo hace quien migra producción, con su `.env`, como en las demás migraciones.
```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
git switch main
git pull --ff-only
python -m alembic upgrade head
python -m alembic current
```
Debe mostrar `bov01_boveda_paquetes_cuotas` (o una revisión posterior).

### 2. Comprobar el catálogo (solo lectura)
```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
python -c "import os,psycopg;from dotenv import load_dotenv;load_dotenv();u=os.environ['MIGRATION_DATABASE_URL'].replace('postgresql+psycopg://','postgresql://');c=psycopg.connect(u);[print(f) for f in c.execute('SELECT codigo, cuota_almacenamiento_bytes, cuota_egress_mensual_bytes, peticiones_api_minuto, tokens_ia_mes, max_claves_integracion, max_webhooks FROM boveda_paquetes ORDER BY codigo')]"
```
Deben salir cuatro filas. ENTERPRISE va con todo en `None`.

### 3. Conceder el rol de edición del catálogo (solo si vas a ajustar valores)
Sustituye `<inicio_de_sesion_del_operador>` por el usuario de base con el que edites el catálogo. **No lo concedas a `lopdp_app`.**
```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
$OPERADOR = "<inicio_de_sesion_del_operador>"
if ($OPERADOR -eq "lopdp_app") { throw "lopdp_app no debe editar el catálogo." }
python -c "import os,sys,psycopg;from psycopg import sql;from dotenv import load_dotenv;load_dotenv();u=os.environ['MIGRATION_DATABASE_URL'].replace('postgresql+psycopg://','postgresql://');c=psycopg.connect(u,autocommit=True);c.execute(sql.SQL('GRANT lopdp_operador_boveda TO {}').format(sql.Identifier(sys.argv[1])));print('ok')" $OPERADOR
```
Para editar, ese usuario hace `SET ROLE lopdp_operador_boveda;` antes del `UPDATE boveda_paquetes ...`.
