"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Guardado con control de cambios del borrador elegido (BIB-207), en la ranura `documento:editor`.
 *
 * Se guarda con la revisión que se abrió. Si otra persona guardó antes, el servidor responde conflicto y aquí
 * se comparan los campos (lo tuyo frente a lo guardado) para recuperar tus cambios sobre la versión vigente o
 * quedarte con la guardada. Nada se pierde en silencio. Sin `role="alert"`; si la carga falla no se muestra.
 */
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  guardarConRevision, obtenerBorrador, type BorradorEditable, type Conflicto, type Valor,
} from "@/lib/biblioteca/trabajos";

const mostrar = (v: Valor | null | undefined) =>
  v === null || v === undefined || v === "" ? "(vacío)" : Array.isArray(v) ? v.join(", ") : String(v);

export default function GuardadoSeguro() {
  const seleccion = useSeleccionBiblioteca((s) => s.documentoId);
  const pruebas = typeof window !== "undefined" ? window.__LOPDP_TRABAJOS_PRUEBAS__?.borradorId : undefined;
  const borradorId = seleccion || pruebas || null;
  const [borrador, setBorrador] = React.useState<BorradorEditable | null>(null);
  const [valores, setValores] = React.useState<Record<string, Valor>>({});
  const [revision, setRevision] = React.useState(0);
  const [conflicto, setConflicto] = React.useState<Conflicto | null>(null);
  const [mensaje, setMensaje] = React.useState("");

  React.useEffect(() => {
    if (!borradorId) return;
    let vigente = true;
    obtenerBorrador(borradorId).then((b) => {
      if (!vigente) return;
      setBorrador(b); setValores(b.contexto); setRevision(b.revision);
    }).catch(() => vigente && setBorrador(null));
    return () => { vigente = false; };
  }, [borradorId]);

  if (!borradorId || !borrador) return null;
  const etiqueta = (clave: string) => borrador.campos.find((c) => c.clave === clave)?.etiqueta ?? clave;

  const guardar = async (sobre: number) => {
    setMensaje("");
    try {
      const r = await guardarConRevision(borrador.id, sobre, valores);
      if (r.ok) {
        setRevision(r.revision); setConflicto(null);
        setMensaje(`Cambios guardados (revisión ${r.revision}).`);
      } else {
        setConflicto(r.conflicto);
        setMensaje("No se guardó: otra persona cambió el borrador. Compara y elige cómo seguir.");
      }
    } catch (e) {
      setMensaje(`No se guardó: ${e instanceof Error ? e.message : "error desconocido"}`);
    }
  };

  const usarGuardada = () => {
    if (!conflicto) return;
    setValores(conflicto.contexto_vigente); setRevision(conflicto.revision_vigente); setConflicto(null);
    setMensaje(`Se cargó la versión guardada (revisión ${conflicto.revision_vigente}); tus cambios se descartaron.`);
  };

  return (
    <section aria-label="Guardado con control de cambios" data-testid="guardado-seguro"
      className="mt-3 space-y-2 border-t border-[var(--ui-borde)] pt-3 text-xs">
      <h4 className="font-semibold">Guardado con control de cambios</h4>
      <p className="text-[var(--ui-texto-suave)]">Editas la revisión {revision}. Si alguien guarda antes, podrás comparar.</p>
      {borrador.campos.filter((c) => c.tipo !== "lista").map((c) => (
        <label key={c.clave} className="flex flex-col gap-1">
          <span>{c.etiqueta}</span>
          {c.tipo === "si_no" ? (
            <select value={String(valores[c.clave] ?? "")} className="rounded border px-2 py-1"
              onChange={(e) => setValores({ ...valores, [c.clave]: e.target.value })}>
              <option value="">Sin responder</option>
              <option value="si">Sí</option>
              <option value="no">No</option>
            </select>
          ) : (
            <input value={String(valores[c.clave] ?? "")} className="rounded border px-2 py-1"
              onChange={(e) => setValores({ ...valores, [c.clave]: e.target.value })} />
          )}
        </label>
      ))}
      <button type="button" onClick={() => guardar(revision)} className="rounded border px-2 py-1">Guardar cambios</button>
      {mensaje && <p role="status">{mensaje}</p>}
      {conflicto && (
        <div role="group" aria-label="Conflicto de edición" className="space-y-2 rounded border p-2">
          <p>Tú partiste de la revisión {conflicto.revision_esperada}; la guardada es la {conflicto.revision_vigente}.</p>
          <table aria-label="Comparación de cambios">
            <thead><tr><th>Campo</th><th>Tu valor</th><th>Valor guardado</th></tr></thead>
            <tbody>
              {conflicto.diferencias.map((d) => (
                <tr key={d.clave}><td>{etiqueta(d.clave)}</td><td>{mostrar(d.mio)}</td><td>{mostrar(d.vigente)}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => guardar(conflicto.revision_vigente)} className="rounded border px-2 py-1">
              Recuperar mis cambios
            </button>
            <button type="button" onClick={usarGuardada} className="rounded border px-2 py-1">Usar la versión guardada</button>
          </div>
        </div>
      )}
    </section>
  );
}
