# Deuda técnica — Sesión de BD duplicada

**Fecha:** 2026-10-07
**Detectado por:** Fase 2.2 (Hoja de Ruta Inteligente)

## Problema

Existen DOS fuentes de sesión de base de datos con patrones distintos:

| Archivo | Inyección RLS | Usado por |
|---|---|---|
| `app_core/db/session.py` | `set_config()` (seguro) | `api/routers/roadmaps.py` |
| `app_core/database.py` | `f-string` (SQL injection) | 7 módulos: ai_copilot, arco_router, terceros_router, derechos_arco, terceros, transferencias, models_base |

## Riesgos

1. Seguridad: database.py usa f-string interpolation → SQL injection potencial.
2. Mantenibilidad: cada módulo nuevo elige una fuente distinta.
3. Duplicación: dos async_session_factory y dos get_db_session en el mismo proyecto.

## Solución propuesta (Fase 2.3 o posterior)

1. Consolidar en app_core/db/session.py como única fuente.
2. Migrar los 7 módulos al patrón con set_config().
3. Eliminar app_core/database.py.
4. Añadir tests de regresión que verifiquen RLS en los 7 módulos migrados.

## Alcance estimado

- Migración: ~2-3 horas.
- Tests: ~1 hora.
- Riesgo: medio (7 módulos, pero bien acotados).
