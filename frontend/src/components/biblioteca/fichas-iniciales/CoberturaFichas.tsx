"use client";
// ¤adpa ¤frontend-ide
/**
 * BIB-208: cobertura de las ocho fichas iniciales. Muestra para cada una cómo se captura (tabla o
 * asistente por secciones), sus campos con requisito y destino de salida, y si la plantilla aún necesita
 * migración. PLA-01 se presenta como instantánea del plan existente, no como captura.
 * Si la carga falla no se muestra nada (sin role="alert": la pestaña sigue usable).
 */
import React from "react";
import { listarFichasIniciales, type MapaFicha } from "./api";

const REQUISITO: Record<string, string> = { O: "Obligatorio", C: "Condicional", D: "Lo asigna el servidor" };

function DetalleFicha({ ficha }: { ficha: MapaFicha }) {
  const grupos = ficha.modo === "secciones" ? ficha.secciones : ["Registro"];
  return <div data-testid={`campos-${ficha.codigo}`} className="mt-2 flex flex-col gap-2">
    {grupos.map((grupo) => <section key={grupo} aria-label={`${ficha.codigo}: ${grupo}`}>
      <h5 className="font-semibold">{grupo}</h5>
      <ul className="list-disc pl-4">
        {ficha.campos.filter((c) => ficha.modo === "tabla" || c.seccion === grupo).map((c) =>
          <li key={c.clave}>
            {c.etiqueta} · {REQUISITO[c.requisito] ?? c.requisito}
            {c.columna ? ` · columna ${c.columna}` : ""}
            {c.valores.length > 0 ? ` · opciones: ${c.valores.join(", ")}` : ""}
          </li>)}
      </ul>
    </section>)}
    {ficha.colecciones.length > 0 && <p>Colecciones repetibles: {ficha.colecciones.join(", ")}</p>}
  </div>;
}

function TarjetaFicha({ ficha }: { ficha: MapaFicha }) {
  const [abierta, setAbierta] = React.useState(false);
  const captura = ficha.codigo === "PLA-01" ? "Instantánea del plan existente"
    : ficha.modo === "tabla" ? "Captura en tabla" : "Asistente por secciones";
  return <article data-testid={`ficha-inicial-${ficha.codigo}`} aria-label={ficha.codigo}
    className="rounded-md border border-[var(--ui-borde)] p-3 text-xs">
    <h4 className="font-semibold">{ficha.codigo} · {ficha.interfaz}</h4>
    <p>{captura} · {ficha.campos.length} campos · esquema {ficha.version_esquema}</p>
    {ficha.estado_generacion.includes("migration_required") &&
      <p>La plantilla maestra aún necesita migración y revisión antes de publicarse.</p>}
    <button type="button" aria-expanded={abierta} onClick={() => setAbierta(!abierta)}
      className="mt-2 rounded border border-[var(--ui-borde)] px-2 py-1">
      {abierta ? "Ocultar campos" : "Ver campos"}
    </button>
    {abierta && <DetalleFicha ficha={ficha} />}
  </article>;
}

export default function CoberturaFichas() {
  const [fichas, setFichas] = React.useState<MapaFicha[] | null>(null);
  React.useEffect(() => { listarFichasIniciales().then(setFichas).catch(() => setFichas(null)); }, []);
  if (!fichas) return null;
  return <section aria-label="Cobertura de fichas iniciales" className="flex flex-col gap-3">
    <h3 className="text-sm font-semibold">Cobertura de fichas iniciales</h3>
    <p className="text-xs">Mapas propuestos de captura y salida; requieren revisión editorial y jurídica.</p>
    {fichas.map((f) => <TarjetaFicha key={f.codigo} ficha={f} />)}
  </section>;
}
