+++
id = "DER-06b"
titulo = "Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz"
ola = "backlog"
estado = "pendiente"
sala = "derechos_arco, frontend"
depende_de = ["DER-06a", "DER-07"]
propiedad = ["features/derechos_arco/domain/plazos.py", "frontend/src/components/modules/ArcoModule.tsx", "frontend/src/types/arco.ts", "tests/test_der06b_tipos_activos.py"]
crea = ["tests/test_der06b_tipos_activos.py"]
arbitro = "pytest tests/test_der06b_tipos_activos.py + Playwright de los formularios + node scripts de citas legales (verificar_citas_legales.py); mutaciones documentadas"
rastros = ["¤regulation-code", "¤arbitro"]
+++

# DER-06b · Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz

Diseño del Arquitecto ADPA (2026-11-09). Segunda mitad. Plazos por tipo de solicitud: 15 días (arts. 13 a 16: acceso, rectificación, eliminación, oposición) y 10 días (art. 62: portabilidad, suspensión, decisiones automatizadas y quejas), validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. Fuente: PR #557 y #558 de Aleczandra. La unidad (hábiles o corridos) sigue pendiente y la regla provisional son días corridos, marcada como estimada.

## Compuerta humana
**No se reparte** hasta que el propietario confirme, con los comandos de solo lectura de `governance/operaciones/BRIEF_PROPIETARIO_DER06B.md`, que la revisión que sirve y la revisión estable de la reversión (GCP-07) son posteriores al despliegue de DER-06a: la reversión por SLO devolvería a la revisión estable el 100 % del tráfico. Depende de DER-06a y de UX/UI.

## Entrega
- `TIPOS_ACTIVOS` en `plazos.py` pasa a incluir los tres tipos nuevos.
- Formularios y textos de la interfaz para suspensión, decisiones automatizadas y queja: los redacta UX/UI. Los formularios internos viven en `frontend/src/components/modules/ArcoModule.tsx` y `frontend/src/types/arco.ts`, que fueron de DER-07, y DER-06b va después de ella: añade los tres tipos al selector y a los tipos. El formulario público de `/solicitud/**` es de DER-02, que depende de esta ficha. UX/UI cierra los textos del selector y el aviso sobre la Autoridad antes de repartir.
- La «queja» es una solicitud al responsable con el plazo de 10 días del art. 62. Si la interfaz avisa al titular de que puede acudir a la Autoridad (lo redacta UX/UI), va **sin plazo** y con cita solo si `CITAS_LEGALES_VERIFICADAS.md` la tiene como `verificado` (los arts. 63 y 64 no se han leído aquí). El árbitro de la interfaz lo cubre con el mismo script de citas de DER-07.

## Árbitros
- Con los tipos activos, crear cada uno de los tres da fila y plazo de 10 días. Mutación: dejar un tipo fuera de `TIPOS_ACTIVOS`.
- La interfaz no cita un plazo para la reclamación ante la Autoridad. Mutación: añadirlo.
