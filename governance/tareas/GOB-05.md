+++
id = "GOB-05"
titulo = "Adoptar el generador de índice del molde de ZERAG (claves de configuración, cabecera de imports, sugerencia de ruta y exenciones con caducidad) y retirar el mecanismo propio de exenciones"
ola = "indep"
estado = "hecha"
sala = "gobernanza"
depende_de = ["ADPA-10", "CI-35", "DEMO-03a"]
propiedad = ["scripts/generar_indice_tareas.py", "governance/tareas/_exenciones_propiedad.txt", "tests/test_generar_indice_tareas_arbol.py", "governance/tareas/GOB-05.md"]
crea = []
arbitro = "pytest tests/test_generar_indice_tareas_arbol.py tests/test_indice_tareas.py + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤arbitro"]
+++

# GOB-05 · Adoptar el generador de índice del molde de ZERAG

**Origen.** TICKETS 292, 293, 294 y 295 de ZERAG, cerrados en ZERAG (`801649b` y `847c820`, este último del TICKET-300). Esta ficha es la condición pendiente para cerrar el TICKET-294. Las exenciones de LOPDP son suyas y no del molde: el aviso «ya no tapa ningún error: retírela» salió 468 veces en 34 sesiones. ZERAG llevó el mecanismo al molde (`governance/molde/generar_indice_tareas.py`) y LOPDP lo adopta ahora. No se copia código de LOPDP hacia ZERAG.

**Medido el 2026-11-22 sobre `origin/main` (`f34d1dc1`):**
- `governance/tareas/_exenciones_propiedad.txt` tiene 0 exenciones activas, solo la cabecera. Medidas anteriores: 80 el 2026-11-13 y 43 el 2026-11-15.
- CI-35 está pendiente y posee `scripts/generar_indice_tareas.py`, `tests/test_indice_tareas.py` y `tests/test_generar_indice_tareas_arbol.py`. Por eso esta ficha depende de ella.

## Entrega
1. **Sustituir** el generador de LOPDP por el del molde de ZERAG, conservando lo que LOPDP añadió a su copia y el molde no tiene.
   - Antes de reemplazar, listar las diferencias con un `diff`.
   - Decidir cada diferencia: se mantiene en LOPDP o sube al molde como ticket de ZERAG. No se sobrescribe a ciegas.
2. **Propiedad por clave en archivos de configuración (TICKET-295).** Un `config.yml#cache` posee solo esa clave de primer nivel. Un archivo que no se puede analizar se posee entero.
3. **Cabecera de imports compartida (TICKET-292).** La cabecera (lo anterior a la primera marca de sección) no pertenece a ninguna ficha: los imports van ahí y las marcas después. Desaparecen los `# noqa: E402` que solo esquivan esa regla; los sobrantes los retira ruff (F401), no la propiedad.
4. **Sugerencia de ruta que respeta lo que otra tarea crea (TICKET-293).** `sugerir_ruta` mira primero lo que declaran las demás tareas abiertas (`crea`) y limita la búsqueda por nombre base a la misma sala.
5. **Exenciones con caducidad (TICKETS 294 y 300).** Se sustituyen `aplicar_exenciones` y `exenciones_nuevas` por las del molde.
   - En modo árbitro (`--arbitro` o `ZERAG_ARBITRO=1`) no escribe y falla nombrando la exención caducada.
   - En modo local, `--verificar` solo informa: lista las caducadas y dice qué línea retirar, sin escribir en el archivo.
   - La lista solo decrece. En modo árbitro, una exención que no está en la referencia publicada es un error. La referencia es `origin/main` o la que se pase con `--referencia`; si no resuelve, el modo árbitro falla.
   - La copia de LOPDP puede seguir creando exenciones con `--generar-exenciones` (COORDINACION C.13 de ZERAG).
6. **Pasar `ZERAG_ARBITRO=1`** donde LOPDP corra el generador como árbitro (su CI), con la referencia de la integración si `origin/main` no está disponible en el clon. Hay que medir cómo lo invoca: ZERAG no lo sabe.
7. **Exenciones actuales.** Si al empezar la tarea hay exenciones activas, se revisan contra el formato `ficha|entrada|motivo`: el generador nuevo trata una línea mal formada como error. Hoy son 0.

## Pruebas
- `tests/test_generar_indice_tareas_arbol.py` migra a las funciones del molde y suma cuatro casos:
  - Una exención vigente se conserva.
  - Una exención caducada se informa en local sin escribir en el archivo.
  - La misma exención falla en modo árbitro sin escribir, tanto por bandera como por variable de entorno.
  - Una exención nueva frente a la referencia falla en modo árbitro.
- Un archivo de configuración con dos fichas que tocan claves distintas no choca; con la misma clave, sí.
- Un archivo con dos secciones y los imports en la cabecera pasa `ruff check --select E402,F401,F821` sin `noqa`.

## Hecho si
- El generador de LOPDP nombra las exenciones caducadas con la línea que hay que retirar, y la lista no crece frente a la referencia publicada.
- `python scripts/generar_indice_tareas.py --verificar` sale 0 sobre el árbol real de LOPDP.
- No queda en LOPDP código propio de exenciones que el molde ya tenga.

## No demostrado
- Que la copia de LOPDP no tenga cambios propios que el molde no conozca. Se mide con el `diff` del punto 1.
- Que el CI de LOPDP pueda recibir `ZERAG_ARBITRO=1` sin tocar más de lo previsto.
- Cuántos `# noqa: E402` de LOPDP se pueden retirar de verdad. Ruff dirá cuáles sobran después del cambio, y el recuento se hace entonces.

## Fuera de esta tarea
- **La comprobación de huellas por carácter** (`scripts/verificar_bom_huellas.py` y `verificadores/arnes_cero_regresiones.py:65`). Su sustitución depende del TICKET-289 de ZERAG, que sigue abierto: hasta que exista la definición canónica de huella abierta, no hay con qué sustituirla. Se abrirá como otra ficha cuando el 289 esté cerrado.
