+++
id = "LEG-02"
titulo = "Norma técnica de notificación de vulneraciones: lectura del texto vinculante"
ola = "D"
estado = "hecha"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/apoyo/NORMA_TECNICA_VULNERACIONES.md"]
arbitro = "el documento existe, cita cada dato con su artículo y fuente oficial, y separa lo verificado de lo no verificado; lo aprueba el propietario"
rastros = ["¤seguridad"]
+++

# LEG-02 · Norma técnica de notificación de vulneraciones: lectura del texto vinculante

**Objetivo.** La gobernanza de la plataforma se ha contrastado con la LOPDP (Registro Oficial 459), su Reglamento General (Decreto 904) y el Reglamento del Delegado (Resolución SPDP-SPD-2025-0028-R). Queda sin leer la **norma técnica de notificación de vulneraciones de seguridad** (referida como SPDP-SPD-2026-0040-R, número no verificado). Los plazos y la pantalla de notificación están aplazados por decisión del propietario; esta tarea solo deja **leído y resumido el texto vinculante**, para que cuando se retome no haya que empezar de cero ni se cite de memoria.

## Entrega
- `governance/apoyo/NORMA_TECNICA_VULNERACIONES.md` con:
  - Identificación oficial: título, número de resolución, fecha y Registro Oficial en que se publicó, y la URL oficial de donde se leyó (preferir `spdp.gob.ec` o el Registro Oficial; un resumen de un despacho no es fuente).
  - Qué regula y a quién obliga (responsable, encargado, delegado, Autoridad).
  - Definiciones, **plazos**, supuestos de notificación a la Autoridad y a los titulares, y contenido mínimo de la notificación, **cada uno con su artículo literal**.
  - Relación con el Art. 43 de la LOPDP y con el Reglamento General (qué agrega la norma técnica a cada uno).
  - Qué implicaría para la plataforma, **sin implementar nada**: datos que habría que registrar, roles que intervienen, eventos de auditoría. Solo una lista.
  - Un apartado «No verificado» con todo lo que no se pudo leer o contrastar.
- Si el texto no se pudo obtener de una fuente oficial, el documento lo dice en la primera línea y no cita artículos.

## Límites
- No implementa plazos, pantallas ni código: los plazos siguen aplazados.
- No edita la LOPDP ni otras normas copiadas en el repositorio.
- No resume de memoria: toda cifra y plazo debe poder localizarse en el texto leído.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
