// ¤adpa
// ¤¤developer-architect
"use client";
import { useState } from "react";
import type { Ficha, Version } from "@/lib/biblioteca/editorial";

export const camposFicha: [keyof Ficha, string][] = [
  ["nombre", "Nombre"], ["objetivo", "Objetivo"], ["fuentes", "Fuentes"],
  ["fecha_revision", "Fecha de revisión"], ["instrucciones", "Instrucciones"],
  ["dependencias", "Dependencias"], ["restricciones", "Restricciones"],
];
const vacia: Ficha = { nombre: "", objetivo: "", fuentes: "", fecha_revision: "",
  instrucciones: "", dependencias: "", restricciones: "" };

export function FichaEditorial({ version, ocupada, guardar }: {
  version: Version; ocupada: boolean; guardar: (ficha: Ficha) => Promise<void>;
}) {
  const [ficha, setFicha] = useState<Ficha>(version.ficha ?? vacia);
  return <form className="grid gap-3" onSubmit={e => { e.preventDefault(); void guardar(ficha); }}>
    <h3 className="font-semibold">Ficha editorial</h3>
    {camposFicha.map(([clave, etiqueta]) => <label key={clave} className="grid gap-1">{etiqueta}
      <input className="rounded border p-2" type={clave === "fecha_revision" ? "date" : "text"}
        required value={ficha[clave]} maxLength={clave === "nombre" ? 200 : clave === "instrucciones" ? 8000 : 4000}
        onChange={e => setFicha({ ...ficha, [clave]: e.target.value })} />
    </label>)}
    <p>Guardar cambios exige nuevas revisiones técnica y jurídica.</p>
    <button disabled={ocupada} className="rounded bg-purple-700 p-2 text-[var(--ui-primario-texto)]">Guardar ficha</button>
  </form>;
}
