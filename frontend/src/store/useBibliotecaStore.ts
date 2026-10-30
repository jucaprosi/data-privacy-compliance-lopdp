"use client";

// ¤adpa ¤rbac-tenant
// ¤¤developer-architect
/**
 * Estado de Biblioteca (BIB-101). Vive aparte de `useAuditStore`, que esta tarea no toca (decisión de
 * la propietaria, 2026-10-27). No se persiste: pestaña, panel y contador valen para la sesión y para
 * una sola organización.
 */
import { create } from "zustand";
import {
  consultarPendientes,
  organizacionDeLaSesion,
  type PestanaBiblioteca,
  type Pendientes,
} from "@/lib/biblioteca/contexto";

export type EstadoPendientes = "inicial" | "cargando" | "listo" | "no_disponible" | "denegado" | "error";

export interface BibliotecaState {
  pestana: PestanaBiblioteca;
  panelAbierto: boolean;
  /** Organización a la que pertenece lo cargado; al cambiar, se descarta todo. */
  organizacion: string;
  pendientes: Pendientes | null;
  estadoPendientes: EstadoPendientes;
  mensaje: string | null;

  elegirPestana: (pestana: PestanaBiblioteca) => void;
  abrirPanel: () => void;
  cerrarPanel: () => void;
  alternarPanel: () => void;
  /** Descarta lo cargado si la organización de la sesión cambió. Devuelve si hubo cambio. */
  sincronizarOrganizacion: () => boolean;
  cargarPendientes: () => Promise<void>;
}

const VACIO = { pendientes: null, estadoPendientes: "inicial" as EstadoPendientes, mensaje: null };

export const useBibliotecaStore = create<BibliotecaState>()((set, get) => ({
  pestana: "documentos",
  panelAbierto: false,
  organizacion: "",
  ...VACIO,

  elegirPestana: (pestana) => set({ pestana }),
  abrirPanel: () => set({ panelAbierto: true }),
  cerrarPanel: () => set({ panelAbierto: false }),
  alternarPanel: () => set((s) => ({ panelAbierto: !s.panelAbierto })),

  sincronizarOrganizacion: () => {
    const actual = organizacionDeLaSesion();
    if (actual === get().organizacion) return false;
    set({ organizacion: actual, pestana: "documentos", ...VACIO });
    return true;
  },

  cargarPendientes: async () => {
    get().sincronizarOrganizacion();
    const organizacion = get().organizacion;
    if (!organizacion) {
      set({ ...VACIO });
      return;
    }
    set({ estadoPendientes: "cargando", mensaje: null });
    const resultado = await consultarPendientes();
    // Una respuesta de otra organización (cambiada mientras se esperaba) no se aplica.
    if (get().organizacion !== organizacion) return;
    switch (resultado.estado) {
      case "listo":
        set({ pendientes: resultado.pendientes, estadoPendientes: "listo", mensaje: null });
        break;
      case "no_disponible":
        set({ pendientes: null, estadoPendientes: "no_disponible", mensaje: null });
        break;
      case "denegado":
      case "error":
        set({ pendientes: null, estadoPendientes: resultado.estado, mensaje: resultado.mensaje });
        break;
    }
  },
}));
