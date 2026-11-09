+++
id = "DER-05"
titulo = "Plazo por tipo de solicitud de derechos: tabla única, unidad estimada y campos de plazo en la respuesta"
ola = "backlog"
estado = "pendiente"
sala = "derechos_arco"
depende_de = ["DER-03"]
propiedad = ["features/derechos_arco/domain/plazos.py", "features/derechos_arco/derechos_arco_service.py", "api/routers/arco_router.py", "tests/test_der05_plazos.py"]
crea = ["features/derechos_arco/domain/plazos.py", "tests/test_der05_plazos.py"]
arbitro = "pytest tests/test_der05_plazos.py + suites existentes de derechos ARCO; mutaciones a, b y c"
rastros = ["¤regulation-code", "¤arbitro"]
+++

# DER-05 · Plazo por tipo de solicitud de derechos: tabla única, unidad estimada y campos de plazo en la respuesta

Diseño del Arquitecto ADPA (2026-11-09), sin migración. Plazos por tipo de solicitud: 15 días (arts. 13 a 16: acceso, rectificación, eliminación, oposición) y 10 días (art. 62: portabilidad, suspensión, decisiones automatizadas y quejas), validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. Fuente: PR #557 y #558 de Aleczandra. La unidad (hábiles o corridos) sigue pendiente y la regla provisional son días corridos, marcada como estimada.

## Medido
`PLAZO_DIAS = 15` en `derechos_arco_service.py:20`, usado en `crear_solicitud_arco` (l. 71). El enum `TipoSolicitud` solo tiene ACCESO, RECTIFICACION, CANCELACION, OPOSICION y PORTABILIDAD.

## Entrega
- `features/derechos_arco/domain/plazos.py`: tabla única `PLAZO_POR_TIPO` (15 días para ACCESO, RECTIFICACION, CANCELACION y OPOSICION; 10 para PORTABILIDAD), `UNIDAD = "corridos"`, `ESTIMADO = True` y `plazo_dias(tipo)`.
- `derechos_arco_service.py` entero (las secciones `#DER-01` y `#DER-02` las abren fichas posteriores, que dependen de esta): usa `plazo_dias(tipo)`; el literal 15 no aparece en el servicio.
- `api/routers/arco_router.py`: la respuesta añade `plazo_dias`, `plazo_unidad` y `plazo_estimado`, derivados del tipo. Los lee DER-07.
- **Filas ya creadas:** no se rehace `fecha_vencimiento`. Una portabilidad existente conserva sus 15 días.
- Los tipos que faltan (suspensión, decisiones automatizadas, queja) son de DER-06a y DER-06b.

## Dónde importa cada cosa
Dentro de `features/derechos_arco/**`, import directo. Nada de otras salas.

## Árbitros, cada uno con su mutación
- (a) El plazo de cada uno de los cinco tipos y vencimiento = creación + plazo. Mutación: PORTABILIDAD en 15.
- (b) El literal 15 no aparece en el servicio, solo en `plazos.py`. Mutación: volver a poner `PLAZO_DIAS = 15`.
- (c) La respuesta lleva los tres campos. Mutación: quitar `plazo_estimado`.
