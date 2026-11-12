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
// --- INICIO BIB-110 ---
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import { marcarFuenteSinGuardar, olvidarFuentesSinGuardar } from "@/store/audit/fuentesSinGuardar";

const PREFIJO_FUENTES = "biblioteca:";

/**
 * Una vista de Biblioteca con cambios sin guardar lo declara aquí. Mientras haya alguna, el aviso de
 * cambio de organización (FE-21, vía `useAuditStore.cambiosSinGuardar`) ofrece guardar o descartar.
 */
export function marcarCambiosBiblioteca(fuente: string, hay: boolean): void {
  marcarFuenteSinGuardar(PREFIJO_FUENTES + fuente, hay);
}

/** Descarta lo que pertenece a la organización anterior: selección, cambios pendientes, pestaña y contador. */
export function invalidarCacheBiblioteca(): void {
  useSeleccionBiblioteca.getState().limpiar();
  olvidarFuentesSinGuardar(PREFIJO_FUENTES);
  useBibliotecaStore.setState({ pestana: "documentos", pendientes: null, estadoPendientes: "inicial", mensaje: null });
}

let vigilando = false;
/** Al pasar de una organización a otra (no en la primera carga) se invalida todo. Una sola vez por pestaña. */
function vigilarCambioDeOrganizacion(): void {
  if (vigilando) return;
  vigilando = true;
  useBibliotecaStore.subscribe((estado, previo) => {
    if (previo.organizacion && estado.organizacion !== previo.organizacion) invalidarCacheBiblioteca();
  });
}

/**
 * Ganchos de `cambio-organizacion.spec.ts`: las pruebas ejercen el almacén sin recorrer cada vista. Solo
 * existen fuera de producción (en un build de producción `NODE_ENV` es una constante y se eliminan).
 */
declare global {
  interface Window {
    __LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__?: {
      almacen: typeof useBibliotecaStore;
      seleccion: typeof useSeleccionBiblioteca;
      marcarCambios: typeof marcarCambiosBiblioteca;
      cambiosSinGuardar: () => Promise<boolean>;
      escribirAuditoria: () => Promise<void>;
      fijarCambiosPropios: (valor: boolean) => Promise<void>;
    };
  }
}
queueMicrotask(() => {
  if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
    window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__ = {
      almacen: useBibliotecaStore,
      seleccion: useSeleccionBiblioteca,
      marcarCambios: marcarCambiosBiblioteca,
      cambiosSinGuardar: async () => (await import("@/store/useAuditStore")).useAuditStore.getState().cambiosSinGuardar,
      // Fuerza una escritura del estado persistido del diagnóstico, para comprobar qué se guarda.
      fijarCambiosPropios: async (valor) => {
        const { useAuditStore } = await import("@/store/useAuditStore");
        useAuditStore.setState({ cambiosSinGuardar: valor });
      },
      escribirAuditoria: async () => {
        const { useAuditStore } = await import("@/store/useAuditStore");
        useAuditStore.setState({ theme: useAuditStore.getState().theme });
      },
    };
  }
});
// --- FIN BIB-110 ---

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

  // --- INICIO BIB-110 ---
  // El almacén aún no existe mientras se define: la vigilancia se engancha al terminar el módulo.
  ...(queueMicrotask(vigilarCambioDeOrganizacion), {}),
  // --- FIN BIB-110 ---
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
