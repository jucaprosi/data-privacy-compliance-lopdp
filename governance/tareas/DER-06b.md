+++
id = "DER-06b"
titulo = "Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz"
ola = "backlog"
estado = "pendiente"
sala = "derechos_arco, frontend"
depende_de = ["DER-06a"]
propiedad = ["features/derechos_arco/domain/plazos.py", "tests/test_der06b_tipos_activos.py"]
crea = ["tests/test_der06b_tipos_activos.py"]
arbitro = "pytest tests/test_der06b_tipos_activos.py + Playwright de los formularios + node scripts de citas legales (verificar_citas_legales.py); mutaciones documentadas"
rastros = ["¤regulation-code", "¤arbitro"]
+++

# DER-06b · Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz

Diseño del Arquitecto ADPA (2026-11-09). Segunda mitad. Plazos por tipo de solicitud: 15 días (arts. 13 a 16: acceso, rectificación, eliminación, oposición) y 10 días (art. 62: portabilidad, suspensión, decisiones automatizadas y quejas), validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. Fuente: PR #557 y #558 de Aleczandra. La unidad (hábiles o corridos) sigue pendiente y la regla provisional son días corridos, marcada como estimada.

## Compuerta humana
**No se reparte** hasta que la revisión anterior de Cloud Run salga de servicio y el propietario lo confirme con un comando de solo lectura (el Arquitecto redacta un brief del propietario, como el de Vertex). Depende de DER-06a y de UX/UI.

## Entrega
- `TIPOS_ACTIVOS` en `plazos.py` pasa a incluir los tres tipos nuevos.
- Formularios y textos de la interfaz para suspensión, decisiones automatizadas y queja: los redacta UX/UI. **La propiedad de los archivos de frontend queda por fijar** entre UX/UI y el Arquitecto antes de repartir; DER-07 ya es dueña de `types/arco.ts`, `ArcoModule.tsx` y `CommandPalette.tsx`.
- La «queja» es una solicitud al responsable con el plazo de 10 días del art. 62. Si la interfaz avisa al titular de que puede acudir a la Autoridad (lo redacta UX/UI), va **sin plazo** y con cita solo si `CITAS_LEGALES_VERIFICADAS.md` la tiene como `verificado` (los arts. 63 y 64 no se han leído aquí). El árbitro de la interfaz lo cubre con el mismo script de citas de DER-07.

## Árbitros
- Con los tipos activos, crear cada uno de los tres da fila y plazo de 10 días. Mutación: dejar un tipo fuera de `TIPOS_ACTIVOS`.
- La interfaz no cita un plazo para la reclamación ante la Autoridad. Mutación: añadirlo.
