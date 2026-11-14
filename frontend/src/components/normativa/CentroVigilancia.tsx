"use client";
/**
 * NORM-02: Centro de Vigilancia Normativa. Catálogo de resoluciones de la SPDP con filtros, panel con el
 * documento y el historial, y bitácora de búsquedas. El catálogo informa; no dictamina.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import Bitacora from "./Bitacora";
import PanelResolucion from "./PanelResolucion";
import {
  ErrorNormativa, esOperador, listarResoluciones, SIN_FILTROS,
  type Filtros, type Pagina, type Resolucion,
} from "./cliente";
import { ESTADO_RESOLUCION, fechaCorta } from "./etiquetas";

type PestanaId = "catalogo" | "bitacora";
const PESTANAS: { id: PestanaId; nombre: string }[] = [
  { id: "catalogo", nombre: "Catálogo" },
  { id: "bitacora", nombre: "Bitácora" },
];
const CAMPO = "rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-2 py-1 text-sm";

export function Etiqueta({ estado }: { estado: Resolucion["estado"] }) {
  const e = ESTADO_RESOLUCION[estado];
  return <span className={`inline-block rounded border border-[var(--ui-borde)] px-2 py-0.5 text-xs ${e.clase}`}>{e.texto}</span>;
}

export default function CentroVigilancia() {
  const [pestana, setPestana] = useState<PestanaId>("catalogo");
  const [filtros, setFiltros] = useState<Filtros>(SIN_FILTROS);
  const [aplicados, setAplicados] = useState<Filtros>(SIN_FILTROS);
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState<Pagina | null>(null);
  const [cargando, setCargando] = useState(true);
  const [fallo, setFallo] = useState(false);
  const [abierta, setAbierta] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const refsPestana = useRef<Record<string, HTMLButtonElement | null>>({});
  const operador = esOperador();

  const cargar = useCallback(async () => {
    setCargando(true);
    setFallo(false);
    try {
      setDatos(await listarResoluciones(aplicados, pagina));
    } catch (e) {
      if (!(e instanceof ErrorNormativa) || e.status !== 401) setFallo(true);
    } finally {
      setCargando(false);
    }
  }, [aplicados, pagina]);

  useEffect(() => { void cargar(); }, [cargar]);

  const hayFiltros = Object.values(aplicados).some((v) => v.trim());
  const cambiar = (campo: keyof Filtros) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFiltros({ ...filtros, [campo]: e.target.value });
  const limpiar = () => { setFiltros(SIN_FILTROS); setAplicados(SIN_FILTROS); setPagina(1); };

  const moverCon = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const i = PESTANAS.findIndex((p) => p.id === pestana);
    const sig = PESTANAS[(i + (e.key === "ArrowRight" ? 1 : PESTANAS.length - 1)) % PESTANAS.length].id;
    setPestana(sig);
    refsPestana.current[sig]?.focus();
  };

  const abrir = (id: string, el: HTMLElement) => { disparador.current = el; setAbierta(id); };
  const cerrar = useCallback(() => { setAbierta(null); disparador.current?.focus(); }, []);
  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / datos.por_pagina)) : 1;

  return (
    <section aria-label="Vigilancia normativa" className="flex flex-col gap-4 p-4">
      <h2 className="text-base font-semibold">Vigilancia normativa</h2>
      <div role="tablist" aria-label="Pestañas de Vigilancia normativa" onKeyDown={moverCon} className="flex gap-1 border-b border-[var(--ui-borde)]">
        {PESTANAS.map((p) => (
          <button key={p.id} ref={(el) => { refsPestana.current[p.id] = el; }} type="button" role="tab"
            id={`norm-tab-${p.id}`} aria-selected={pestana === p.id} aria-controls={`norm-panel-${p.id}`}
            tabIndex={pestana === p.id ? 0 : -1} onClick={() => setPestana(p.id)}
            className={`px-3 py-2 text-sm ${pestana === p.id ? "border-b-2 border-current font-medium" : "text-[var(--ui-texto-suave)]"}`}>
            {p.nombre}
          </button>
        ))}
      </div>

      {pestana === "bitacora" ? (
        <div role="tabpanel" id="norm-panel-bitacora" aria-labelledby="norm-tab-bitacora"><Bitacora operador={operador} /></div>
      ) : (
        <div role="tabpanel" id="norm-panel-catalogo" aria-labelledby="norm-tab-catalogo" className="flex flex-col gap-3">
          <form role="search" aria-label="Filtrar normas" className="grid grid-cols-1 gap-2 sm:grid-cols-3"
            onSubmit={(e) => { e.preventDefault(); setAplicados(filtros); setPagina(1); }}>
            <label className="flex flex-col text-xs">Número<input className={CAMPO} value={filtros.numero} onChange={cambiar("numero")} /></label>
            <label className="flex flex-col text-xs">Año<input className={CAMPO} inputMode="numeric" value={filtros.anio} onChange={cambiar("anio")} /></label>
            <label className="flex flex-col text-xs">Palabra<input className={CAMPO} value={filtros.q} onChange={cambiar("q")} /></label>
            <label className="flex flex-col text-xs">Órgano<input className={CAMPO} value={filtros.organo} onChange={cambiar("organo")} /></label>
            <label className="flex flex-col text-xs">Materia<input className={CAMPO} value={filtros.materia} onChange={cambiar("materia")} /></label>
            <label className="flex flex-col text-xs">Estado
              <select className={CAMPO} value={filtros.estado} onChange={cambiar("estado")}>
                <option value="">Todos</option>
                {Object.entries(ESTADO_RESOLUCION).map(([v, e]) => <option key={v} value={v}>{e.texto}</option>)}
              </select>
            </label>
            <div className="flex items-end gap-2">
              <button type="submit" className={CAMPO}>Filtrar</button>
              <button type="button" className={CAMPO} onClick={limpiar}>Limpiar filtros</button>
            </div>
          </form>
          <p role="status" className="text-sm text-[var(--ui-texto-suave)]">
            {cargando ? "Cargando el catálogo…" : datos ? `${datos.total} normas` : ""}
          </p>
          {fallo ? (
            <div role="alert" className="flex items-center gap-2 text-sm">
              No pudimos cargar el catálogo. Inténtalo de nuevo.
              <button type="button" className={CAMPO} onClick={() => void cargar()}>Volver a cargar</button>
            </div>
          ) : null}
          {!cargando && !fallo && datos && datos.items.length === 0 ? (
            <p className="text-sm">
              {hayFiltros ? "Ninguna norma coincide con los filtros." : "No hay normas en el catálogo todavía."}
              {hayFiltros ? <button type="button" className={`${CAMPO} ml-2`} onClick={limpiar}>Limpiar filtros</button> : null}
            </p>
          ) : null}
          {datos && datos.items.length > 0 ? (
            <>
              <table aria-label="Catálogo de normas" className="hidden w-full text-left text-sm md:table">
                <caption className="sr-only">Catálogo de normas</caption>
                <thead><tr className="border-b border-[var(--ui-borde)]">
                  <th scope="col" className="py-2">Número</th><th scope="col">Año</th><th scope="col">Título</th>
                  <th scope="col">Estado</th><th scope="col">Detectada</th>
                </tr></thead>
                <tbody>
                  {datos.items.map((r) => (
                    <tr key={r.id} className="border-b border-[var(--ui-borde)]">
                      <td className="py-2"><button type="button" className="underline" onClick={(e) => abrir(r.id, e.currentTarget)}>{r.numero_resolucion}</button></td>
                      <td>{r.anio_emision}</td><td>{r.titulo}</td><td><Etiqueta estado={r.estado} /></td><td>{fechaCorta(r.detectada_en)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <ul className="flex flex-col gap-2 md:hidden">
                {datos.items.map((r) => (
                  <li key={r.id} className="rounded border border-[var(--ui-borde)] p-3 text-sm">
                    <button type="button" className="font-medium underline" onClick={(e) => abrir(r.id, e.currentTarget)}>{r.numero_resolucion}</button>
                    <p>{r.titulo}</p>
                    <p className="mt-1 flex items-center gap-2"><span>{r.anio_emision}</span><Etiqueta estado={r.estado} /></p>
                  </li>
                ))}
              </ul>
              <div className="flex items-center gap-2 text-sm">
                <button type="button" className={CAMPO} disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>Anterior</button>
                <span>Página {pagina} de {totalPaginas}</span>
                <button type="button" className={CAMPO} disabled={pagina >= totalPaginas} onClick={() => setPagina(pagina + 1)}>Siguiente</button>
              </div>
            </>
          ) : null}
        </div>
      )}
      {abierta ? <PanelResolucion id={abierta} operador={operador} alCerrar={cerrar} alRevisar={() => void cargar()} /> : null}
    </section>
  );
}
