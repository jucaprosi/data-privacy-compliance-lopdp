"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Registro de vistas de Biblioteca (BIB-111). Mismo patrón que FE-22 (`menus/`, `pantallas/`): cada
 * tarea escribe solo su sección de `components/biblioteca/vistas/index.ts` y registra ahí su vista en
 * una ranura; `BibliotecaWorkspace.tsx` ya no se vuelve a editar.
 *
 * Una ranura es un lugar donde una tarea puede montar algo. Quien pinta la ranura (el workspace para
 * las dos pestañas, la vista de cada ficha para las demás) llama a `vistasDe(ranura)`; si no hay
 * ninguna, conserva su vacío. El contenido de cada ranura es de la ficha que lo registra.
 */
import React from "react";
import { create } from "zustand";

export const RANURAS = [
  "pestana:documentos",
  "pestana:plantillas",
  "plantilla:ficha",
  "plantilla:acciones",
  "documento:detalle",
  "documento:acciones",
  "documento:editor",
] as const;

export type RanuraBiblioteca = (typeof RANURAS)[number];

export interface PropsVistaBiblioteca {
  variante: "completa" | "panel";
}

export type VistaBiblioteca = React.ComponentType<PropsVistaBiblioteca>;

const registro = new Map<RanuraBiblioteca, VistaBiblioteca[]>();

/** Monta `componente` en `ranura`. Varias tareas pueden compartir ranura: salen en orden de registro. */
export function registrarVista(ranura: RanuraBiblioteca, componente: VistaBiblioteca): void {
  if (!RANURAS.includes(ranura)) throw new Error(`Ranura desconocida «${String(ranura)}» (BIB-111).`);
  const actuales = registro.get(ranura) ?? [];
  if (actuales.includes(componente)) return;
  registro.set(ranura, [...actuales, componente]);
}

/** Vistas registradas en `ranura`; vacío si ninguna tarea ha montado nada. */
export function vistasDe(ranura: RanuraBiblioteca): readonly VistaBiblioteca[] {
  return registro.get(ranura) ?? [];
}

/**
 * Lo único que una tarea necesita saber de otra: qué plantilla y qué documento están elegidos.
 * No se persiste y no sustituye a `useBibliotecaStore` (de BIB-101 y BIB-110).
 */
export interface SeleccionBiblioteca {
  plantillaId: string | null;
  documentoId: string | null;
  elegirPlantilla: (id: string | null) => void;
  elegirDocumento: (id: string | null) => void;
  limpiar: () => void;
}

export const useSeleccionBiblioteca = create<SeleccionBiblioteca>((set) => ({
  plantillaId: null,
  documentoId: null,
  elegirPlantilla: (plantillaId) => set({ plantillaId }),
  elegirDocumento: (documentoId) => set({ documentoId }),
  limpiar: () => set({ plantillaId: null, documentoId: null }),
}));

/**
 * Vistas de prueba que `registro.spec.ts` fija desde el navegador (`addInitScript`) para comprobar
 * que una vista registrada sustituye al vacío sin tocar `vistas/index.ts`. Solo existen fuera de
 * producción: en un build de producción `NODE_ENV` es una constante y este bloque se elimina.
 */
export interface VistaDePrueba {
  ranura: RanuraBiblioteca;
  texto: string;
}

declare global {
  interface Window {
    __LOPDP_VISTAS_BIBLIOTECA_PRUEBAS__?: VistaDePrueba[];
  }
}

if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  for (const { ranura, texto } of window.__LOPDP_VISTAS_BIBLIOTECA_PRUEBAS__ ?? []) {
    registrarVista(ranura, () => React.createElement("p", { "data-testid": `vista-prueba-${ranura}` }, texto));
  }
}
