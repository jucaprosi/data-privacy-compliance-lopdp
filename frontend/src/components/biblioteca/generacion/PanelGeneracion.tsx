"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Generación de Word y Excel del documento elegido (BIB-205), en la ranura `documento:acciones`.
 *
 * - «Generar borrador» admite datos que faltan: el archivo lleva la marca Borrador y su listado.
 * - «Generar para revisión» exige los obligatorios y condicionales; si faltan, se informa y no se crea nada.
 * - Generar no aprueba el documento ni cierra acciones. Los fallos se anuncian con `role="status"`.
 */
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  descargarGeneracion, generar, listarGeneraciones,
  type FormatoGeneracion, type Generacion, type ModoGeneracion,
} from "@/lib/biblioteca/generacion";

declare global {
  interface Window {
    __LOPDP_GENERACION_PRUEBAS__?: { borradorId?: string };
  }
}

const FORMATOS: { id: FormatoGeneracion; nombre: string }[] = [
  { id: "docx", nombre: "Word" }, { id: "xlsx", nombre: "Excel" },
];

export default function PanelGeneracion() {
  const seleccion = useSeleccionBiblioteca((s) => s.documentoId);
  const pruebas = typeof window !== "undefined" ? window.__LOPDP_GENERACION_PRUEBAS__?.borradorId : undefined;
  const borradorId = seleccion || pruebas || null;
  const [formato, setFormato] = React.useState<FormatoGeneracion>("docx");
  const [lista, setLista] = React.useState<Generacion[]>([]);
  const [mensaje, setMensaje] = React.useState("");
  const [ocupado, setOcupado] = React.useState(false);

  React.useEffect(() => {
    if (!borradorId) return;
    let vigente = true;
    listarGeneraciones(borradorId).then((g) => vigente && setLista(g)).catch(() => vigente && setLista([]));
    return () => { vigente = false; };
  }, [borradorId]);

  if (!borradorId) return null;

  const pedir = async (modo: ModoGeneracion) => {
    setOcupado(true);
    setMensaje("");
    try {
      const nueva = await generar(borradorId, modo, formato);
      setLista((actual) => [nueva, ...actual.filter((g) => g.id !== nueva.id)]);
      setMensaje(nueva.estado === "borrador"
        ? `Borrador generado${nueva.faltantes.length ? ` con ${nueva.faltantes.length} datos por completar` : ""}.`
        : "Archivo para revisión generado.");
    } catch (e) {
      setMensaje(`No se generó el archivo: ${e instanceof Error ? e.message : "error desconocido"}`);
    } finally {
      setOcupado(false);
    }
  };

  const bajar = async (g: Generacion) => {
    try { await descargarGeneracion(g); } catch (e) { setMensaje(e instanceof Error ? e.message : "No se pudo descargar."); }
  };

  return (
    <section aria-label="Generar Word y Excel" data-testid="generacion-documento"
      className="mt-3 space-y-2 border-t border-[var(--ui-borde)] pt-3 text-xs">
      <h4 className="font-semibold">Generar Word y Excel</h4>
      <p className="text-[var(--ui-texto-suave)]">
        El archivo sale de una instantánea fija de los datos y la plantilla. Generarlo no aprueba el documento.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <select aria-label="Formato" value={formato} onChange={(e) => setFormato(e.target.value as FormatoGeneracion)}
          className="rounded border px-2 py-1">
          {FORMATOS.map((f) => <option key={f.id} value={f.id}>{f.nombre}</option>)}
        </select>
        <button type="button" disabled={ocupado} onClick={() => pedir("borrador")} className="rounded border px-2 py-1">
          Generar borrador
        </button>
        <button type="button" disabled={ocupado} onClick={() => pedir("revision")} className="rounded border px-2 py-1">
          Generar para revisión
        </button>
      </div>
      {mensaje && <p role="status">{mensaje}</p>}
      {lista.length > 0 && (
        <ul aria-label="Archivos generados" className="space-y-1">
          {lista.map((g) => (
            <li key={g.id} className="flex flex-wrap items-center gap-2">
              <span>{g.nombre_archivo}</span>
              <span>{g.estado === "borrador" ? "Borrador" : "Para revisión"}</span>
              {g.faltantes.length > 0 && <span>Faltan: {g.faltantes.join(", ")}</span>}
              <span title={g.archivo_sha256}>Huella de integridad (SHA-256) {g.archivo_sha256.slice(0, 12)}…</span>
              <button type="button" onClick={() => bajar(g)} className="rounded border px-2 py-1">
                Descargar {g.nombre_archivo}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
