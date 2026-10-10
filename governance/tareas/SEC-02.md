+++
id = "SEC-02"
titulo = "Auditoría de seguridad previa a producción"
ola = "D"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["SEC-03", "RM-10", "RM-13"]
propiedad = ["governance/AUDITORIA_SEGURIDAD_HOJA_DE_RUTA.md"]
arbitro = "informe sin hallazgos críticos abiertos"
rastros = ["¤seguridad"]
+++

# SEC-02 · Auditoría de seguridad previa a producción

**Objetivo.** Revisión final antes de abrir el módulo a clientes.

## Entrega
- RLS, SoD, autenticación, carga de evidencia, errores públicos y secretos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
