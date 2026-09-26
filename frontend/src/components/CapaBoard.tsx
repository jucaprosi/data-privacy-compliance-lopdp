"use client";

import React, { useState, useEffect, useTransition, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  UploadCloud,
  Shield,
  FileCheck,
  User,
  Activity,
  XCircle
} from "lucide-react";
import type { TicketCAPA, EstadoCAPA } from "@/types/capa";
import {
  listarTicketsCAPA,
  subirEvidenciaMejora,
  verificarCierreCapa,
} from "@/app/actions/capaActions";

// Roles simulados para la demostración de SoD (Separation of Duties)
const CURRENT_OPERADOR_ID = "operador-infra-1";
const CURRENT_AUDITOR_ID = "auditor-dpo-principal";

const KANBAN_ESTADOS: { key: EstadoCAPA; label: string; color: string; bgCol: string }[] = [
  { key: "Abierto", label: "Abiertos (Pendiente Ejecución)", color: "text-amber-400", bgCol: "border-amber-900/50" },
  { key: "Pendiente de Verificacion", label: "En Verificación DPO", color: "text-blue-400", bgCol: "border-blue-900/50" },
  { key: "Cerrado Conforme", label: "Cerrados Conforme", color: "text-[#00c853]", bgCol: "border-[#00c853]/30" },
  { key: "Rechazado", label: "Rechazados / Reabiertos", color: "text-[#ff1744]", bgCol: "border-[#ff1744]/30" },
];

