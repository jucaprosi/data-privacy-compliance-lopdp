"use client";

// ¤adpa
// ¤¤frontend-architect
/**
 * Panel lateral derecho de Biblioteca (BIB-101): las mismas dos pestañas que el menú BIBLIOTECA y
 * «Abrir en pantalla completa», que lleva a la vista del menú. Se cierra con Escape o con su botón y
 * devuelve el foco a quien lo abrió.
 */
import React from "react";
import { createPortal } from "react-dom";
import { Maximize2, X } from "lucide-react";
import BibliotecaWorkspace from "@/components/biblioteca/BibliotecaWorkspace";
import { useAuditStore, type ActiveView } from "@/store/useAuditStore";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";

export const ID_PANEL_BIBLIOTECA = "panel-biblioteca";
/** Vista del menú BIBLIOTECA que registra `menus/BIB-101.ts`. */
export const VISTA_BIBLIOTECA = "biblioteca";

interface Props {
  /** Elemento al que vuelve el foco al cerrar. */
  origen: React.RefObject<HTMLElement | null>;
}

export default function PanelBiblioteca({ origen }: Props) {
  const abierto = useBibliotecaStore((s) => s.panelAbierto);
  const cerrarPanel = useBibliotecaStore((s) => s.cerrarPanel);
  const setActiveView = useAuditStore((s) => s.setActiveView);
  const panel = React.useRef<HTMLDivElement>(null);

  const cerrar = React.useCallback(() => {
    cerrarPanel();
    origen.current?.focus();
  }, [cerrarPanel, origen]);

  React.useEffect(() => {
    if (!abierto) return;
    panel.current?.focus();
    const alPulsar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") cerrar();
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, [abierto, cerrar]);

  function abrirPantallaCompleta() {
    // Mismo paso que hace el menú (dashboard/page.tsx): la vista del registro de FE-22 es una cadena
    // que `ActiveView` todavía no enumera.
    setActiveView(VISTA_BIBLIOTECA as unknown as ActiveView);
    cerrarPanel();
  }

  if (!abierto || typeof document === "undefined") return null;
  return createPortal(
    <div
      ref={panel}
      id={ID_PANEL_BIBLIOTECA}
      role="dialog"
      aria-label="Panel de Biblioteca"
      tabIndex={-1}
      className="fixed inset-y-0 right-0 z-50 flex w-[440px] max-w-full flex-col gap-3 border-l border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 shadow-2xl outline-none"
    >
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="text-sm font-semibold">Biblioteca</span>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={abrirPantallaCompleta}
            className="h-7 px-2 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] flex items-center gap-1 cursor-pointer"
          >
            <Maximize2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Abrir en pantalla completa</span>
          </button>
          <button
            type="button"
            onClick={cerrar}
            aria-label="Cerrar panel de Biblioteca"
            className="h-7 w-7 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] flex items-center justify-center cursor-pointer"
          >
            <X className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <BibliotecaWorkspace variante="panel" />
      </div>
    </div>,
    document.body,
  );
}
