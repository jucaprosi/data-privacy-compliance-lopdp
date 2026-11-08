/**
 * Estado compartido de la demo entre las dos ranuras del aviso (DEMO-04). ¤demo
 */
import { create } from "zustand";
import type { EstadoDemo, PersonaDemo } from "./contrato";
import { consultarEstado, entornoEsDemo } from "./cliente";
import { alVencerLaDemo, demoVencida } from "./estado";

interface StoreDemo {
  cargado: boolean;
  estado: EstadoDemo | null;
  vencida: boolean;
  iniciar: () => Promise<void>;
  refrescar: () => Promise<void>;
  adoptar: (persona: PersonaDemo) => void;
}

let iniciado = false;

export const useDemo = create<StoreDemo>((set, get) => ({
  cargado: false,
  estado: null,
  vencida: false,
  iniciar: async () => {
    if (iniciado) return;
    iniciado = true;
    alVencerLaDemo(() => set({ vencida: true }));
    if (!(await entornoEsDemo())) {
      set({ cargado: true });
      return;
    }
    await get().refrescar();
    set({ cargado: true, vencida: demoVencida() });
  },
  refrescar: async () => {
    const r = await consultarEstado();
    if (r.ok && r.valor.demo) set({ estado: r.valor });
  },
  adoptar: (persona) => {
    const estado = get().estado;
    if (estado) set({ estado: { ...estado, persona_activa: persona } });
  },
}));
