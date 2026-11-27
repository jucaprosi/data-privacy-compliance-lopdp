+++
id = "GCP-04c"
titulo = "Cloud Armor con sensibilidad 1 en SQLi y XSS, sin exclusiones de firmas"
ola = "backlog"
estado = "hecha"
sala = "operaciones"
depende_de = []
propiedad = ["governance/operaciones/cloud_load_balancer.yaml", "tests/test_gcp04b_waf_y_registro.py", "tests/test_gcp04c_waf_sensibilidad.py"]
crea = ["tests/test_gcp04c_waf_sensibilidad.py"]
arbitro = "pytest tests/test_gcp04c_waf_sensibilidad.py tests/test_gcp04b_waf_y_registro.py; mutaciones m1 a m3."
rastros = ["¤seguridad", "¤arbitro"]
+++

# GCP-04c · Cloud Armor con sensibilidad 1 en SQLi y XSS

**Contrato:** `governance/especificaciones/GCP-04c.md` (manda sobre esta ficha).

**Origen.** Decisión del CTO (2026-11-27). La regla 1000 bloqueó con la firma 942200 el alta de organizaciones en producción. El propietario lo aplica en la nube con el brief `PROPIETARIO_WAF_SENSIBILIDAD_1.md`; esta ficha alinea el repositorio.

## Entrega
- Reglas 1000 y 1001 de `evydentia-waf` con sensibilidad 1, sin `opt_out_rule_ids`.
- Prueba nueva de las reglas del WAF.

## Límites
- En `governance/operaciones/cloud_load_balancer.yaml`, solo las expresiones de las reglas 1000 y 1001. La 2000, la regla por defecto y el registro no cambian.
- En `tests/test_gcp04b_waf_y_registro.py`, solo se quitan `test_regla_1000_excluye_solo_942421`, `test_regla_1001_sin_cambios` y `test_exclusiones_con_evidencia`, con sus constantes y ayudantes, que pasan a GCP-04c. `test_registro_en_todos_los_servicios` no cambia.
- No toca la nube: lo aplica el propietario con su brief.
