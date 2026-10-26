+++
id = "RAT-04"
titulo = "Retirar el RAT paralelo guardado en un archivo JSON del frontend"
ola = "D"
estado = "hecha"
sala = "frontend"
depende_de = ["RAT-01", "MTGE-01"]
propiedad = ["frontend/src/app/actions/ratActions.ts", "frontend/data/rat_master.json", "tests/test_sin_rat_paralelo.py"]
arbitro = "pytest tests/test_sin_rat_paralelo.py + tsc --noEmit + suite Playwright completa; prueba de mutación documentada"
rastros = ["¤rat"]
+++

# RAT-04 · Un solo RAT

**Hallazgo (2026-10-24, revisión de MTGE-01).** Además del RAT de la base (RAT-01), existe otro en `frontend/data/rat_master.json`, gestionado por las acciones de servidor de `frontend/src/app/actions/ratActions.ts`:
- sin organización ni RLS;
- con su propio cálculo de gran escala de 100 puntos, contrario a la Res. SPDP-SPD-2026-0005-R.

Ninguna pantalla lo importa hoy (comprobado con búsqueda en `frontend/src`), pero sigue desplegado y cualquiera podría volver a usarlo.

## Entrega
- Eliminar `ratActions.ts` y `frontend/data/rat_master.json`, después de comprobar de nuevo que nada los usa.
- `tests/test_sin_rat_paralelo.py`: árbitro estático que falla si reaparece una acción de servidor o un archivo de datos del RAT fuera de la sala `rat` del backend (búsqueda de `rat_master` y de escrituras de archivo con «rat» en `frontend/src`).
- **Prueba de mutación documentada:** recrear un `rat_master.json` y comprobar que el árbitro falla.

## Límites
- No toca `incident_logs.json` ni `snapshots.json` ni sus acciones: si guardan datos de organizaciones fuera de la base, es otra tarea.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
