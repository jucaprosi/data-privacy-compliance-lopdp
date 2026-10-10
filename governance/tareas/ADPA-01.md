+++
id = "ADPA-01"
titulo = "Compuertas de las salas Derechos ARCO, Terceros y Transferencias"
ola = "C"
estado = "pendiente"
sala = "derechos_arco, terceros, transferencias"
depende_de = ["RM-02"]
propiedad = ["features/derechos_arco/**", "features/terceros/**", "features/transferencias/**", "api/routers/arco_router.py", "api/routers/terceros_router.py", "tests/test_compuertas_arco_terceros_transferencias.py"]
arbitro = "pytest tests/test_compuertas_arco_terceros_transferencias.py tests/test_adpa_bulkheads.py + suite completa"
rastros = ["¤adpa", "¤derechos", "¤transferencias"]
+++

# ADPA-01 · Compuertas de las salas Derechos ARCO, Terceros y Transferencias

**Objetivo.** Las tres salas existen como carpeta pero no tienen compuerta: `derechos_arco` y `terceros` solo contienen sus modelos de dominio y `transferencias` no contiene código. Hoy sus routers llegan a los modelos sin pasar por una interfaz pública, lo que rompe ADPA (`ImportsCruzados = ∅`). Dar a cada sala su compuerta `<sala>_service.py`, con la lógica de servicio dentro de la sala y los routers importando solo la compuerta.

## Entrega
- `features/derechos_arco/derechos_arco_service.py`, `features/terceros/terceros_service.py` y `features/transferencias/transferencias_service.py`, con la superficie pública mínima que hoy usan sus routers.
- Los routers `arco_router.py` y `terceros_router.py` importan únicamente la compuerta de su sala.
- Una prueba por sala que falla si un router importa algo de `features/<sala>/` distinto de la compuerta.

## Límites
- No cambia el comportamiento observable de la API ni el esquema de datos.
- No crea las salas `incidentes` y `conservacion`, que siguen planificadas en el PRD (apartado 7.1).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
