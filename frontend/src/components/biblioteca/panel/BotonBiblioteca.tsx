"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Botón fijo «Biblioteca» del lado derecho de la barra superior (BIB-101), en todas las pantallas
 * del panel. Muestra el total de pendientes de la organización de la sesión y abre el panel lateral.
 * Sin la ruta de pendientes en el servidor (BIB-107) funciona igual, sin contador.
 * Si el contador no se pudo cargar (denegado o error), muestra un aviso sin número (BIB-116); el
 * detalle sigue en el panel.
 */
import React from "react";
import { LibraryBig } from "lucide-react";
import PanelBiblioteca, { ID_PANEL_BIBLIOTECA } from "./PanelBiblioteca";
import { useBibliotecaStore, type EstadoPendientes } from "@/store/useBibliotecaStore";
import type { Pendientes } from "@/lib/biblioteca/contexto";

/** Lo que el botón muestra: contador, aviso o nada. */
interface Vista {
  total: number | null;
  aviso: boolean;
  mensaje: string | null;
}

const VISTA_VACIA: Vista = { total: null, aviso: false, mensaje: null };

/** Vista para un estado del almacén; `null` con `cargando`, que conserva la última mostrada. */
function vistaPara(estado: EstadoPendientes, pendientes: Pendientes | null, mensaje: string | null): Vista | null {
  switch (estado) {
    case "cargando":
      return null;
    case "listo":
      return { total: pendientes?.total || null, aviso: false, mensaje: null };
    case "denegado":
    case "error":
      return { total: null, aviso: true, mensaje };
    default:
      return VISTA_VACIA;
  }
}

const mismaVista = (a: Vista, b: Vista) => a.total === b.total && a.aviso === b.aviso && a.mensaje === b.mensaje;

export default function BotonBiblioteca() {
  const abierto = useBibliotecaStore((s) => s.panelAbierto);
  const alternarPanel = useBibliotecaStore((s) => s.alternarPanel);
  const cargarPendientes = useBibliotecaStore((s) => s.cargarPendientes);
  const pendientes = useBibliotecaStore((s) => s.pendientes);
  const estado = useBibliotecaStore((s) => s.estadoPendientes);
  const mensaje = useBibliotecaStore((s) => s.mensaje);
  const boton = React.useRef<HTMLButtonElement>(null);

  // Al montar, y al abrir el panel: así el contador sigue a la organización de la sesión.
  React.useEffect(() => {
    void cargarPendientes();
  }, [cargarPendientes, abierto]);

  // Mientras carga se conserva lo último mostrado, para que no parpadee al abrir el panel.
  const actual = vistaPara(estado, pendientes, mensaje);
  const [ultima, setUltima] = React.useState<Vista>(VISTA_VACIA);
  if (actual && !mismaVista(actual, ultima)) setUltima(actual);
  const { total, aviso, mensaje: motivo } = actual ?? ultima;

  const etiqueta = aviso
    ? "Biblioteca, no se pudo cargar el contador"
    : total
      ? `Biblioteca, ${total} pendientes`
      : "Biblioteca";
  return (
    <>
      <button
        ref={boton}
        type="button"
        onClick={alternarPanel}
        aria-expanded={abierto}
        aria-controls={ID_PANEL_BIBLIOTECA}
        aria-label={etiqueta}
        title={aviso && motivo ? motivo : undefined}
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
        {aviso ? (
          <span
            data-testid="aviso-biblioteca"
            aria-hidden="true"
            className="h-2 w-2 rounded-full bg-amber-400 ring-2 ring-amber-400/30"
          />
        ) : null}
      </button>
      <PanelBiblioteca origen={boton} />
    </>
  );
}
