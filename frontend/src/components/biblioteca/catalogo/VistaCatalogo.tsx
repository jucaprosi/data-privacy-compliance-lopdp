"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Pestaña «Plantillas» (BIB-102). Se registra en `pestana:plantillas` desde su sección de
 * `vistas/index.ts`. Filtra por fuente, tipo y ola; al elegir una plantilla la fija en
 * `useSeleccionBiblioteca` (la ficha la pinta BIB-103). No hay botón de descarga: la descarga es de
 * BIB-104 y solo para versiones publicadas con archivo; aquí una entrada que no está publicada se
 * rotula como tal y no ofrece ninguna acción.
 */
import React from "react";
import { LibraryBig, RefreshCw } from "lucide-react";
import {
  FUENTES, OLAS, SIN_FILTROS, TIPOS, consultarCatalogo, hayFiltros,
  type FiltrosCatalogo, type PlantillaCatalogo, type ResultadoCatalogo,
} from "@/lib/biblioteca/catalogo";
import { useSeleccionBiblioteca, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";

const nombreDe = (lista: ReadonlyArray<{ id: string; nombre: string }>, id: string | null) =>
  lista.find((x) => x.id === id)?.nombre ?? id ?? "—";

const ESTADOS: Record<string, string> = {
  publicada: "Publicada", en_revision: "En revisión", sustituida: "Sustituida", retirada: "Retirada",
};

function Tarjeta({ p, elegida, elegir }: { p: PlantillaCatalogo; elegida: boolean; elegir: () => void }) {
  return (
    <li data-testid={`plantilla-${p.codigo}`} className="rounded-md border border-[var(--ui-borde)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold">{p.nombre ?? p.codigo}</p>
          <p className="text-[var(--ui-texto-suave)]">
            {p.codigo} · {nombreDe(TIPOS, p.tipo)} · versión {p.version}{p.ola ? ` · ola ${p.ola}` : ""}
          </p>
        </div>
        <button
          type="button"
          aria-pressed={elegida}
          aria-label={`Elegir ${p.nombre ?? p.codigo}`}
          onClick={elegir}
          className={`rounded-md border border-[var(--ui-borde)] px-3 py-1 font-medium cursor-pointer ${
            elegida ? "bg-[var(--ui-campo)]" : "hover:bg-[var(--ui-boton-hover)]"
          }`}
        >
          {elegida ? "Elegida" : "Elegir"}
        </button>
      </div>
      <p className="mt-1 flex flex-wrap gap-x-3 text-[var(--ui-texto-suave)]">
        <span>{nombreDe(FUENTES, p.fuente)}</span>
        <span>{ESTADOS[p.estado] ?? p.estado}</span>
        <span>Validación legal: {p.validacion_legal ?? "sin dictamen registrado"}</span>
      </p>
    </li>
  );
}

export default function VistaCatalogo(_: PropsVistaBiblioteca) {
  const organizacion = useBibliotecaStore((s) => s.organizacion);
  const plantillaId = useSeleccionBiblioteca((s) => s.plantillaId);
  const elegirPlantilla = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const [filtros, setFiltros] = React.useState<FiltrosCatalogo>(SIN_FILTROS);
  const [resultado, setResultado] = React.useState<ResultadoCatalogo | null>(null);
  const [intento, setIntento] = React.useState(0);

  // Cada cambio de filtro, de organización o «Reintentar» consulta de nuevo; una respuesta tardía se descarta.
  React.useEffect(() => {
    let vigente = true;
    setResultado(null);
    consultarCatalogo(filtros).then((r) => { if (vigente) setResultado(r); });
    return () => { vigente = false; };
  }, [filtros, organizacion, intento]);

  const cambiar = (campo: keyof FiltrosCatalogo) => (e: React.ChangeEvent<HTMLSelectElement>) =>
    setFiltros((f) => ({ ...f, [campo]: e.target.value }));
  const estilo = "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1";

  return (
    <div data-testid="catalogo-plantillas" className="flex flex-col gap-3">
      <div role="group" aria-label="Filtros del catálogo" className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1">Fuente
          <select value={filtros.fuente} onChange={cambiar("fuente")} className={estilo}>
            <option value="">Todas</option>
            {FUENTES.map((f) => <option key={f.id} value={f.id}>{f.nombre}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">Tipo
          <select value={filtros.tipo} onChange={cambiar("tipo")} className={estilo}>
            <option value="">Todos</option>
            {TIPOS.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">Ola
          <select value={filtros.ola} onChange={cambiar("ola")} className={estilo}>
            <option value="">Todas</option>
            {OLAS.map((o) => <option key={o} value={String(o)}>{o}</option>)}
          </select>
        </label>
        <button type="button" disabled={!hayFiltros(filtros)} onClick={() => setFiltros(SIN_FILTROS)}
          className="rounded-md border border-[var(--ui-borde)] px-3 py-1 cursor-pointer disabled:cursor-default disabled:opacity-50">
          Limpiar filtros
        </button>
      </div>

      {resultado === null && <p role="status">Cargando plantillas…</p>}

      {resultado?.estado === "listo" && resultado.plantillas.length > 0 && (
        <ul aria-label="Plantillas" className="flex flex-col gap-2">
          {resultado.plantillas.map((p) => (
            <Tarjeta key={p.id} p={p} elegida={plantillaId === p.id}
              elegir={() => elegirPlantilla(plantillaId === p.id ? null : p.id)} />
          ))}
        </ul>
      )}

      {resultado?.estado === "listo" && resultado.plantillas.length === 0 && (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--ui-borde)] px-4 py-8 text-center">
          <LibraryBig className="h-6 w-6 text-[var(--ui-texto-suave)]" aria-hidden="true" />
          <p className="font-semibold">
            {hayFiltros(filtros) ? "Ninguna plantilla coincide con los filtros" : "Todavía no hay plantillas publicadas"}
          </p>
          {filtros.fuente === "organizacion" && (
            <p className="max-w-md text-[var(--ui-texto-suave)]">
              Las copias «Mi plantilla» aparecerán aquí cuando la organización cree la primera.
            </p>
          )}
        </div>
      )}

      {resultado && resultado.estado !== "listo" && (
        <div role="alert" data-testid={`catalogo-${resultado.estado}`}
          className="flex flex-wrap items-center gap-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300">
          <p>{resultado.mensaje}</p>
          {resultado.estado !== "denegado" && (
            <button type="button" onClick={() => setIntento((n) => n + 1)}
              className="inline-flex items-center gap-1 rounded-md border border-current px-2 py-1 cursor-pointer">
              <RefreshCw className="h-3 w-3" aria-hidden="true" /> Reintentar
            </button>
          )}
        </div>
      )}
    </div>
  );
}
