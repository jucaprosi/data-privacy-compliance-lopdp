+++
id = "DEMO-07"
titulo = "Infraestructura de la demo en Google Cloud (personas, sin agente)"
ola = "D"
estado = "pendiente"
sala = "operaciones"
depende_de = ["DEMO-02", "DEMO-04", "DEMO-05", "DEMO-06", "GCP-01", "GCP-03", "GCP-04"]
propiedad = ["governance/operaciones/DEMO_COMERCIAL.md", "governance/operaciones/entornos/demo/**"]
arbitro = "Recorrido de aceptación documentado en governance/operaciones/DEMO_COMERCIAL.md: entrada, «Ver como», terminar y purga de la noche siguiente comprobados en el proyecto demo"
rastros = ["¤demo"]
+++

# DEMO-07 · Infraestructura de la demo en Google Cloud (personas, sin agente)

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `operaciones`. Sin agente: la hacen personas.

**Por qué.** Proyecto de Google Cloud de la demo, despliegue por digest, Cloud Scheduler, cuenta de servicio de la purga, OAuth y secretos. Lo hacen Juan Carlos, Aleczandra o José, nunca una sesión de IA (§5.5).

## Entrega
- Proyecto demo con Cloud Run (backend y frontend), Cloud SQL **siempre encendida** y buckets propios; `APP_ENV=demo` (decisiones del propietario, PRD §5.6.2 y §5.6.7, 2026-11-07).
- IAP en Cloud Run limitado a un grupo de Google de vendedores, además de `DEMO_VENDEDORES`.
- Dirección: subdominio `demo.` del dominio comercial cuando esté comprado; mientras tanto, `run.app`.
- `DEMO_COMERCIAL.md` explica cómo dar de alta o de baja a un vendedor en las dos listas (grupo de IAP y `DEMO_VENDEDORES`).
- Secret Manager: `DEMO_VENDEDORES` y la credencial de purga, solo legible por la cuenta del job.
- Cloud Scheduler nocturno del job de DEMO-05.
- Origen OAuth de la demo; siembra de la plantilla con DEMO-03.
- Despliegue del mismo digest que pasó por pruebas (§5.6, flujo 1.6).

## Pruebas
- El recorrido de aceptación del arbitro, con su fecha y quién lo hizo.

## Límites
- Contrato congelado: rutas, cuerpos y códigos de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, para y consulta a Tech Lead.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS ni `main.py`.
- En archivos con secciones `#ID` escribe solo dentro de tus marcas `# --- INICIO <ID> --- … # --- FIN <ID> ---`.
- Nunca uses la base ni el proyecto de producción; solo datos ficticios con correos `.invalid`.

## Fuentes
- `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` §5.6 (demo comercial) y §5.6.8 (corte confirmado por el Arquitecto ADPA y el CTO, 2026-11-07).
- `governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, invariantes 60 a 63.
- Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Interfaz: `governance/apoyo/UX_DEMO_EVYDENTIA.md` (lo que cambia) sobre `governance/apoyo/UX_DEMO_COMERCIAL.md`.
