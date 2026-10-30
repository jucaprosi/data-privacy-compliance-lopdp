"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Botón fijo «Biblioteca» del lado derecho de la barra superior (BIB-101), en todas las pantallas
 * del panel. Muestra el total de pendientes de la organización de la sesión y abre el panel lateral.
 * Sin la ruta de pendientes en el servidor (BIB-107) funciona igual, sin contador.
 */
import React from "react";
import { LibraryBig } from "lucide-react";
import PanelBiblioteca, { ID_PANEL_BIBLIOTECA } from "./PanelBiblioteca";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";

export default function BotonBiblioteca() {
  const abierto = useBibliotecaStore((s) => s.panelAbierto);
  const alternarPanel = useBibliotecaStore((s) => s.alternarPanel);
  const cargarPendientes = useBibliotecaStore((s) => s.cargarPendientes);
  const pendientes = useBibliotecaStore((s) => s.pendientes);
  const estado = useBibliotecaStore((s) => s.estadoPendientes);
  const boton = React.useRef<HTMLButtonElement>(null);

  // Al montar, y al abrir el panel: así el contador sigue a la organización de la sesión.
  React.useEffect(() => {
    void cargarPendientes();
  }, [cargarPendientes, abierto]);

  const total = estado === "listo" && pendientes ? pendientes.total : null;
  return (
    <>
      <button
        ref={boton}
        type="button"
        onClick={alternarPanel}
        aria-expanded={abierto}
        aria-controls={ID_PANEL_BIBLIOTECA}
        aria-label={total ? `Biblioteca, ${total} pendientes` : "Biblioteca"}
        data-testid="boton-biblioteca"
        className="h-7 px-2 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-[var(--ui-texto-suave)] hover:text-white flex items-center space-x-1 transition cursor-pointer"
      >
        <LibraryBig className="w-3.5 h-3.5 text-[#9a3bf1]" aria-hidden="true" />
        <span>Biblioteca</span>
        {total ? (
          <span
            data-testid="contador-biblioteca"
            className="min-w-[18px] rounded-full bg-[#9a3bf1] px-1.5 text-center font-mono text-[10px] font-semibold text-white"
          >
            {total > 99 ? "99+" : total}
          </span>
        ) : null}
      </button>
      <PanelBiblioteca origen={boton} />
    </>
  );
}
