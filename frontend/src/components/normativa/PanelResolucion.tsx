"use client";
/** Panel lateral de una norma: documento, historial de versiones y, para el operador, el registro de la revisión. */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  bajarOriginal, detalleResolucion, registrarRevision, ErrorNormativa,
  type DetalleResolucion, type EstadoRevision,
} from "./cliente";
import { ESTADO_RESOLUCION, fechaCorta, MENSAJES, OPCIONES_REVISION } from "./etiquetas";

export default function PanelResolucion({ id, operador, alCerrar, alRevisar }: {
  id: string; operador: boolean; alCerrar: () => void; alRevisar: () => void;
}) {
  const [d, setD] = useState<DetalleResolucion | null>(null);
  const [fallo, setFallo] = useState(false);
  const [enlace, setEnlace] = useState<string | null>(null);
  const [sinDocumento, setSinDocumento] = useState<string | null>(null);
  const [revisando, setRevisando] = useState(false);
  const [estado, setEstado] = useState<EstadoRevision>("vigente");
  const [nota, setNota] = useState("");
  const [errorNota, setErrorNota] = useState("");
  const titulo = useRef<HTMLHeadingElement>(null);
  const enlaceActual = useRef<string | null>(null);

  const cargarDocumento = useCallback(async () => {
    setSinDocumento(null);
    try {
      const url = URL.createObjectURL(await bajarOriginal(id));
      if (enlaceActual.current) URL.revokeObjectURL(enlaceActual.current);
      enlaceActual.current = url;
      setEnlace(url);
    } catch (e) {
      setEnlace(null);
      setSinDocumento(MENSAJES[(e as ErrorNormativa).codigo ?? ""] ?? "No pudimos cargar el documento.");
    }
  }, [id]);

  const cargarDetalle = useCallback(async () => {
    try { setD(await detalleResolucion(id)); setFallo(false); } catch { setFallo(true); }
  }, [id]);

  useEffect(() => {
    void cargarDetalle();
    void cargarDocumento();
    titulo.current?.focus();
    return () => { if (enlaceActual.current) URL.revokeObjectURL(enlaceActual.current); };
  }, [cargarDetalle, cargarDocumento]);

  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => { if (e.key === "Escape") alCerrar(); };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, [alCerrar]);

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (nota.trim().length < 10) { setErrorNota("Escribe una nota."); return; }
    try {
      await registrarRevision(id, estado, nota);
      setRevisando(false); setNota(""); setErrorNota("");
      await cargarDetalle();
      alRevisar();
    } catch (err) {
      setErrorNota(MENSAJES[(err as ErrorNormativa).codigo ?? ""] ?? "No pudimos guardar la revisión.");
    }
  };

  const nombre = d ? `${d.numero_resolucion}/${d.anio_emision}` : "Norma";
  return (
    <aside aria-labelledby="norm-panel-titulo" role="dialog" aria-modal="true"
      className="fixed inset-y-0 right-0 z-40 flex w-full flex-col gap-3 overflow-y-auto border-l border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 lg:w-1/2">
      <div className="flex items-start justify-between gap-2">
        <h3 id="norm-panel-titulo" ref={titulo} tabIndex={-1} className="text-base font-semibold">
          {d ? `${nombre} · ${d.organo_emisor ?? "SPDP"}` : "Cargando…"}
        </h3>
        <button type="button" onClick={alCerrar} className="rounded border border-[var(--ui-borde)] px-2 py-1 text-sm">Cerrar el panel</button>
      </div>
      {fallo ? <p role="alert" className="text-sm">No pudimos cargar la norma. Inténtalo de nuevo.</p> : null}
      {d ? (
        <>
          <p className="text-sm">{d.titulo}</p>
          <p className="text-sm">Estado: {ESTADO_RESOLUCION[d.estado].texto}
            {d.revisada_en ? ` · revisada el ${fechaCorta(d.revisada_en)}` : ""}</p>
          {d.nota_revision ? <p className="text-sm">Nota de la revisión: {d.nota_revision}</p> : null}
          {enlace ? (
            <>
              <iframe title={`Documento: ${nombre}`} src={enlace} className="h-[60vh] w-full rounded border border-[var(--ui-borde)]" />
              <a href={enlace} target="_blank" rel="noopener noreferrer" className="text-sm underline">Abrir el documento en otra pestaña</a>
            </>
          ) : sinDocumento ? <p role="alert" className="text-sm">{sinDocumento}</p> : <p role="status" className="text-sm">Cargando el documento…</p>}
          <div className="flex items-center gap-2 text-sm">
            <button type="button" onClick={() => void cargarDocumento()} className="rounded border border-[var(--ui-borde)] px-2 py-1">Volver a cargar el documento</button>
            <span>Si el documento no se ve, vuelve a cargarlo.</span>
          </div>
          <h4 className="text-sm font-medium">Historial de versiones</h4>
          {d.versiones.length === 0 ? <p className="text-sm">Sin versiones posteriores.</p> : (
            <ul className="text-sm">{d.versiones.map((v) => <li key={v.id}>{fechaCorta(v.detectada_en)} · {v.motivo.replace(/_/g, " ")}</li>)}</ul>
          )}
          {operador ? (
            revisando ? (
              <form onSubmit={guardar} className="flex flex-col gap-2 text-sm">
                <fieldset className="flex flex-col gap-1"><legend>Estado de la revisión</legend>
                  {OPCIONES_REVISION.map((o) => (
                    <label key={o.valor} className="flex items-center gap-2">
                      <input type="radio" name="estado-revision" checked={estado === o.valor} onChange={() => setEstado(o.valor)} />{o.texto}
                    </label>
                  ))}
                </fieldset>
                <label className="flex flex-col">Nota
                  <textarea value={nota} onChange={(e) => setNota(e.target.value)} aria-invalid={Boolean(errorNota)}
                    className="rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-2" />
                </label>
                {errorNota ? <p role="alert">{errorNota}</p> : null}
                <div className="flex gap-2">
                  <button type="button" onClick={() => { setRevisando(false); setErrorNota(""); }} className="rounded border border-[var(--ui-borde)] px-2 py-1">Cancelar</button>
                  <button type="submit" className="rounded border border-[var(--ui-borde)] px-2 py-1">Guardar revisión</button>
                </div>
              </form>
            ) : <button type="button" onClick={() => setRevisando(true)} className="self-start rounded border border-[var(--ui-borde)] px-2 py-1 text-sm">Registrar revisión</button>
          ) : null}
        </>
      ) : null}
    </aside>
  );
}
