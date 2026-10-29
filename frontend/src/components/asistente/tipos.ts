// ¤asistente ¤frontend-ide
// Contrato del patrón único de asistente (FE-23). Fuente: governance/especificaciones/FE-23.md §1.
import type React from "react";

/** Un paso del asistente. Lo declara la sala dueña del flujo, no el componente. */
export interface PasoAsistente {
  id: string;
  titulo: string;
  opcional: boolean;
  /** null = válido; texto = motivo visible que impide avanzar. */
  validar: () => string | null;
  contenido: React.ReactNode;
}

export interface AsistenteProps {
  /** Entre 1 y 20 pasos. */
  pasos: PasoAsistente[];
  /** Persiste el paso al terminarlo. La provee la sala dueña de los datos; el asistente no llama a la API. */
  guardar: (pasoId: string) => Promise<void>;
  alTerminar: () => void;
  /** Índice del paso con el que se abre; por defecto 0. */
  pasoInicial?: number;
}

/** Cómo quedó un paso que ya se dejó atrás (R5). */
export type EstadoPaso = "completado" | "saltado";

export const MAX_PASOS = 20;
export const AVISO_ERROR_GUARDAR = "No se pudo guardar este paso. Intenta de nuevo.";
