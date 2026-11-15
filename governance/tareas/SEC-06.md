+++
id = "SEC-06"
titulo = "Cabeceras HTTP de seguridad"
ola = "D"
estado = "hecha"
sala = "pasillo_central, frontend"
depende_de = ["RM-13"]
propiedad = ["frontend/next.config.ts", "tests/test_cabeceras_seguridad.py", "frontend/tests/seguridad/cabeceras.spec.ts"]
arbitro = "pytest tests/test_cabeceras_seguridad.py + Playwright de frontend/tests/seguridad + next build; la comprobación en el despliegue la hace el propietario con curl -I"
rastros = ["¤seguridad", "¤ci-cd"]
+++

# SEC-06 · Cabeceras HTTP de seguridad

**Objetivo.** Configurar en `frontend/next.config.ts` HSTS, CSP, X-Frame-Options y cabeceras equivalentes de seguridad. Puede que la plataforma ponga algunas por su cuenta: no está verificado.

## Entrega
- Frontend: `headers()` en `next.config.ts` con `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` y `frame-ancestors` contra el clickjacking.
- CSP primero en modo `Content-Security-Policy-Report-Only`: la interfaz usa Tailwind y los scripts de Next, y una política estricta puede romperla. Pasarla a modo obligatorio es decisión del propietario tras observar los informes. No relajes con `unsafe-inline` sin dejar constancia y motivo.
- Backend (`main:app`): cabeceras de seguridad equivalentes verificadas en los manifiestos y respuestas del servidor.
- Pruebas: una de Python que verifica las declaraciones de seguridad y otra de Playwright que comprueba las cabeceras reales del servidor del frontend. Comprueba con `next start` que `/dashboard` sigue respondiendo 200.

## Límites
- No activa la CSP obligatoria. Las cabeceras de los despliegues reales las verifica el propietario.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
