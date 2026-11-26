// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤cita-verificada
// ¤¤frontend-architect
"use client";
/**
 * BIB-408 · Diálogos de las propuestas de la IA: «Proponer cambio», «Aprobar y publicar», «Devolver con observaciones»
 * y «Descartar» (textos de la especificación §4). El foco inicial es «Cancelar» y Escape cierra. Sin ningún texto de límite de uso.
 */
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { CONFLICTO_PROPUESTA, aprobarYPublicar, descartarVersion, devolverVersion, proponerCambio, type Version } from "@/lib/biblioteca/editorial";

/** La persona puede dejar vacío «Qué quieres que revise»; el servidor pide un motivo, y este se omite al mostrar el origen. */
export const MOTIVO_GENERAL = "Revisión general de la plantilla.";

function Dialogo({ titulo, onCerrar, children }: { titulo: string; onCerrar: () => void; children: ReactNode }) {
  const cancelar = useRef<HTMLButtonElement>(null);
  const previo = useRef<Element | null>(null);
  useEffect(() => {
    previo.current = document.activeElement;
    cancelar.current?.focus();
    return () => { if (previo.current instanceof HTMLElement) previo.current.focus(); };
  }, []);
  // Escape cierra aunque el foco se haya perdido (p. ej. al desaparecer el botón que se acaba de pulsar).
  useEffect(() => {
    const cerrar = (e: KeyboardEvent) => { if (e.key === "Escape") onCerrar(); };
    document.addEventListener("keydown", cerrar);
    return () => document.removeEventListener("keydown", cerrar);
  }, [onCerrar]);
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4">
    <div role="dialog" aria-modal="true" aria-labelledby="titulo-dialogo-version"
      className="grid max-h-full w-full max-w-lg gap-3 overflow-y-auto rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5">
      <h2 id="titulo-dialogo-version" className="text-lg font-semibold">{titulo}</h2>
      {children}
      <button ref={cancelar} type="button" onClick={onCerrar} className="justify-self-start rounded border p-2">Cancelar</button>
    </div>
  </div>;
}

/** Diálogo de una acción con texto, un campo opcional o requerido y un resultado. */
function DialogoAccion({ titulo, texto, campo, confirmar, resultado, ejecutar, onCerrar, onHecho }: {
  titulo: string; texto: string; campo?: { etiqueta: string; obligatorio: boolean }; confirmar: string; resultado: string;
  ejecutar: (valor: string) => Promise<void>; onCerrar: () => void; onHecho: () => void;
}) {
  const [valor, setValor] = useState("");
  const [ocupada, setOcupada] = useState(false);
  const [error, setError] = useState("");
  const [hecho, setHecho] = useState(false);
  async function enviar(e: FormEvent) {
    e.preventDefault(); setOcupada(true); setError("");
    try { await ejecutar(valor.trim()); setHecho(true); onHecho(); }
    catch (err) { setError(err instanceof Error ? err.message : "No se pudo completar la operación."); }
    finally { setOcupada(false); }
  }
  return <Dialogo titulo={titulo} onCerrar={onCerrar}>
    <p>{texto}</p>
    {error && <p role="alert">{error}</p>}
    {hecho ? <p role="status">{resultado}</p> : <form className="grid gap-3" onSubmit={enviar}>
      {campo && <label className="grid gap-1">{campo.etiqueta}
        <textarea className="rounded border p-2" required={campo.obligatorio} value={valor} maxLength={4000}
          onChange={e => setValor(e.target.value)} /></label>}
      <button disabled={ocupada || (!!campo?.obligatorio && !valor.trim())} className="justify-self-start rounded bg-[var(--ui-primario)] p-2 text-[var(--ui-primario-texto)]">{confirmar}</button>
    </form>}
  </Dialogo>;
}

export function DialogoAprobar({ version, publicadaN, onCerrar, onHecho }: {
  version: Version; publicadaN: string | null; onCerrar: () => void; onHecho: () => void;
}) {
  const sustituye = publicadaN ? ` y sustituirá a la versión ${publicadaN} publicada` : "";
  return <DialogoAccion titulo="Aprobar y publicar esta versión" confirmar="Aprobar y publicar" resultado="Versión publicada."
    texto={`Se publicará en el catálogo${sustituye}. Quedará registrado que la aprobaste.`}
    ejecutar={async () => { await aprobarYPublicar(version, "Aprobada y publicada por la persona que la revisó."); }}
    onCerrar={onCerrar} onHecho={onHecho} />;
}

export function DialogoDevolver({ version, onCerrar, onHecho }: { version: Version; onCerrar: () => void; onHecho: () => void }) {
  return <DialogoAccion titulo="Devolver con observaciones" confirmar="Devolver con observaciones" resultado="Versión devuelta."
    campo={{ etiqueta: "Observaciones", obligatorio: true }}
    texto="La versión vuelve con tus observaciones. Para corregirla, pide una propuesta nueva con «Proponer cambio»."
    ejecutar={async observaciones => { await devolverVersion(version, observaciones); }} onCerrar={onCerrar} onHecho={onHecho} />;
}

export function DialogoDescartar({ version, onCerrar, onHecho }: { version: Version; onCerrar: () => void; onHecho: () => void }) {
  return <DialogoAccion titulo="Descartar propuesta" confirmar="Descartar" resultado="Propuesta descartada."
    campo={{ etiqueta: "Motivo del descarte", obligatorio: true }}
    texto="Descartar es definitivo; la propuesta quedará en el historial."
    ejecutar={async motivo => { await descartarVersion(version, motivo); }} onCerrar={onCerrar} onHecho={onHecho} />;
}

export function DialogoProponer({ codigo, onCerrar, onHecho }: { codigo: string; onCerrar: () => void; onHecho: () => void }) {
  const [motivo, setMotivo] = useState("");
  const [fase, setFase] = useState<"nuevo" | "preparando" | "lista" | "sin_cambios" | "conflicto" | "error">("nuevo");
  async function enviar(e: FormEvent) {
    e.preventDefault(); setFase("preparando");
    try {
      const r = await proponerCambio(codigo, motivo.trim() || MOTIVO_GENERAL);
      setFase(r.resultado === "creada" ? "lista" : r.resultado === "sin_cambios" ? "sin_cambios" : "conflicto");
      if (r.resultado === "creada") onHecho();
    } catch { setFase("error"); }
  }
  return <Dialogo titulo="Pedir una propuesta a la IA" onCerrar={onCerrar}>
    <p>La IA redactará una versión nueva, con la cita de cada cambio, y quedará en revisión. Tu nombre quedará en su origen.</p>
    {fase === "preparando" && <p role="status">Preparando la propuesta…</p>}
    {fase === "lista" && <p role="status">Propuesta lista para revisar.</p>}
    {fase === "sin_cambios" && <p role="status">La IA no encontró cambios necesarios en esta plantilla.</p>}
    {fase === "conflicto" && <p role="alert">{CONFLICTO_PROPUESTA}</p>}
    {fase === "error" && <p role="alert">No pudimos preparar la propuesta. Inténtalo de nuevo más tarde.</p>}
    {(fase === "nuevo" || fase === "error" || fase === "preparando") && <form className="grid gap-3" onSubmit={enviar}>
      <label className="grid gap-1">Qué quieres que revise
        <textarea className="rounded border p-2" value={motivo} maxLength={4000} onChange={e => setMotivo(e.target.value)} /></label>
      <button disabled={fase === "preparando"} className="justify-self-start rounded bg-[var(--ui-primario)] p-2 text-[var(--ui-primario-texto)]">Pedir propuesta</button>
    </form>}
  </Dialogo>;
}
