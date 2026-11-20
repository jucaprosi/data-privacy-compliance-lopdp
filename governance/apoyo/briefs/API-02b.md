### API-02b · webhooks-firmados-con-techo  (tanda 1)

**Contexto.** Salas: `pasillo_central`, `frontend`. Depende de: nada abierto. Especificaciones: `governance/tareas/API-02b.md` y `governance/especificaciones/API-02b.md`.

**Objetivo** (en este orden):

1. `API-02b` — Webhooks firmados HMAC-SHA256 con techo del paquete

**Rastro ¤**:

- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/api02b_webhooks_suscripciones.py`
  - `app_core/integraciones/webhooks.py`
  - `app_core/integraciones/techos.py#API-02b`
  - `api/routers/integraciones_webhooks.py`
  - `tests/test_api02b_webhooks.py`
  - `tests/matriz/API-02b.py`
  - `frontend/src/components/integraciones/IntegracionesView.tsx#API-02b`
  - `frontend/src/components/integraciones/WebhooksPanel.tsx`
  - `frontend/src/lib/integraciones/webhooks.ts`
  - `frontend/tests/integraciones/webhooks.spec.ts`
  - `governance/operaciones/BRIEF_PROPIETARIO_SECRETO_WEBHOOKS.md`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/API-02b.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida. El secreto `WEBHOOKS_CLAVE_CIFRADO` lo crea el propietario con su brief.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `API-02b`: pytest tests/test_api02b_webhooks.py + test_matriz_permisos.py + Playwright frontend/tests/integraciones/webhooks.spec.ts + tsc --noEmit + build; mutaciones m1 a m5
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
