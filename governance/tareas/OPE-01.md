+++
id = "OPE-01"
titulo = "Cada operador de la plataforma tiene su usuario, enlazado y sin organización"
ola = "D"
estado = "en_curso"
tanda = 112
sala = "plataforma"
depende_de = []
propiedad = ["alembic/versions/20261125_ope01_operador_usuario.py", "features/plataforma/administrar_operadores.py", "features/plataforma/services/operador_engine.py", "features/plataforma/plataforma_service.py", "app_core/pasillo/plataforma.py", "tests/test_ope01_operador_usuario.py"]
crea = ["alembic/versions/20261125_ope01_operador_usuario.py", "tests/test_ope01_operador_usuario.py"]
arbitro = "pytest tests/test_ope01_operador_usuario.py tests/test_alembic_cabeza_por_sala.py tests/test_adpa_bulkhead.py; mutaciones m1 a m4."
rastros = ["¤arbitro"]
+++

# OPE-01 · Cada operador de la plataforma tiene su usuario, enlazado y sin organización

**Contrato:** `governance/especificaciones/OPE-01.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_UXUI_BIBLIOTECA_OPERADORES` (2026-11-25) y parte de pantalla del UX/UI `UXUI_PARTE_PANTALLA_BIBLIOTECA_OPERADORES` (2026-11-25). El propietario decidió que el equipo editorial de la biblioteca (Aleczandra, José y Juan Carlos) trabaja como operadores de la plataforma, sin organización, «desde el código». El CTO aprobó el corte y la identidad: una fila en `users` por operador, enlazada por `operadores_plataforma.usuario_id`.

## Entrega
- Columna `operadores_plataforma.usuario_id`, en la rama de Alembic de plataforma.
- `alta` crea o recupera el usuario, y el subcomando nuevo `vincular` enlaza a los operadores ya activos.
- Pasillo: `operador_activo(usuario_id)`, `usuario_de_operador(identidad)` y `listar_operadores_activos()`.
- Los mismos pasos en la base de la demo.

## Límites
- No toca la nube ni las bases. `alta` y `vincular` en producción y en `evydentia_demo` los ejecuta el propietario por un brief.
- `users` se crea solo por `app_core/pasillo/organizacion.py` (`crear_o_recuperar_usuario`), sin tocar la sala organizacion.
- En `operador_engine.py` solo se añade la lectura del usuario enlazado; `verificar_operador` no cambia.
