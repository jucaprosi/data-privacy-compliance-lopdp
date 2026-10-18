+++
id = "SEC-02"
titulo = "Auditoría de seguridad previa a producción"
ola = "D"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["SEC-03", "RM-10", "RM-13", "SEC-04", "SEC-05", "SEC-06"]
propiedad = ["governance/AUDITORIA_SEGURIDAD_HOJA_DE_RUTA.md"]
arbitro = "informe sin hallazgos críticos abiertos"
rastros = ["¤seguridad"]
+++

# SEC-02 · Auditoría de seguridad previa a producción

**Objetivo.** Revisión final antes de abrir el módulo a clientes.

## Entrega
- RLS, SoD, autenticación, carga de evidencia, errores públicos y secretos.
- Comprobar lo entregado por SEC-04 (evidencia filtrada por rol), SEC-05 (validación de la evidencia en el servidor) y SEC-06 (cabeceras HTTP de seguridad).

- **Endpoints sin ninguna identidad** (hallazgo del 2026-10-17, comprobado en `api/routers/`): `niif18`, `riesgos_mtge`, `arco` e `implementation_assistant` no declaran dependencia de identidad alguna, ni siquiera con `AUTH_MODE=oidc`. Decidir para cada uno si es público a propósito o debe exigir sesión.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
