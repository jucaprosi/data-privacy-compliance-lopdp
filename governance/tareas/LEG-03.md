+++
id = "LEG-03"
titulo = "Verificación con el texto oficial de los artículos y plazos marcados (*) en el PRD, y fuente única de citas legales"
ola = "backlog"
estado = "pendiente"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/apoyo/CITAS_LEGALES_VERIFICADAS.md"]
arbitro = "el documento existe, cada dato lleva su artículo literal y su fuente oficial, separa lo verificado de lo no verificado y propone un valor por parámetro; lo aprueba el propietario"
rastros = ["¤regulation-code", "¤seguridad"]
+++

# LEG-03 · Verificación legal de los (*) del PRD y fuente única de citas

**Decisión del propietario (2026-10-28).** «Nada por ahora, pero documenta la tarea.» La ficha queda en `backlog`: no se lanza hasta que el propietario lo decida, y se coordina con el dictamen del abogado sobre las plantillas de la Biblioteca.

**Objetivo.** El PRD incorporó la estructura funcional EVYDENTIA (PR #210) con artículos y plazos marcados (*) que el documento de origen pide confirmar con el texto oficial de la LOPDP. En esta sesión se confirmaron por fuentes secundarias los Arts. 42, 43 y 48, y **no** se confirmaron los Arts. 12–24, 47 ni 55–61. Además, la interfaz cita hoy artículos distintos de los del PRD (`dashboardNavigation.ts`: «Art. 35» para el RAT, «Art. 37» para derechos ARCO, «Arts. 21-24 · SLA 15d», «Art. 60» para transferencias, «Art. 48» para el DPO; `Playbook Incidentes`: «SLA 72h»). La plataforma necesita **una sola fuente de citas y plazos**: el paquete normativo (PRD, apartado 6), del que lean el frontend, los informes y el copiloto.

## Entrega
- `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md` con:
  - **Identificación oficial de cada fuente leída:** LOPDP (Registro Oficial Suplemento 459, 26-may-2021), Reglamento General (Decreto Ejecutivo 904), Reglamento del Delegado (Resolución SPDP-SPD-2025-0028-R), Norma técnica de vulneraciones (Resolución SPDP-SPD-2026-0040-R; ya leída en LEG-02), guía de riesgos y EIPD de la SPDP, metodología de multas (Resolución SPDP-SPD-2025-0022-R). Preferir `spdp.gob.ec` o el Registro Oficial; un resumen comercial no vale como fuente.
  - **Tabla de verificación**, una fila por dato del PRD con (*): dato, dónde aparece en el PRD, artículo literal, fuente y URL oficial, valor confirmado, y estado `verificado` o `no verificado`. Como mínimo:
    - derechos del titular y su enumeración (acceso, rectificación y actualización, eliminación, oposición, portabilidad, suspensión del tratamiento, no ser objeto de decisiones automatizadas): Arts. 12–24 (*);
    - registro de actividades de tratamiento y a quién obliga: Art. 47 (*) frente al «Art. 35» que muestra la interfaz;
    - transferencias internacionales y garantías: Arts. 55–61 (*) frente al «Art. 60» de la interfaz;
    - medidas de seguridad: Art. 37 (*);
    - evaluación de impacto, supuestos de obligatoriedad y consulta previa: Art. 42 (*) y guía de la SPDP;
    - vulneraciones: Arts. 43–46 (*) y los plazos encargado → responsable 2 días, responsable → SPDP 5 días, responsable → titulares 3 días, **con su unidad** (hábiles o calendario) y el momento desde el que cuentan;
    - respuesta a solicitudes de derechos: 15 días (*), con su unidad y el momento desde el que cuentan, frente al «SLA 15d» de la interfaz;
    - delegado de protección de datos: Arts. 48–50 y Reglamento del Delegado (ya verificados en LEG-01; solo se consolidan en la tabla);
    - canal de notificación a la Autoridad (SISPDP) y datos para el registro ante la SPDP (*).
  - **Valor propuesto por parámetro del paquete normativo** (apartado 6 del PRD): plazos, unidad, autoridad, canal, tipos de derecho, bases de legitimación, categorías sensibles. Cada valor con su cita; sin cita, queda como `no verificado` y no se propone.
  - **Inventario de citas de la interfaz** y, para cada una, la cita correcta según la tabla. Es una lista para que las salas dueñas (frontend, regulación) la ejecuten en sus propias tareas; esta ficha **no** edita código.
  - Un apartado «No verificado» con todo lo que no se pudo leer o contrastar en fuente oficial.
- Si un texto no se pudo obtener de una fuente oficial, el documento lo dice al principio y no cita sus artículos.

## Límites
- No implementa plazos, pantallas ni código, y no edita el PRD ni `INVARIANTS.md`: los cambios que proponga los aplica el coordinador en el PR de gobernanza de la tanda (regla 9).
- No sustituye el dictamen del abogado sobre las plantillas; lo complementa con la verificación de los parámetros de la plataforma.
- No resume de memoria: toda cifra, plazo y artículo debe poder localizarse en el texto leído, como en LEG-02.

## Hecho cuando
- Su árbitro pasa y el propietario aprueba el documento. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
