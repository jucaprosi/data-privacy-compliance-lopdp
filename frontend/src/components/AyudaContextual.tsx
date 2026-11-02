"use client";

/**
 * Ayuda contextual (REG-02): icono «?» que abre un panel con el texto del corpus y su cita.
 * Si el corpus no tiene fuente para el control o el artículo, lo dice: nunca muestra texto sin cita
 * (Doctrina 7, INV_LOPDP_AI_RAG_STRICT_CITATION).
 */
import React, { useEffect, useId, useState } from "react";
import { BookOpen, HelpCircle, X } from "lucide-react";
import { etiquetaCita, obtenerAyuda, type ResultadoAyuda } from "@/lib/conocimiento";

interface AyudaContextualProps {
  /** Control del catálogo (p. ej. «P12»); manda sobre `articulo`. */
  controlRef?: string;
  /** Artículo del corpus (p. ej. «Art. 7»). */
  articulo?: string;
  /** Nombre del campo, para el nombre accesible del botón. */
  etiqueta?: string;
}

type Estado = { fase: "cerrado" } | { fase: "cargando" } | { fase: "error"; mensaje: string } | { fase: "listo"; resultado: ResultadoAyuda };

export default function AyudaContextual({ controlRef, articulo, etiqueta }: AyudaContextualProps) {
  const [estado, setEstado] = useState<Estado>({ fase: "cerrado" });
  const idPanel = useId();

  useEffect(() => setEstado({ fase: "cerrado" }), [controlRef, articulo]);

  const abrir = async () => {
    if (estado.fase !== "cerrado") {
      setEstado({ fase: "cerrado" });
      return;
    }
    setEstado({ fase: "cargando" });
    try {
      setEstado({ fase: "listo", resultado: await obtenerAyuda({ controlRef, articulo }) });
    } catch (e) {
      setEstado({ fase: "error", mensaje: e instanceof Error ? e.message : "No se pudo consultar la ayuda." });
    }
  };

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={abrir}
        aria-expanded={estado.fase !== "cerrado"}
        aria-controls={idPanel}
        aria-label={etiqueta ? `Ayuda sobre ${etiqueta}` : "Ayuda: base legal"}
        className="rounded-full text-[var(--ui-texto-suave)] hover:text-[var(--ui-primario)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-primario)]"
      >
        <HelpCircle className="w-4 h-4" aria-hidden="true" />
      </button>
      {estado.fase !== "cerrado" && (
        <div
          id={idPanel}
          role="dialog"
          aria-label="Base legal"
          className="absolute left-0 top-6 z-30 w-80 max-w-[85vw] rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-3 text-xs text-[var(--ui-texto)] shadow-lg space-y-2"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-1 font-semibold">
              <BookOpen className="w-3.5 h-3.5 text-[var(--ui-primario)]" aria-hidden="true" /> Base legal
            </span>
            <button
              type="button"
              onClick={() => setEstado({ fase: "cerrado" })}
              aria-label="Cerrar ayuda"
              className="text-[var(--ui-texto-suave)] hover:text-[var(--ui-texto)]"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
          {estado.fase === "cargando" && <p className="text-[var(--ui-texto-suave)]">Consultando el corpus…</p>}
          {estado.fase === "error" && (
            <p role="alert" className="text-[var(--ui-peligro)]">
              {estado.mensaje}
            </p>
          )}
          {estado.fase === "listo" && estado.resultado.estado === "sin_fuente" && (
            <p className="text-[var(--ui-texto-suave)]">Sin fuente en el corpus.</p>
          )}
          {estado.fase === "listo" && estado.resultado.estado === "con_cita" && (
            <>
              <p className="leading-relaxed">{estado.resultado.ayuda.texto}</p>
              <p className="badge-render-success inline-block rounded-md px-2 py-0.5 font-mono font-semibold">
                {etiquetaCita(estado.resultado.ayuda.cita)}
              </p>
              <p className="text-[var(--ui-texto-suave)]">Versión del corpus: {estado.resultado.ayuda.cita.version}</p>
            </>
          )}
        </div>
      )}
    </span>
  );
}
