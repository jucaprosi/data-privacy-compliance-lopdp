+++
id = "ORG-24b"
titulo = "La ficha de la organización cuenta las vulneraciones abiertas, no solo las registradas"
ola = "backlog"
estado = "en_curso"
sala = "organizacion"
depende_de = ["ORG-24", "INC-03"]
propiedad = ["features/organizacion/services/ficha_engine.py", "api/routers/organizacion_ficha.py", "tests/test_org24_ficha_organizacion.py"]
arbitro = "pytest tests/test_org24_ficha_organizacion.py + tests/test_matriz_permisos.py contra PostgreSQL 16 local con lopdp_app (RLS); mutaciones"
rastros = ["¤rbac-tenant"]
+++

# ORG-24b · La ficha de la organización cuenta las vulneraciones abiertas

Diseño del Arquitecto ADPA (2026-11-12). Cuando INC-03 deje el estado del incidente, la ficha puede decir «abiertas» sin afirmar un dato falso.

## Entrega
- `ficha_engine.py` suma `vulneraciones_abiertas` con `pasillo_incidentes.contar_abiertos` (de INC-03), sin importar `features.incidentes` directo.
- **Transición del contrato:** la respuesta lleva **los dos campos** (`vulneraciones_registradas` y `vulneraciones_abiertas`) mientras FE-25 no lea el nuevo; el campo viejo se retira en una ficha posterior, no aquí. Así FE-25 no se rompe y el texto «abiertas» solo se muestra cuando exista el campo.
- Sin migración, sin archivo nuevo.

## Pruebas
- Con un incidente cerrado y otro abierto: `vulneraciones_registradas = 2` y `vulneraciones_abiertas = 1`. Mutación: contar todos como abiertos → rojo.
- Aislamiento por tenant (el de otra organización no cuenta). Mutación: quitar el contexto RLS → rojo.

## Límites
- No toca el frontend: el cambio de texto de FE-25 a «abiertas» va aparte, con UX/UI. No se mete en INC-03 (otra sala y otro contrato).
