// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/** Textos de la pestaña «Impacto» (UX/UI NORM-03). Siempre con texto; el color solo refuerza. */
import type { EstadoImpacto, TipoElemento } from "./cliente";

export const TIPO_ELEMENTO: Record<TipoElemento, string> = {
  pregunta: "Pregunta del assessment",
  tratamiento: "Tratamiento del RAT",
  tarea: "Tarea del plan",
  plantilla: "Plantilla",
};

export const ESTADO_IMPACTO: Record<EstadoImpacto, { texto: string; clase: string }> = {
  propuesta: { texto: "Pendiente de decisión", clase: "badge-render-warning" },
  aceptada: { texto: "Aceptada", clase: "badge-render-success" },
  rechazada: { texto: "Rechazada", clase: "opacity-70" },
};

export const AVISO_IA = "Esta propuesta la generó una IA y requiere la revisión del delegado de protección de datos. "
  + "No cambia nada hasta que la acepte.";

export const MENSAJES: Record<string, string> = {
  NORMATIVA_IMPACTO_NOTA_OBLIGATORIA: "Escribe una nota de al menos 10 caracteres.",
  NORMATIVA_IMPACTO_YA_DECIDIDO: "Esta propuesta ya fue decidida.",
  NORMATIVA_IMPACTO_IA_NO_DISPONIBLE: "El análisis no está disponible por ahora. Inténtalo más tarde.",
  NORMATIVA_IMPACTO_SIN_TEXTO: "No pudimos leer el texto del documento.",
  NORMATIVA_ORIGINAL_NO_DISPONIBLE: "El documento no está disponible por ahora.",
  NORMATIVA_RESOLUCION_NO_ENCONTRADA: "La norma ya no está en el catálogo.",
};
