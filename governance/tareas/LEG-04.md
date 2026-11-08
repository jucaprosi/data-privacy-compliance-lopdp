+++
id = "LEG-04"
titulo = "Citas legales: cómputo de plazos y términos (COA y Reglamento General)"
ola = "indep"
estado = "hecha"
sala = "gobernanza"
depende_de = ["LEG-03"]
propiedad = ["governance/apoyo/CITAS_LEGALES_VERIFICADAS.md"]
arbitro = "python scripts/verificar_citas_legales.py + pytest tests/test_leg03_citas_legales.py + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤regulation-code"]
+++

# LEG-04 · Cómputo de plazos y términos

**Origen.** Pedido del propietario (2026-11-08), con textos cotejados por el CTO. LEG-03 está hecha, así que el agregado va en esta ficha corta.

## Entrega
- Sección «Cómputo de plazos y términos (2026-11-08)» en `CITAS_LEGALES_VERIFICADAS.md`: remisión de la LOPDP al COA, arts. 158 a 160 del COA, arts. 62 y 64 de la LOPDP, arts. 14 y 16 del Reglamento General, propuesta de parámetro (pendiente del abogado) y advertencias.
- No cambia la tabla de verificación ni el inventario; el parámetro lo aplica REG-01 cuando el propietario lo apruebe con el abogado.
