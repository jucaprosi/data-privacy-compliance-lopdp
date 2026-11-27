# OPE-02 · La plataforma expone en la base si alguien es operador activo
`¤sdd` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` 517be04f:
- `operadores_plataforma.usuario_id` y `activo` existen desde OPE-01 (`20261125_ope01_operador_usuario.py`).
- La cabeza de la rama plataforma es `20261125_ope01_operador_usuario`.

Migración `20261126_ope02_operador_activo_bd`, que cuelga de `20261125_ope01_operador_usuario`. Crea `plataforma_operador_activo(usuario_id varchar) RETURNS boolean`, plpgsql `STABLE SECURITY DEFINER SET search_path = pg_catalog, public`, del dueño de las tablas. Devuelve verdadero solo si existe una fila de `operadores_plataforma` con ese `usuario_id` y `activo`; con `NULL` devuelve falso. `REVOKE ALL ... FROM PUBLIC` y `EXECUTE` solo para `lopdp_app`.

## 2. API

Sin API ni pasillo Python: es el pasillo de la sala plataforma dentro de la base, para las funciones de otras salas (BIB-411).

## 3. Reglas

- **R1 · Misma verdad que el pasillo.** Da lo mismo que `operador_activo()` de OPE-01 R3, leído en cada llamada.
- **R2 · Lectura mínima.** Solo devuelve un booleano; no expone email, nombre ni otros operadores.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`OPE-02`).** Solo los archivos de la propiedad. Las pruebas no usan `import yaml`.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** un operador activo, uno dado de baja y un usuario que no es operador, **entonces** la función da verdadero, falso y falso, y con `NULL` da falso. Mutación m1: ignorar `activo` da rojo. | `tests/test_ope02_operador_activo_bd.py` |
| **Dado** `lopdp_app` sin privilegios sobre `operadores_plataforma`, **entonces** la función responde igual. Mutación m2: declararla `SECURITY INVOKER` da rojo. | ídem |
| **Dado** `PUBLIC`, **entonces** no tiene `EXECUTE`. Mutación m3: dejar `EXECUTE` a `PUBLIC` da rojo. | ídem |
| **Dado** el grafo, **entonces** plataforma tiene una sola cabeza, `20261126_ope02_operador_activo_bd`. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- Revisión de seguridad del CTO sobre BIB-411 (2026-11-26), base `origin/main` 517be04f.
