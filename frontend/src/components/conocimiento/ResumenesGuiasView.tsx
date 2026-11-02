"use client";

/**
 * Conocimiento › Resúmenes y guías (REG-02): resúmenes del corpus agrupados por fuente, cada uno con su cita.
 * Las guías del catálogo de Biblioteca se añadirán cuando el catálogo marque qué documentos son guía.
 */
import React, { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { buscarNormativa, etiquetaCita, type ArticuloNormativa } from "@/lib/conocimiento";

export default function ResumenesGuiasView() {
  const [articulos, setArticulos] = useState<ArticuloNormativa[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    buscarNormativa("", "")
      .then((a) => vigente && setArticulos(a))
      .catch((e: unknown) => vigente && setError(e instanceof Error ? e.message : "No se pudo consultar el corpus."));
    return () => {
      vigente = false;
    };
  }, []);

  const porFuente = new Map<string, ArticuloNormativa[]>();
  for (const a of articulos ?? []) porFuente.set(a.fuente, [...(porFuente.get(a.fuente) ?? []), a]);

  return (
    <section className="space-y-6 text-[var(--ui-texto)]" aria-labelledby="titulo-resumenes">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 id="titulo-resumenes" className="text-xl font-bold flex items-center gap-2">
          <FileText className="w-5 h-5 text-[var(--ui-primario)]" aria-hidden="true" /> Resúmenes y guías
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Resúmenes breves por fuente. Cada uno indica el artículo del que sale; consulta el texto oficial antes de decidir.
        </p>
      </div>
      {error && (
        <p role="alert" className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]">
          {error}
        </p>
      )}
      {[...porFuente.entries()].map(([fuente, lista]) => (
        <div key={fuente} className="space-y-2">
          <h3 className="text-sm font-semibold">{fuente}</h3>
          <ul className="grid gap-3 md:grid-cols-2" aria-label={`Resúmenes de ${fuente}`}>
            {lista.map((a) => (
              <li key={a.articulo} className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-1">
                <p className="text-sm font-semibold">{a.titulo}</p>
                <p className="text-xs leading-relaxed text-[var(--ui-texto-suave)]">{a.texto}</p>
                <p className="badge-render-success inline-block rounded-md px-2 py-0.5 text-[11px] font-mono font-semibold">{etiquetaCita(a)}</p>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <p className="text-xs text-[var(--ui-texto-suave)]">
        Guías del catálogo: sin documentos marcados como guía por ahora.
      </p>
    </section>
  );
}
