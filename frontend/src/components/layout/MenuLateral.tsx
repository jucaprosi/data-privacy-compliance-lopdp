"use client";

// ¤¤frontend-architect
// ¤frontend-ide
// ¤navegacion-menus
/**
 * Navegación por los nueve menús (FE-22): la barra superior con los menús y el dock lateral con
 * los submenús del menú abierto. Solo presenta: qué menús y submenús son visibles lo decide
 * dashboard/page.tsx (R4); aquí no se llama a ninguna API.
 */
import React from "react";
import type { Menu, MenuId, Submenu } from "./menus";
import type { VistaActiva } from "./dashboardNavigation";

export const ID_DOCK_SUBMENUS = "dock-submenus";

interface BarraMenusProps {
  menus: readonly Menu[];
  /** Menú de la vista que está montada: lleva `aria-current="page"`. */
  menuDeLaVista: MenuId | null;
  /** Menú cuyos submenús muestra el dock. */
  menuAbierto: MenuId | null;
  onAbrir: (menu: MenuId) => void;
}

/** Barra superior: los menús visibles en el orden R1. */
export function BarraMenus({ menus, menuDeLaVista, menuAbierto, onAbrir }: BarraMenusProps) {
  if (menus.length === 0) return null;
  return (
    // Un <div role="navigation"> y no <nav>: globals.css fuerza el color de `.theme-dark nav button`
    // con !important (estilo de la cabecera) y aquí rompería el contraste de los menús.
    <div
      role="navigation"
      aria-label="Menús principales"
      className="shrink-0 flex items-center gap-0.5 overflow-x-auto rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-1.5 py-1"
    >
      {menus.map((menu) => {
        const actual = menu.id === menuDeLaVista;
        const abierto = menu.id === menuAbierto;
        return (
          <button
            key={menu.id}
            type="button"
            data-menu={menu.id}
            aria-current={actual ? "page" : undefined}
            aria-expanded={abierto}
            aria-controls={ID_DOCK_SUBMENUS}
            onClick={() => onAbrir(menu.id)}
            className={`shrink-0 rounded-md px-2.5 py-1 text-[11px] font-medium cursor-pointer border ${
              abierto
                ? "bg-[var(--ui-boton)] border-[var(--ui-borde)]"
                : "border-transparent text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
            } ${actual ? "underline underline-offset-4 decoration-2 decoration-[var(--ui-primario)]" : ""}`}
          >
            {menu.nombre}
          </button>
        );
      })}
    </div>
  );
}

interface MenuLateralProps {
  menu: Menu | null;
  /** Submenús visibles del menú abierto, ya en su orden. */
  submenus: readonly Submenu[];
  vistaActiva: VistaActiva;
  onSeleccionar: (vista: VistaActiva) => void;
}

/** Dock lateral: los submenús del menú abierto. */
export default function MenuLateral({ menu, submenus, vistaActiva, onSeleccionar }: MenuLateralProps) {
  if (!menu) return null;
  return (
    <div id={ID_DOCK_SUBMENUS} role="group" aria-label={`Submenús de ${menu.nombre}`} className="space-y-1">
      <div className="px-1 py-1 text-[10px] uppercase font-bold tracking-wider text-[var(--ui-texto-suave)] font-mono">
        {menu.nombre}
      </div>
      {submenus.map((s) => {
        const seleccionado = s.vista === vistaActiva;
        return (
          <button
            key={s.vista}
            type="button"
            data-vista={s.vista}
            aria-current={seleccionado ? "page" : undefined}
            onClick={() => onSeleccionar(s.vista)}
            className={`w-full text-left px-2.5 py-2 rounded-lg flex flex-col cursor-pointer border ${
              seleccionado
                ? "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] border-[var(--ui-primario)]"
                : "border-transparent hover:bg-[var(--ui-boton-hover)]"
            }`}
          >
            <span className="truncate text-[11px] font-medium">{s.nombre}</span>
            <span
              className={`truncate text-[10px] ${
                seleccionado ? "text-[var(--ui-primario-texto)]" : "text-[var(--ui-texto-suave)]"
              }`}
            >
              {s.subtitulo}
            </span>
          </button>
        );
      })}
    </div>
  );
}
