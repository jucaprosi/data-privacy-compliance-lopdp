"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { respuestaVerificable, sanearCopiloto } from "@/lib/copilotClient";
import type { TurnoCopiloto } from "@/types/copilot";

interface SesionCopiloto {
  turnos: TurnoCopiloto[];
}
interface CopilotStore {
  sesiones: Record<string, SesionCopiloto>;
  agregar: (scope: string, turno: TurnoCopiloto) => void;
  limpiar: (scope: string) => void;
}
export const SESION_VACIA: SesionCopiloto = { turnos: [] };

export const useCopilotStore = create<CopilotStore>()(persist((set) => ({
  sesiones: {},
  agregar: (scope, turno) => set((s) => {
    const actual = s.sesiones[scope] ?? SESION_VACIA;
    return { sesiones: { ...s.sesiones, [scope]: {
      ...actual, turnos: [...actual.turnos, sanearCopiloto(turno)].slice(-30),
    } } };
  }),
  limpiar: (scope) => set((s) => ({
    sesiones: Object.fromEntries(Object.entries(s.sesiones).filter(([key]) => key !== scope)),
  })),
}), {
  name: "lopdp-copilot-v1",
  storage: createJSONStorage(() => localStorage),
  partialize: (s) => ({
    sesiones: Object.fromEntries(Object.entries(s.sesiones).filter(([key]) => key.startsWith("project:"))),
  }),
  merge: (persistido, actual) => {
    const sesiones = (persistido as Partial<CopilotStore>)?.sesiones ?? {};
    const limpias: Record<string, SesionCopiloto> = {};
    for (const [key, session] of Object.entries(sesiones)) {
      if (!key.startsWith("project:") || !session || !Array.isArray(session.turnos)) continue;
      limpias[key] = {
        turnos: sanearCopiloto(session.turnos.filter((t) => t && typeof t.pregunta === "string" &&
          respuestaVerificable(t.respuesta)).slice(-30)),
      };
    }
    return { ...actual, sesiones: limpias };
  },
}));
