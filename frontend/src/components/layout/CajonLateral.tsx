"use client";

// ¤¤frontend-architect
// ¤frontend-ide
/**
 * Cajón lateral superpuesto (FE-27): diálogo modal que atrapa el foco, se cierra con Escape o
 * tocando fuera, devuelve el foco a quien lo abrió y deja el resto de la página inerte.
 */
import React from "react";

interface CajonLateralProps {
  abierto: boolean;
  onCerrar: () => void;
  lado: "izquierdo" | "derecho";
  /** Nombre accesible del diálogo, p. ej. «Menú de navegación». */
  nombre: string;
  /** Nombre accesible del botón «Cerrar», p. ej. «Cerrar menú». */
  nombreCerrar: string;
  /** Clases de ancho del panel. */
  anchoClase: string;
  children: React.ReactNode;
}

const FOCALIZABLES =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Marca como inertes los hermanos de `nodo` y de sus ancestros; devuelve cómo deshacerlo. */
function aislar(nodo: HTMLElement): () => void {
  const marcados: HTMLElement[] = [];
  let actual: HTMLElement | null = nodo;
  while (actual && actual.parentElement) {
    const padre: HTMLElement = actual.parentElement;
    for (const hermano of Array.from(padre.children)) {
      if (hermano === actual || !(hermano instanceof HTMLElement) || hermano.hasAttribute("inert")) continue;
      hermano.setAttribute("inert", "");
      marcados.push(hermano);
    }
    actual = padre === document.body ? null : padre;
  }
  return () => marcados.forEach((el) => el.removeAttribute("inert"));
}

export default function CajonLateral({
  abierto,
  onCerrar,
  lado,
  nombre,
  nombreCerrar,
  anchoClase,
  children,
}: CajonLateralProps) {
  const dialogo = React.useRef<HTMLDivElement>(null);
  const alCerrar = React.useRef(onCerrar);
  alCerrar.current = onCerrar;

  React.useEffect(() => {
    if (!abierto || !dialogo.current) return;
    const el = dialogo.current;
    const disparador = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const deshacer = aislar(el);
    const desbordeOriginal = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    el.querySelector<HTMLElement>("[data-cajon-cerrar]")?.focus();
    return () => {
      deshacer();
      document.body.style.overflow = desbordeOriginal;
      disparador?.focus();
    };
  }, [abierto]);

  if (!abierto) return null;

  const alTeclear = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      alCerrar.current();
      return;
    }
    if (e.key !== "Tab" || !dialogo.current) return;
    const items = Array.from(dialogo.current.querySelectorAll<HTMLElement>(FOCALIZABLES));
    if (items.length === 0) {
      e.preventDefault();
      return;
    }
    const primero = items[0];
    const ultimo = items[items.length - 1];
    const activo = document.activeElement;
    if (e.shiftKey && (activo === primero || !dialogo.current.contains(activo))) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && (activo === ultimo || !dialogo.current.contains(activo))) {
      e.preventDefault();
      primero.focus();
    }
  };

  const izquierdo = lado === "izquierdo";
  return (
    <div className="fixed inset-0 z-50" data-cajon={lado}>
      <style>{`
        @keyframes cajon-entra-izq { from { transform: translateX(-100%); } to { transform: none; } }
        @keyframes cajon-entra-der { from { transform: translateX(100%); } to { transform: none; } }
        @media (prefers-reduced-motion: no-preference) {
          [data-cajon="izquierdo"] > [role="dialog"] { animation: cajon-entra-izq 160ms ease-out; }
          [data-cajon="derecho"] > [role="dialog"] { animation: cajon-entra-der 160ms ease-out; }
        }
      `}</style>
      <div className="absolute inset-0 bg-black/40" data-cajon-fondo onClick={() => onCerrar()} aria-hidden="true" />
      <div
        ref={dialogo}
        role="dialog"
        aria-modal="true"
        aria-label={nombre}
        onKeyDown={alTeclear}
        className={`absolute inset-y-0 ${izquierdo ? "left-0 border-r" : "right-0 border-l"} ${anchoClase} flex flex-col bg-white dark:bg-[var(--ui-superficie)] border-[var(--ui-borde)] shadow-xl`}
      >
        <div className="flex shrink-0 justify-end border-b border-[var(--ui-borde)] p-1.5">
          <button
            type="button"
            data-cajon-cerrar
            aria-label={nombreCerrar}
            onClick={() => onCerrar()}
            className="min-h-10 min-w-10 rounded-md border border-[var(--ui-borde)] px-3 text-xs font-medium cursor-pointer hover:bg-[var(--ui-boton-hover)]"
          >
            Cerrar
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto flex flex-col">{children}</div>
      </div>
    </div>
  );
}
