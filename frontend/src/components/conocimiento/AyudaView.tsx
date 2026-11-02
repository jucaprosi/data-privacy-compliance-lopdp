"use client";

/** Conocimiento › Ayuda (REG-02): cómo funciona el «?» de los formularios y consulta directa por control o artículo. */
import React, { useState } from "react";
import { LifeBuoy } from "lucide-react";
import AyudaContextual from "@/components/AyudaContextual";

export default function AyudaView() {
  const [control, setControl] = useState("P12");
  const [articulo, setArticulo] = useState("");

  return (
    <section className="space-y-6 text-[var(--ui-texto)]" aria-labelledby="titulo-ayuda">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 id="titulo-ayuda" className="text-xl font-bold flex items-center gap-2">
          <LifeBuoy className="w-5 h-5 text-[var(--ui-primario)]" aria-hidden="true" /> Ayuda
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          El icono «?» junto a un campo abre su base legal con el artículo y la versión del corpus. Si el corpus no tiene
          fuente, lo dice: no se muestra texto sin cita.
        </p>
      </div>
      <div className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-4">
        <div className="flex flex-wrap items-end gap-4">
          <label className="text-xs space-y-1">
            <span className="block text-[var(--ui-texto-suave)]">Control (p. ej. P12)</span>
            <input
              value={control}
              onChange={(e) => setControl(e.target.value)}
              className="w-36 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 text-sm"
            />
          </label>
          <span className="inline-flex items-center gap-2 text-sm">
            Base legal del control <AyudaContextual controlRef={control.trim()} etiqueta="el control" />
          </span>
        </div>
        <div className="flex flex-wrap items-end gap-4">
          <label className="text-xs space-y-1">
            <span className="block text-[var(--ui-texto-suave)]">Artículo (p. ej. Art. 7)</span>
            <input
              value={articulo}
              onChange={(e) => setArticulo(e.target.value)}
              className="w-36 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 text-sm"
            />
          </label>
          <span className="inline-flex items-center gap-2 text-sm">
            Texto del artículo <AyudaContextual articulo={articulo.trim()} etiqueta="el artículo" />
          </span>
        </div>
      </div>
    </section>
  );
}
