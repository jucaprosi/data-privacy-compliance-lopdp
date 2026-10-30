"use client";

/** Conocimiento › Normativa Ecuador (REG-02): corpus versionado de `regulacion_rag`, por fuente y artículo. */
import React, { useEffect, useState } from "react";
import { Scale } from "lucide-react";
import { buscarNormativa, type ArticuloNormativa } from "@/lib/conocimiento";

const FUENTES = [
  { valor: "", nombre: "Todas las fuentes" },
  { valor: "LOPDP", nombre: "LOPDP" },
  { valor: "Reglamento", nombre: "Reglamento General a la LOPDP" },
];

export default function NormativaEcuadorView() {
  const [fuente, setFuente] = useState("");
  const [q, setQ] = useState("");
  const [articulos, setArticulos] = useState<ArticuloNormativa[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    setError(null);
    const demora = setTimeout(() => {
      buscarNormativa(fuente, q)
        .then((a) => vigente && setArticulos(a))
        .catch((e: unknown) => vigente && setError(e instanceof Error ? e.message : "No se pudo consultar la normativa."));
    }, 250);
    return () => {
      vigente = false;
      clearTimeout(demora);
    };
  }, [fuente, q]);

  return (
    <section className="space-y-6 text-[var(--ui-texto)]" aria-labelledby="titulo-normativa">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 id="titulo-normativa" className="text-xl font-bold flex items-center gap-2">
          <Scale className="w-5 h-5 text-[var(--ui-primario)]" aria-hidden="true" /> Normativa Ecuador
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Corpus versionado de la LOPDP y su Reglamento: resúmenes editoriales trazables, no transcripciones legales.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <select
          aria-label="Fuente"
          value={fuente}
          onChange={(e) => setFuente(e.target.value)}
          className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 text-sm"
        >
          {FUENTES.map((f) => (
            <option key={f.valor} value={f.valor}>
              {f.nombre}
            </option>
          ))}
        </select>
        <input
          type="search"
          aria-label="Buscar en la normativa"
          placeholder="Buscar: derechos, consentimiento…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 min-w-56 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 text-sm"
        />
      </div>
      {error && (
        <p role="alert" className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]">
          {error}
        </p>
      )}
      {articulos && articulos.length === 0 && !error && (
        <p className="text-sm text-[var(--ui-texto-suave)]">Sin fuente en el corpus para esa búsqueda.</p>
      )}
      <ul className="space-y-3" aria-label="Artículos del corpus">
        {(articulos ?? []).map((a) => (
          <li key={`${a.fuente}-${a.articulo}`} className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge-render-success rounded-md px-2 py-0.5 text-xs font-mono font-semibold">
                {a.articulo} {a.fuente}
              </span>
              <h3 className="text-sm font-semibold">{a.titulo}</h3>
            </div>
            <p className="text-sm leading-relaxed">{a.texto}</p>
            <p className="text-[11px] text-[var(--ui-texto-suave)]">Versión del corpus: {a.version}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
