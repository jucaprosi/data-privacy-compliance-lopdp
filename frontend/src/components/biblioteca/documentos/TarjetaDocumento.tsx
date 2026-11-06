"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Tarjeta de un documento de la organización (BIB-113).
 * Muestra el nombre, código, revisión, fecha próxima de revisión y la obligatoria etiqueta de origen
 * (basado en plantilla, propio o subido) según el apartado c) del PMV.
 */
import React from "react";
import {
  ETIQUETAS_ESTADO,
  ETIQUETAS_ORIGEN,
  type DocumentoResumen,
} from "@/lib/biblioteca/documentos";

interface Props {
  documento: DocumentoResumen;
  elegido: boolean;
  elegir: () => void;
}

export default function TarjetaDocumento({ documento, elegido, elegir }: Props) {
  const etiquetaOrigen = ETIQUETAS_ORIGEN[documento.origen] ?? documento.origen;
  const etiquetaEstado = ETIQUETAS_ESTADO[documento.estado] ?? documento.estado;

  return (
    <li
      data-testid={`documento-${documento.codigo}`}
      className={`rounded-md border p-3 transition-colors ${
        elegido
          ? "border-blue-500/70 bg-blue-500/5 dark:bg-blue-900/10"
          : "border-[var(--ui-borde)] bg-[var(--ui-fondo)]"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <p className="font-semibold text-sm">{documento.nombre}</p>
          <p className="text-[var(--ui-texto-suave)] text-xs">
            {documento.codigo}
            {documento.plantilla_version ? ` · versión ${documento.plantilla_version}` : ""}
            {` · revisión ${documento.revision}`}
            {documento.editado ? " · (editado)" : ""}
          </p>
        </div>
        <button
          type="button"
          aria-pressed={elegido}
          aria-label={`Elegir ${documento.nombre ?? documento.codigo}`}
          onClick={elegir}
          className={`rounded-md border border-[var(--ui-borde)] px-3 py-1 font-medium cursor-pointer text-xs ${
            elegido
              ? "bg-[var(--ui-campo)] font-semibold shadow-sm"
              : "hover:bg-[var(--ui-boton-hover)]"
          }`}
        >
          {elegido ? "Elegido" : "Elegir"}
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
        <span
          data-testid="etiqueta-origen"
          className="rounded-full border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-0.5 font-medium"
        >
          {etiquetaOrigen}
        </span>
        <span
          data-testid="etiqueta-estado"
          className="rounded-full border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-0.5 text-[var(--ui-texto-suave)]"
        >
          {etiquetaEstado}
        </span>
        <span className="text-[var(--ui-texto-suave)] ml-auto text-[11px]">
          Próxima revisión: {documento.proxima_revision}
        </span>
      </div>
    </li>
  );
}
