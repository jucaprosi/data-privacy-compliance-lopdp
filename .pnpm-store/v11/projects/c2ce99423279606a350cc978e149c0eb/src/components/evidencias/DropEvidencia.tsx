"use client";

import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import { AlertTriangle, CheckCircle2, Loader2, UploadCloud } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { registrarArchivoComoEvidencia } from "@/lib/evidencias/registro";
import { resolverNormativa } from "@/lib/normativas";

const SUGERENCIA_POR_NIVEL: Record<number, string> = {
  1: "Una política, un procedimiento o un borrador formal que documente esta práctica.",
  2: "Registros que muestren que la práctica se ejecuta: bitácoras, actas, reportes o capturas.",
  3: "Un informe de auditoría, una certificación o una validación externa.",
};

interface Aviso {
  tipo: "exito" | "duplicado" | "error";
  texto: string;
}

interface DropEvidenciaProps {
  preguntaId: number;
  nivel: number;
  evidenciaEsperada: string;
  /** El control ya tiene al menos un documento vinculado. */
  tieneEvidencia: boolean;
}

/**
 * Campo para subir, desde la propia pregunta, el documento que respalda el nivel
 * de evidencia declarado. Registra la huella y vincula el documento al control.
 */
export default function DropEvidencia({
  preguntaId,
  nivel,
  evidenciaEsperada,
  tieneEvidencia,
}: DropEvidenciaProps) {
  const normativaSeleccionada = useAuditStore((s) => s.normativaSeleccionada);
  const normativa = resolverNormativa(normativaSeleccionada);
  const [enProceso, setEnProceso] = useState(0);
  const [avisos, setAvisos] = useState<Aviso[]>([]);

  const procesar = async (archivos: File[]) => {
    setAvisos([]);
    setEnProceso((n) => n + archivos.length);
    const nuevos: Aviso[] = [];
    for (const archivo of archivos) {
      const resultado = await registrarArchivoComoEvidencia(archivo, { controles: [preguntaId] });
      if (!resultado.ok) {
        nuevos.push({ tipo: "error", texto: resultado.error });
      } else if (resultado.duplicada) {
        nuevos.push({
          tipo: "duplicado",
          texto: `"${archivo.name}" ya estaba registrado como ${resultado.evidencia.codigo}; se vinculó a este control.`,
        });
      } else {
        nuevos.push({
          tipo: "exito",
          texto: `"${archivo.name}" registrado como ${resultado.evidencia.codigo} y vinculado a este control.`,
        });
      }
      setEnProceso((n) => n - 1);
    }
    setAvisos(nuevos);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (aceptados) => {
      if (aceptados.length > 0) void procesar(aceptados);
    },
  });

  const falta = !tieneEvidencia;

  return (
    <div className="space-y-2" data-testid="drop-evidencia">
      <div
        {...getRootProps()}
        className={`rounded-lg border-2 border-dashed px-3.5 py-3 cursor-pointer transition flex items-center gap-3 ${
          isDragActive
            ? "border-[#9a3bf1] bg-[#9a3bf1]/10"
            : falta
            ? "border-[#ffab00]/50 bg-[#ffab00]/5 hover:border-[#ffab00]"
            : "border-[#26262b] bg-[#0a0a0c] hover:border-[#9a3bf1]/60"
        }`}
      >
        <input {...getInputProps()} accept={normativa.accept} aria-label="Subir documento de evidencia" />
        <div className="w-9 h-9 rounded-full bg-[#1e1e24] flex items-center justify-center shrink-0">
          {enProceso > 0 ? (
            <Loader2 className="w-4 h-4 text-[#9a3bf1] animate-spin" />
          ) : (
            <UploadCloud className={`w-4 h-4 ${falta ? "text-[#ffab00]" : "text-[#9a3bf1]"}`} />
          )}
        </div>
        <div className="min-w-0 space-y-0.5">
          <p className="text-xs font-semibold text-white">
            {enProceso > 0
              ? "Calculando la huella del documento…"
              : falta
              ? `Sube el documento que respalda el nivel E${nivel}`
              : "Sube otro documento para este control"}
          </p>
          <p className="text-[10px] text-zinc-400 leading-relaxed">
            {SUGERENCIA_POR_NIVEL[nivel] ?? evidenciaEsperada}{" "}
            <span className="text-zinc-500">
              Formatos: {normativa.extensiones.join(", ")}. El archivo no sale de tu equipo: solo se registra su huella.
            </span>
          </p>
        </div>
      </div>

      {avisos.map((aviso, i) => (
        <div
          key={`${aviso.tipo}-${i}`}
          role={aviso.tipo === "error" ? "alert" : "status"}
          className={`flex items-start gap-2 px-3 py-2 rounded-lg border text-[11px] leading-relaxed ${
            aviso.tipo === "error"
              ? "bg-[#ff1744]/10 border-[#ff1744]/40 text-[#ff1744]"
              : aviso.tipo === "duplicado"
              ? "bg-[#ffab00]/10 border-[#ffab00]/40 text-[#ffab00]"
              : "bg-[#00c853]/10 border-[#00c853]/40 text-[#00c853]"
          }`}
        >
          {aviso.tipo === "exito" ? (
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          )}
          <span>{aviso.texto}</span>
        </div>
      ))}
    </div>
  );
}
