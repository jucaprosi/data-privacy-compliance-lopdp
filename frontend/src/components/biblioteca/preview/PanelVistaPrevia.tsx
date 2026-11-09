"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Vista previa del archivo antes de emitirlo (BIB-206), en la ranura `documento:acciones`.
 *
 * - Muestra el contenido con la misma instantánea y estructura que el archivo, su estado y la revisión.
 * - «Emitir este archivo» solo procede si la vista previa sigue vigente; si el documento cambió, se
 *   descarta y se pide volver a previsualizar. Emitir no aprueba el documento.
 * - Los fallos se anuncian con `role="status"`, nunca con `role="alert"`.
 */
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import type { FormatoGeneracion, ModoGeneracion } from "@/lib/biblioteca/generacion";
import {
  emitirDesdeVista, previsualizar, VistaObsoleta, type BloqueVista, type VistaPrevia,
} from "@/lib/biblioteca/preview";

declare global {
  interface Window {
    __LOPDP_PREVIEW_PRUEBAS__?: { borradorId?: string };
  }
}

function Bloque({ b }: { b: BloqueVista }) {
  if (b.tipo === "titulo") return <p className="font-semibold" data-nivel={b.nivel}>{b.texto}</p>;
  if (b.tipo === "lista") return <p className="pl-3">• {b.texto}</p>;
  if (b.tipo === "cita") return <blockquote className="border-l-2 pl-2 italic">{b.texto}</blockquote>;
  if (b.tipo === "tabla") {
    const [cabecera, ...filas] = b.filas;
    return (
      <table className="w-full border-collapse">
        {cabecera && <thead><tr>{cabecera.map((c, i) => <th key={i} className="border px-1 text-left">{c}</th>)}</tr></thead>}
        <tbody>
          {filas.map((f, i) => <tr key={i}>{f.map((c, j) => <td key={j} className="border px-1">{c}</td>)}</tr>)}
        </tbody>
      </table>
    );
  }
  return <p className="whitespace-pre-wrap break-words">{b.texto}</p>;
}

export default function PanelVistaPrevia() {
  const seleccion = useSeleccionBiblioteca((s) => s.documentoId);
  const pruebas = typeof window !== "undefined" ? window.__LOPDP_PREVIEW_PRUEBAS__?.borradorId : undefined;
  const borradorId = seleccion || pruebas || null;
  const [modo, setModo] = React.useState<ModoGeneracion>("revision");
  const [formato, setFormato] = React.useState<FormatoGeneracion>("docx");
  const [vista, setVista] = React.useState<VistaPrevia | null>(null);
  const [mensaje, setMensaje] = React.useState("");
  const [ocupado, setOcupado] = React.useState(false);

  React.useEffect(() => { setVista(null); setMensaje(""); }, [borradorId, modo, formato]);

  if (!borradorId) return null;

  const ver = async () => {
    setOcupado(true);
    setMensaje("");
    try {
      setVista(await previsualizar(borradorId, modo, formato));
    } catch (e) {
      setVista(null);
      setMensaje(`Sin vista previa: ${e instanceof Error ? e.message : "error desconocido"}`);
    } finally {
      setOcupado(false);
    }
  };

  const emitir = async () => {
    if (!vista) return;
    setOcupado(true);
    try {
      const g = await emitirDesdeVista(vista);
      setMensaje(`Archivo emitido: ${g.nombre_archivo}. Descárguelo en «Generar Word y Excel».`);
    } catch (e) {
      if (e instanceof VistaObsoleta) setVista(null);
      setMensaje(`No se emitió el archivo: ${e instanceof Error ? e.message : "error desconocido"}`);
    } finally {
      setOcupado(false);
    }
  };

  return (
    <section aria-label="Vista previa" data-testid="vista-previa-documento"
      className="mt-3 space-y-2 border-t border-[var(--ui-borde)] pt-3 text-xs">
      <h4 className="font-semibold">Vista previa</h4>
      <p className="text-[var(--ui-texto-suave)]">
        Revise el contenido antes de emitir: es el mismo que tendrá el archivo. Si edita el documento, vuelva a previsualizar.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <select aria-label="Modo de la vista previa" value={modo}
          onChange={(e) => setModo(e.target.value as ModoGeneracion)} className="rounded border px-2 py-1">
          <option value="revision">Para revisión</option>
          <option value="borrador">Borrador</option>
        </select>
        <select aria-label="Formato de la vista previa" value={formato}
          onChange={(e) => setFormato(e.target.value as FormatoGeneracion)} className="rounded border px-2 py-1">
          <option value="docx">Word</option>
          <option value="xlsx">Excel</option>
        </select>
        <button type="button" disabled={ocupado} onClick={ver} className="rounded border px-2 py-1">
          Previsualizar
        </button>
      </div>
      {mensaje && <p role="status">{mensaje}</p>}
      {vista && (
        <div className="space-y-2">
          <dl aria-label="Datos de la vista previa" className="flex flex-wrap gap-x-3">
            <div><dt className="inline">Estado: </dt><dd className="inline">{vista.estado === "borrador" ? "Borrador" : "Para revisión"}</dd></div>
            <div><dt className="inline">Revisión: </dt><dd className="inline">{vista.revision}</dd></div>
            <div><dt className="inline">Archivo: </dt><dd className="inline">{vista.nombre_archivo}</dd></div>
            <div><dt className="inline">Huella de integridad (SHA-256): </dt><dd className="inline" title={vista.instantanea_sha256}>{vista.instantanea_sha256.slice(0, 12)}…</dd></div>
          </dl>
          {vista.faltantes.length > 0 && <p>Faltan: {vista.faltantes.join(", ")}</p>}
          <article aria-label="Contenido de la vista previa" className="max-h-96 space-y-1 overflow-auto rounded border p-2">
            {vista.bloques.map((b, i) => <Bloque key={i} b={b} />)}
          </article>
          <button type="button" disabled={ocupado} onClick={emitir} className="rounded border px-2 py-1">
            Emitir este archivo
          </button>
        </div>
      )}
    </section>
  );
}
