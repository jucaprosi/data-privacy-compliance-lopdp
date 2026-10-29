"use client";
// ¤asistente ¤frontend-ide
// Lista de pasos con su progreso (FE-23, R5 y §4): el actual lleva aria-current="step".
import React from "react";
import type { EstadoPaso, PasoAsistente } from "./tipos";

interface ListaPasosProps {
  pasos: PasoAsistente[];
  actual: number;
  estados: Record<string, EstadoPaso>;
  /** true cuando el asistente terminó: ningún paso es el actual. */
  terminado: boolean;
}

const ETIQUETA_ESTADO: Record<EstadoPaso, string> = {
  completado: "Completado",
  saltado: "Saltado",
};

const CLASE_ESTADO: Record<EstadoPaso, string> = {
  completado: "badge-render-success",
  saltado: "badge-render-warning",
};

export default function ListaPasos({ pasos, actual, estados, terminado }: ListaPasosProps) {
  return (
    <ol className="flex flex-col gap-1" aria-label="Pasos del asistente">
      {pasos.map((paso, indice) => {
        const esActual = !terminado && indice === actual;
        const estado = estados[paso.id];
        return (
          <li
            key={paso.id}
            data-paso={paso.id}
            data-estado={esActual ? "actual" : (estado ?? "pendiente")}
            aria-current={esActual ? "step" : undefined}
            className={`flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm ${
              esActual
                ? "border-[var(--ui-primario)] bg-[var(--ui-superficie-2)] font-semibold"
                : "border-[var(--ui-borde)] bg-[var(--ui-superficie)] text-[var(--ui-texto-suave)]"
            }`}
          >
            <span>
              {indice + 1}. {paso.titulo}
              {paso.opcional ? <span className="ml-1 text-xs">(opcional)</span> : null}
            </span>
            {!esActual && estado ? (
              <span className={`rounded px-2 py-0.5 text-xs ${CLASE_ESTADO[estado]}`}>{ETIQUETA_ESTADO[estado]}</span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
