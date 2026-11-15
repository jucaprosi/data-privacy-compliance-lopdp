+++
id = "OPS-02"
titulo = "Verificar el tiempo límite de generación en Cloud Run"
ola = "E"
estado = "hecha"
sala = "operaciones"
depende_de = ["RM-13", "OPS-01"]
propiedad = ["governance/tareas/OPS-02.md"]
arbitro = "una generación completa termina dentro del timeout de 300 s configurado en Cloud Run"
rastros = ["¤roadmap"]
+++

# OPS-02 · Verificar la generación en Cloud Run

**Objetivo.** Verificar la latencia y estabilidad de la generación completa en línea dentro del timeout de 300 s de Cloud Run.

## Entrega
- Medir una generación completa en producción y dejar el resultado por escrito; si se acerca al límite, abrir la evaluación de una cola.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
