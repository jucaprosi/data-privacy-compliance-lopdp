"use client";

/**
 * Plantilla única de los mensajes de la demo (DEMO-04): icono, título, una línea y una acción.
 * El código técnico solo va en `data-codigo`, nunca a la vista. ¤demo
 */
import type { ReactNode } from "react";
import { AlertCircle } from "lucide-react";
import type { CodigoErrorDemo } from "@/lib/demo/contrato";

interface Props {
  codigo: CodigoErrorDemo;
  titulo: string;
  texto?: string;
  extra?: string | null;
  accion?: ReactNode;
  completa?: boolean;
}

export default function PantallaDemoMensaje({ codigo, titulo, texto, extra, accion, completa }: Props) {
  const cuerpo = (
    <div
      role="alert"
      data-testid="demo-mensaje"
      data-codigo={codigo}
      className="flex w-full max-w-sm flex-col items-center gap-3 rounded-xl border border-red-200 bg-white p-6 text-center text-zinc-800"
    >
      <AlertCircle aria-hidden="true" className="h-6 w-6 text-red-600" />
      <h2 className="text-base font-semibold">{titulo}</h2>
      {texto && <p className="text-sm text-zinc-600">{texto}</p>}
      {extra && <p className="text-sm text-zinc-600">{extra}</p>}
      {accion}
    </div>
  );
  if (!completa) return cuerpo;
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-white/95 px-4" data-testid="demo-pantalla-completa">
      {cuerpo}
    </div>
  );
}
