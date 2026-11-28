# DEMO-13 · La demo no arranca si le falta el clon de una sala
`¤sdd` `¤demo` `¤arbitro`

## 1. Datos

Sin tablas. `copiar_plantilla` (`features/demo/services/entrada_engine.py:50-63`) recorre `ORDEN_DE_SALAS` (`features/demo/domain/plantilla.py:22`: organización, diagnóstico, roadmap, biblioteca, evidencias y videovigilancia). Si una sala no registró `clonar_desde_plantilla`, la salta y solo lo anota en la auditoría como `salas_omitidas` (l. 117). Hoy las seis registran clon en `app_core/pasillo/`, pero un cambio que lo pierda deja al vendedor con una demo incompleta y sin aviso.

## 2. API

`POST /demo/entrar` responde **503 `DEMO_INCOMPLETA`** con la lista de salas sin clon, en vez de entrar.

## 3. Reglas

- **R1 · Todas o ninguna.** Antes de copiar, `copiar_plantilla` comprueba que cada sala de `ORDEN_DE_SALAS` tiene clon. Si falta alguna, lanza `DEMO_INCOMPLETA` (503) con sus nombres y no copia nada, porque la transacción no llega a abrirse.
- **R2 · Evento sin omitidas.** `DEMO_INICIADA` deja de llevar `salas_omitidas`.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-13`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin cambios: el frontend ya muestra los 503 de la demo (`frontend/tests/demo/demo.spec.ts:273`).

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el registro de clones sin `videovigilancia`, **entonces** `copiar_plantilla` lanza `DEMO_INCOMPLETA` nombrándola, y no se llamó a ningún clon. Mutación m1: volver a saltar la sala da rojo. | `tests/test_demo13_salas_completas.py` |
| **Dado** las seis salas con clon, **entonces** se copia en el orden de `ORDEN_DE_SALAS` y el evento no lleva `salas_omitidas`. Mutación m2: comprobar solo la primera sala da rojo con la falta de la última. | ídem |

## 6. Trazabilidad

- PRD §5.6. Análisis de brechas de la tanda 129: `governance/partes/arquitecto/2026-11-28_BRECHAS_PRD.md`.
