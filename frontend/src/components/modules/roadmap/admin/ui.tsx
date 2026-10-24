"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

import type { ErrorDescrito } from "./errores";

export const CAMPO =
  "w-full rounded-md bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-2.5 py-1.5 text-xs text-zinc-100 " +
  "placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#3892f3] disabled:opacity-60";

export const BOTON =
  "inline-flex items-center gap-1.5 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-2.5 py-1.5 text-xs " +
  "font-semibold text-zinc-100 hover:bg-[var(--ui-boton-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] " +
  "disabled:opacity-50 disabled:cursor-not-allowed";

export const BOTON_PRIMARIO =
  "inline-flex items-center gap-1.5 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-primario-texto)] " +
  "hover:bg-[var(--ui-primario-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] " +
  "disabled:opacity-50 disabled:cursor-not-allowed";

export const ETIQUETA = "block text-[11px] font-semibold text-zinc-300 mb-1";

export interface BloqueErrorProps {
  error: ErrorDescrito;
  testId?: string;
  /** Si se indica y el error pide configurar el tamaño, se ofrece el botón. */
  onIrAConfiguracion?: () => void;
}

export function BloqueError({ error, testId, onIrAConfiguracion }: BloqueErrorProps) {
  return (
    <div
      role="alert"
      data-testid={testId}
      className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs"
    >
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" aria-hidden="true" />
      <div className="space-y-1">
        <p>{error.mensaje}</p>
        {error.codigo && <p className="text-zinc-400">Código: {error.codigo}</p>}
        {error.accion && <p className="text-zinc-400">Acción requerida: {error.accion}</p>}
        {error.irAConfiguracion && onIrAConfiguracion && (
          <button type="button" className={BOTON} onClick={onIrAConfiguracion}>
            Ir a la configuración
          </button>
        )}
      </div>
    </div>
  );
}
