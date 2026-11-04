"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Procedencia de los datos reutilizados del documento elegido (BIB-202). Muestra la instantánea emitida
 * (no se reescribe), avisa si la fuente cambió y deja proponer una corrección sin tocar el dato canónico.
 * Si la carga falla no muestra alerta: se queda con un estado neutro.
 */
import React from "react";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";
import { cambiosDeFuente, emitirInstantanea, proponerCorreccion, type AvisoCambios, type OrigenCampo } from "@/lib/biblioteca/fuentes";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";

const fuentes: Record<OrigenCampo["fuente"], string> = {
  organizacion: "Organización", dpd: "Delegado (DPD)", rat: "RAT", diagnostico: "Diagnóstico",
};

export default function PanelProcedencia() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [aviso, setAviso] = React.useState<AvisoCambios | null>(null);
  const [estado, setEstado] = React.useState<"cargando" | "sin_instantanea" | "listo" | "no_disponible">("cargando");
  const [mensaje, setMensaje] = React.useState("");
  const [clave, setClave] = React.useState("");
  const [valor, setValor] = React.useState("");
  const [motivo, setMotivo] = React.useState("");

  const cargar = React.useCallback(async () => {
    if (!documentoId) return;
    try { setAviso(await cambiosDeFuente(documentoId)); setEstado("listo"); }
    catch (e) {
      setAviso(null);
      setEstado(e instanceof ErrorBiblioteca && e.codigo === "BIB_PROCEDENCIA_SIN_INSTANTANEA" ? "sin_instantanea" : "no_disponible");
    }
  }, [documentoId]);
  React.useEffect(() => { setEstado("cargando"); void cargar(); }, [cargar]);
  if (!documentoId) return null;

  const emitir = async () => {
    try { await emitirInstantanea(documentoId); setMensaje("Se guardó la procedencia de esta revisión."); await cargar(); }
    catch { setMensaje("No se pudo guardar la procedencia."); }
  };
  const proponer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clave || !valor.trim() || motivo.trim().length < 3) { setMensaje("Elige el dato, escribe el valor y el motivo."); return; }
    try {
      await proponerCorreccion(documentoId, clave, valor.trim(), motivo.trim());
      setMensaje("Corrección propuesta. El dato de origen no cambió."); setValor(""); setMotivo("");
    } catch { setMensaje("No se pudo registrar la propuesta."); }
  };

  return (
    <section data-testid="procedencia-documento" aria-label="Procedencia de los datos" className="mt-3 flex flex-col gap-3 border-t border-[var(--ui-borde)] pt-3 text-xs">
      <h4 className="font-semibold">Procedencia de los datos</h4>
      {mensaje && <p role="status">{mensaje}</p>}
      {estado === "cargando" && <p>Cargando procedencia…</p>}
      {estado === "no_disponible" && <p className="text-[var(--ui-texto-suave)]">La procedencia no está disponible ahora.</p>}
      {estado === "sin_instantanea" && <div className="flex flex-col gap-2">
        <p>Esta revisión aún no guarda de dónde salen sus datos.</p>
        <button type="button" onClick={() => void emitir()} className="self-start underline">Guardar procedencia</button>
      </div>}
      {aviso && <>
        {aviso.cambiado
          ? <div data-testid="aviso-cambio-fuente" role="status" className="rounded border border-amber-500 p-2">
              <p className="font-semibold">La fuente cambió después de emitir este documento.</p>
              <p>El documento conserva los valores emitidos; revisa si debe actualizarse.</p>
              <ul>{aviso.cambios.map((c) => <li key={c.clave}>{c.clave}: «{c.emitido ?? "—"}» → «{c.actual ?? "—"}»</li>)}</ul>
            </div>
          : <p data-testid="fuente-sin-cambios">Los datos de origen no han cambiado desde la emisión.</p>}
        <table className="w-full text-left">
          <thead><tr><th>Dato</th><th>Valor emitido</th><th>Origen</th><th>Versión</th><th>Fecha</th><th>Validación</th></tr></thead>
          <tbody>{aviso.emitida.campos.map((c) => (
            <tr key={c.clave} data-testid="campo-procedencia">
              <td>{c.clave}</td><td>{c.valor}</td><td>{fuentes[c.fuente]} · {c.fuente_id}</td>
              <td>{c.revision ?? "sin versión"}</td><td>{c.fecha ?? "—"}</td>
              <td>{c.estado === "validado" ? `Validado por ${c.validador}` : "Sin validar"}{c.limitacion && <span title={c.limitacion}> · sin historial</span>}</td>
            </tr>))}</tbody>
        </table>
        <form onSubmit={(e) => void proponer(e)} className="flex flex-col gap-2" aria-label="Proponer corrección">
          <label className="flex flex-col gap-1">Dato
            <select value={clave} onChange={(e) => setClave(e.target.value)} className="rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-1">
              <option value="">Elige un dato</option>
              {aviso.actual.campos.map((c) => <option key={c.clave} value={c.clave}>{c.clave}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">Valor propuesto
            <input value={valor} onChange={(e) => setValor(e.target.value)} className="rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-1" />
          </label>
          <label className="flex flex-col gap-1">Motivo
            <textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} className="rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-1" />
          </label>
          <button type="submit" className="self-start underline">Proponer corrección</button>
        </form>
      </>}
    </section>
  );
}
