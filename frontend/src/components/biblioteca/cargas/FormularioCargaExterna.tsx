"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
import React from "react";
import { cargarExterno, ESTADOS_ANALISIS, formatoDe, TAMANO_MAXIMO, type Carga } from "@/lib/biblioteca/cargas";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";

interface Props {
  /** Si viene, la carga es una revisión nueva de ese documento externo. */
  documentoId?: string;
  alTerminar?: (carga: Carga) => void;
}

export default function FormularioCargaExterna({ documentoId, alTerminar }: Props) {
  const [abierto, setAbierto] = React.useState(false);
  const [titulo, setTitulo] = React.useState("");
  const [codigo, setCodigo] = React.useState("");
  const [version, setVersion] = React.useState("");
  const [maestra, setMaestra] = React.useState("");
  const [archivo, setArchivo] = React.useState<File | null>(null);
  const [enviando, setEnviando] = React.useState(false);
  const [mensaje, setMensaje] = React.useState("");
  const prefijo = documentoId ? "revision" : "carga";

  const validar = (): string => {
    if (!titulo.trim() || !codigo.trim() || !version.trim()) return "Indica título, código y versión propia.";
    if (!archivo) return "Selecciona un archivo DOCX o XLSX.";
    if (!formatoDe(archivo.name)) return "Solo se admiten archivos DOCX o XLSX.";
    if (archivo.size === 0 || archivo.size > TAMANO_MAXIMO) return "El archivo debe pesar entre 1 byte y 10 MB.";
    return "";
  };

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    const error = validar();
    if (error) { setMensaje(error); return; }
    setEnviando(true); setMensaje("");
    try {
      const carga = await cargarExterno({
        titulo: titulo.trim(), codigo: codigo.trim(), version_propia: version.trim(),
        ...(maestra.trim() ? { version_maestra_id: maestra.trim() } : {}),
        ...(documentoId ? { documento_id: documentoId } : {}),
      }, archivo as File);
      setMensaje(carga.finalizada
        ? "Documento externo guardado como borrador."
        : `${ESTADOS_ANALISIS[carga.estado_analisis]}. El archivo queda retenido y no se puede descargar.`);
      alTerminar?.(carga);
    } catch (e) {
      setMensaje(e instanceof ErrorBiblioteca ? e.message : "No se pudo subir el archivo.");
    } finally { setEnviando(false); }
  };

  if (!abierto) {
    return (
      <button type="button" onClick={() => setAbierto(true)} className="self-start underline"
        data-testid={`${prefijo}-abrir`}>
        {documentoId ? "Subir revisión nueva" : "Adjuntar documento externo"}
      </button>
    );
  }

  return (
    <form onSubmit={enviar} aria-label={documentoId ? "Revisión nueva del documento externo" : "Adjuntar documento externo"}
      className="flex flex-col gap-2 rounded border border-[var(--ui-borde)] p-3" data-testid={`${prefijo}-formulario`}>
      <label className="flex flex-col">Título
        <input value={titulo} onChange={(e) => setTitulo(e.target.value)} maxLength={200} className="border p-1" />
      </label>
      <label className="flex flex-col">Código
        <input value={codigo} onChange={(e) => setCodigo(e.target.value)} maxLength={40} className="border p-1" />
      </label>
      <label className="flex flex-col">Versión propia
        <input value={version} onChange={(e) => setVersion(e.target.value)} maxLength={40} className="border p-1" />
      </label>
      <label className="flex flex-col">Versión maestra usada (opcional)
        <input value={maestra} onChange={(e) => setMaestra(e.target.value)} maxLength={36} className="border p-1"
          placeholder="Déjalo vacío si no la conoces" />
      </label>
      <label className="flex flex-col">Archivo (DOCX o XLSX, hasta 10 MB)
        <input type="file" accept=".docx,.xlsx" onChange={(e) => setArchivo(e.target.files?.[0] ?? null)} />
      </label>
      <div className="flex gap-2">
        <button type="submit" disabled={enviando} className="rounded border px-2 py-1">
          {enviando ? "Subiendo…" : "Subir"}
        </button>
        <button type="button" onClick={() => setAbierto(false)} className="underline">Cancelar</button>
      </div>
      {mensaje && <p role="status" data-testid={`${prefijo}-mensaje`}>{mensaje}</p>}
    </form>
  );
}

/** Montaje en la pestaña de documentos: alta de un documento externo nuevo. */
export function AdjuntarDocumentoExterno() {
  return <FormularioCargaExterna />;
}
