+++
id = "OPS-02"
titulo = "Verificar la generación en el entorno gratuito"
ola = "E"
estado = "pendiente"
sala = "operaciones"
depende_de = ["RM-13", "OPS-01"]
propiedad = ["governance/operaciones/VERIFICACION_GENERACION.md"]
arbitro = "una generación completa termina dentro de 300 s en Vercel"
rastros = ["¤roadmap"]
+++

# OPS-02 · Verificar la generación en el entorno gratuito

**Objetivo.** Comprobar de verdad que la decisión D-1 funciona en el plan Hobby.

## Entrega
- Medir una generación completa en producción y dejar el resultado por escrito; si se acerca al límite, abrir la evaluación de una cola.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
