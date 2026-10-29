"use client";
// ¤asistente ¤frontend-ide
// Resumen final del asistente (FE-23): qué pasos se completaron y cuáles se saltaron.
import React from "react";
import type { EstadoPaso, PasoAsistente } from "./tipos";

interface ResumenAsistenteProps {
  pasos: PasoAsistente[];
  estados: Record<string, EstadoPaso>;
  /** El asistente enfoca este título al terminar. */
  ref?: React.Ref<HTMLHeadingElement>;
}

export default function ResumenAsistente({ pasos, estados, ref }: ResumenAsistenteProps) {
  const completados = pasos.filter((p) => estados[p.id] === "completado").length;
  const saltados = pasos.filter((p) => estados[p.id] === "saltado").length;
  return (
    <div className="flex flex-1 flex-col gap-3" role="status" data-testid="asistente-resumen">
      <h2 ref={ref} tabIndex={-1} className="text-lg font-semibold outline-none">
        Resumen
      </h2>
      <p className="text-sm text-[var(--ui-texto-suave)]">
        {completados} {completados === 1 ? "paso completado" : "pasos completados"}, {saltados}{" "}
        {saltados === 1 ? "saltado" : "saltados"}.
      </p>
      <ul className="flex flex-col gap-1 text-sm">
        {pasos.map((p) => (
          <li key={p.id} data-paso={p.id}>
            {p.titulo}: {estados[p.id] === "saltado" ? "saltado" : estados[p.id] === "completado" ? "completado" : "sin completar"}
          </li>
        ))}
      </ul>
    </div>
  );
}