export default function CapaBoard() {
  const [tickets, setTickets] = useState<TicketCAPA[]>([]);
  const [isPending, startTransition] = useTransition();
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);

  // Estados interactivos por ticket
  const [dictamenes, setDictamenes] = useState<Record<string, string>>({});
  const [uploadingTicket, setUploadingTicket] = useState<string | null>(null);

  const cargarDatos = useCallback(() => {
    startTransition(async () => {
      setErrorGlobal(null);
      const res = await listarTicketsCAPA();
      if (res.success && res.data) {
        setTickets(res.data);
      } else {
        setErrorGlobal(res.error || "Error al cargar tickets CAPA.");
      }
    });
  }, []);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const handleUploadEvidencia = async (ticketId: string, file: File) => {
    setUploadingTicket(ticketId);
    setErrorGlobal(null);
    try {
      // Simulacion de subida a storage
      await new Promise((r) => setTimeout(r, 1500));
      const urlSimulada = `https://storage.lopdp360.ec/evidencias/${file.name}`;

      const res = await subirEvidenciaMejora(ticketId, urlSimulada, CURRENT_OPERADOR_ID);
      if (!res.success) {
        setErrorGlobal(res.error || "Error al subir evidencia.");
      } else {
        cargarDatos();
      }
    } catch {
      setErrorGlobal("Error inesperado en upload.");
    } finally {
      setUploadingTicket(null);
    }
  };

  const handleVerificacion = (ticketId: string, aprobado: boolean) => {
    const nota = dictamenes[ticketId] || (aprobado ? "Cumple criterios E1+" : "No cumple");
    startTransition(async () => {
      setErrorGlobal(null);
      const res = await verificarCierreCapa(ticketId, nota, aprobado, CURRENT_AUDITOR_ID);
      if (!res.success) {
        setErrorGlobal(res.error || "Error en validación SoD / verificación.");
      } else {
        setDictamenes((prev) => ({ ...prev, [ticketId]: "" })); // Reset dictamen
        cargarDatos();
      }
    });
  };

  const renderTicket = (ticket: TicketCAPA) => {
    return (
      <div
        key={ticket.id}
        className="bg-[#141417] border border-[#26262b] rounded-xl p-4 flex flex-col space-y-3 shadow-lg shadow-black/40 hover:border-[#3a3a42] transition-colors"
      >
        {/* Cabecera del ticket */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <span className="text-[10px] font-mono text-zinc-500 block mb-1">
              ID: {ticket.id.split("-")[0].toUpperCase()}
            </span>
            <h4 className="text-sm font-semibold text-zinc-200 leading-snug">
              {ticket.descripcionHallazgo}
            </h4>
          </div>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ml-3 ${
              ticket.severidad?.includes("Mayor") || ticket.severidad?.includes("Crítica")
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : "bg-amber-950 text-amber-300 border-amber-800"
            }`}
          >
            {ticket.severidad || "Hallazgo"}
          </span>
        </div>

        {/* Origen y Responsable */}
        <div className="flex flex-col space-y-1 text-xs text-zinc-400 bg-[#0a0a0c] p-2.5 rounded-lg border border-[#26262b]/50">
          <div className="flex items-center space-x-2">
            <Shield className="w-3.5 h-3.5 text-zinc-500" />
            <span className="truncate">
              <span className="text-zinc-500">Origen:</span> {ticket.preguntaIdOriginaria} (Brecha LOPDP)
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <User className="w-3.5 h-3.5 text-zinc-500" />
            <span>
              <span className="text-zinc-500">Área Responsable:</span> {ticket.responsableArea}
            </span>
          </div>
        </div>

        {/* ================================================================================= */}
        {/* VISTA OPERADOR (Responsable de Area) - Solo si Abierto / Rechazado */}
        {/* ================================================================================= */}
        {(ticket.estado === "Abierto" || ticket.estado === "Rechazado") && (
          <div className="pt-2 border-t border-[#26262b] flex flex-col space-y-2">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
              Acción Operador (Adjuntar E2)
            </div>
            <DropzoneArea
              isUploading={uploadingTicket === ticket.id}
              onUpload={(file) => handleUploadEvidencia(ticket.id, file)}
            />
          </div>
        )}

        {/* ================================================================================= */}
        {/* VISTA AUDITOR (DPO) - Solo si Pendiente de Verificación */}
        {/* ================================================================================= */}
        {ticket.estado === "Pendiente de Verificacion" && (
          <div className="pt-2 border-t border-[#26262b] flex flex-col space-y-3">
            <div className="text-[10px] font-bold text-[#3892f3] uppercase tracking-wider flex items-center">
              <FileCheck className="w-3 h-3 mr-1" /> Consola Verificación Independiente (SoD)
            </div>

            <div className="bg-emerald-950/20 border border-emerald-900/50 p-2 rounded text-xs">
              <span className="text-emerald-500 font-semibold block mb-0.5">Evidencia Subida:</span>
              <a
                href="#"
                className="text-emerald-300 font-mono text-[10px] truncate block hover:underline"
              >
                {ticket.evidenciaMitigacion}
              </a>
              <span className="text-[10px] text-zinc-500 mt-1 block">
                Subido por: {ticket.usuarioQueSubioEvidencia}
              </span>
            </div>

            <textarea
              className="w-full bg-[#0a0a0c] border border-[#26262b] rounded-lg p-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-[#3892f3]"
              placeholder="Dictamen técnico del auditor..."
              rows={2}
              value={dictamenes[ticket.id] || ""}
              onChange={(e) => setDictamenes((prev) => ({ ...prev, [ticket.id]: e.target.value }))}
            />

            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => handleVerificacion(ticket.id, false)}
                disabled={isPending}
                className="flex-1 bg-[#2a1114] hover:bg-[#ff1744]/20 border border-[#ff1744]/40 text-[#ff1744] rounded-lg py-1.5 text-xs font-bold transition disabled:opacity-50 flex items-center justify-center"
              >
                <XCircle className="w-3.5 h-3.5 mr-1" /> Rechazar
              </button>
              <button
                type="button"
                onClick={() => handleVerificacion(ticket.id, true)}
                disabled={isPending || !dictamenes[ticket.id]?.trim()}
                className="flex-1 bg-[#0a1e12] hover:bg-[#00c853]/20 border border-[#00c853]/40 text-[#00c853] rounded-lg py-1.5 text-xs font-bold transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                title={!dictamenes[ticket.id]?.trim() ? "Requiere dictamen para aprobar" : ""}
              >
                <CheckCircle className="w-3.5 h-3.5 mr-1" /> Aprobar Cierre
              </button>
            </div>
          </div>
        )}

        {/* ================================================================================= */}
        {/* VISTA CERRADO / HISTORIAL */}
        {/* ================================================================================= */}
        {ticket.estado === "Cerrado Conforme" && (
          <div className="pt-2 border-t border-[#00c853]/20 flex flex-col space-y-2">
            <div className="text-[10px] font-bold text-[#00c853] uppercase tracking-wider flex items-center">
              <Shield className="w-3 h-3 mr-1" /> Expediente Sellado
            </div>
            <div className="text-[10px] text-zinc-400 font-mono">
              Auditor: {ticket.auditorAsignado} <br />
              Cierre: {new Date(ticket.fechaCierreConforme!).toLocaleString("es-EC")}
            </div>
            <div className="bg-[#0a0a0c] border border-[#26262b] rounded p-2 text-xs text-emerald-400 italic">
              &quot;{ticket.dictamenAuditor}&quot;
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Header CAPA */}
      <div className="flex items-center justify-between pb-4 border-b border-[#26262b] shrink-0">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-[#ff1744]" /> Tablero de Hallazgos y CAPA
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Gestión de no conformidades (Arts. 10 y 41 LOPDP). Teorema 4 (Separación de Funciones - SoD) estrictamente forzado.
          </p>
        </div>
        <button
          onClick={cargarDatos}
          disabled={isPending}
          className="p-2 bg-[#141417] hover:bg-[#1e1e24] border border-[#26262b] rounded-lg text-zinc-400 hover:text-white transition cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${isPending ? "animate-spin" : ""}`} />
        </button>
      </div>

      {errorGlobal && (
        <div className="bg-[#ff1744]/10 border border-[#ff1744]/30 text-[#ff1744] p-3 rounded-xl flex items-start text-xs shadow-lg shrink-0">
          <AlertTriangle className="w-4 h-4 mr-2 shrink-0 mt-0.5" />
          <span className="font-medium">{errorGlobal}</span>
        </div>
      )}

      {/* Grid Kanban */}
      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 overflow-x-auto pb-4">
        {KANBAN_ESTADOS.map((col) => {
          const ticketsCol = tickets.filter((t) => t.estado === col.key);

          return (
            <div
              key={col.key}
              className={`flex flex-col h-full bg-[#0a0a0c] border-t-2 ${col.bgCol} border-[#26262b] border-x border-b rounded-xl overflow-hidden`}
            >
              <div className="p-3 border-b border-[#26262b] bg-[#141417] flex items-center justify-between shrink-0">
                <span className={`text-xs font-bold uppercase tracking-wider ${col.color}`}>
                  {col.label}
                </span>
                <span className="bg-[#0a0a0c] border border-[#26262b] text-zinc-400 text-[10px] font-mono px-2 py-0.5 rounded-full">
                  {ticketsCol.length}
                </span>
              </div>
              
              <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                {ticketsCol.length === 0 ? (
                  <div className="h-24 flex items-center justify-center text-zinc-600 text-xs border border-dashed border-[#26262b] rounded-xl">
                    Sin hallazgos
                  </div>
                ) : (
                  ticketsCol.map(renderTicket)
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Subcomponente Dropzone para UI de Operador
// ---------------------------------------------------------------------------

function DropzoneArea({
  onUpload,
  isUploading,
}: {
  onUpload: (f: File) => void;
  isUploading: boolean;
}) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    disabled: isUploading,
  });

  if (isUploading) {
    return (
      <div className="h-16 w-full rounded-lg bg-[#0a0a0c] border border-[#26262b] p-3 flex flex-col items-center justify-center relative overflow-hidden">
        {/* Skeleton animado estilo Render (purpura a cyan) */}
        <div className="absolute inset-0 w-[200%] animate-[slide_1.5s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-[#9a3bf1]/40 to-[#3892f3]/40" />
        <RefreshCw className="w-4 h-4 text-white animate-spin relative z-10" />
        <span className="text-[10px] text-white font-medium mt-1 relative z-10">
          Procesando Evidencia y actualizando flujo...
        </span>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`h-16 w-full rounded-lg border border-dashed flex flex-col items-center justify-center text-center cursor-pointer transition-colors px-2 ${
        isDragActive
          ? "border-[#9a3bf1] bg-[#9a3bf1]/10 text-[#9a3bf1]"
          : "border-[#3a3a42] bg-[#0a0a0c] hover:border-[#9a3bf1]/50 text-zinc-400 hover:text-zinc-300"
      }`}
    >
      <input {...getInputProps()} />
      <UploadCloud className="w-4 h-4 mb-1" />
      <span className="text-[10px]">
        {isDragActive ? "Suelta el archivo aquí..." : "Clic o arrastra evidencia E2 para mitigar"}
      </span>
    </div>
  );
}
