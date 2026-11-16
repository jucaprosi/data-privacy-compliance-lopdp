# Corrección al diseño IA-10: SEC-22 y el filtro de log del copiloto

Arquitecto ADPA, 2026-11-12. Corrige `2026-11-12_DISENO_IA10_TRAZABILIDAD.md`, que ya está en `main` y no se edita.

- El diseño dice, en SEC-22, que `APILoggerFilter` «no protege». Es inexacto. El filtro sí tapa la f-string de la línea 38, pero deja pasar la clave cuando va como argumento de formato, cuando la registra un logger hijo o cuando viaja en una traza de excepción. Está medido en el Aporte 157.
- El `except` de la llamada al proveedor registra solo `type(e).__name__`, sin `{e}` y sin `exc_info`, igual que la compuerta de IA-03. No se redacta la clave dentro del mensaje, porque eso repite el error del filtro (decisión del Arquitecto a pedido del Tech Lead).
- La prueba de SEC-22 cubre las cuatro vías. Mutaciones: reponer la línea 38 sin el filtro; reponer el filtro y registrar la clave como argumento; volver a registrar `{e}` con un cliente falso que levanta `RuntimeError` con la clave. Las tres dan rojo.
- Todo esto ya está en la ficha SEC-22 y en BL-271 (PR #656).
