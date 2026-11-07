+++
id = "DEMO-05"
titulo = "Infraestructura de la demo comercial: rama Neon, proyectos Vercel, OAuth y purga nocturna"
ola = "D"
estado = "pendiente"
sala = "operaciones"
depende_de = ["DEMO-02", "DEMO-03", "DEMO-04"]
propiedad = ["governance/operaciones/DEMO_COMERCIAL.md", ".github/workflows/demo-purga.yml"]
arbitro = "Recorrido de aceptación documentado en governance/operaciones/DEMO_COMERCIAL.md: entrada, cambio de persona, terminar y purga de la noche siguiente comprobada en la rama demo"
rastros = ["¤demo"]
+++

# DEMO-05 · Infraestructura de la demo comercial: rama Neon, proyectos Vercel, OAuth y purga nocturna

**Sin agente.** La hace una persona del equipo (responsable de operación). Ninguna sesión de IA crea ramas de Neon, proyectos de Vercel, secretos ni flujos de `.github/workflows/`.

## Entrega
1. Rama Neon `demo`, hija de `test-main`, con `alembic upgrade head` y la plantilla sembrada (`scripts/demo/sembrar_plantilla_demo.py`). La base demo no tiene filas en `operadores_plataforma`.
2. Proyectos Vercel `lopdp-demo-front` y `lopdp-demo-back`. Backend: `DEMO_MODE=1`, `DATABASE_URL` de la rama `demo` con `lopdp_app`, `JWT_SECRET` y `SESSION_SECRET` propios, `DEMO_VENDEDORES`, `CORS_ORIGINS` solo con el frontend demo. Ninguna variable apunta a producción.
3. Cliente OAuth de Google: se recomienda uno propio para la demo; como mínimo, añadir los orígenes de la demo.
4. Flujo `.github/workflows/demo-purga.yml`, nocturno, con el parche que entrega DEMO-02. Usa un entorno de GitHub propio (`demo-purga`) con el secreto de la credencial del dueño de la rama `demo`.
5. `governance/operaciones/DEMO_COMERCIAL.md`: qué existe, quién lo administra, cómo se añade un vendedor y el recorrido de aceptación.

## Límites
- Nunca la base de producción ni sus secretos.
- Vercel Hobby excluye el uso comercial: riesgo ya anotado por el CTO para producción; la decisión de plan es del propietario.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y proyección ADPA del Arquitecto de soluciones: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; vencimiento a los 60 minutos sin actividad; tope de 20 demos activas; lista `DEMO_VENDEDORES` en Vercel; dirección `*.vercel.app`; una sola demo activa por vendedor (la nueva entrada vence la anterior, motivo `reemplazo`).
