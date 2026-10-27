"use client";

import React, { useState, useEffect } from "react";
import { UserCircle, Clock, AlertTriangle, FileText, ShieldAlert, Loader2 } from "lucide-react";
import { fetchAutenticado } from "@/lib/auth";

type EstadoSolicitud = "RECIBIDA" | "EN_ANALISIS" | "EN_REQUERIMIENTO" | "CONTESTADA" | "VENCIDA";
type TipoSolicitud = "ACCESO" | "RECTIFICACION" | "CANCELACION" | "OPOSICION" | "PORTABILIDAD";

interface SolicitudARCO {
  id: string;
  tipo: TipoSolicitud;
  estado: EstadoSolicitud;
  solicitante: string;
  cedula: string;
  diasRestantes: number;
}

interface SolicitudARCOResponse {
  id: string;
  tipo_solicitud: TipoSolicitud;
  estado: EstadoSolicitud;
  nombre_solicitante: string;
  cedula_solicitante: string;
  fecha_vencimiento: string;
}

const diasHasta = (fechaVencimiento: string) =>
  Math.ceil((new Date(fechaVencimiento).getTime() - Date.now()) / 86_400_000);

export default function ArcoModule() {
  const [solicitudes, setSolicitudes] = useState<SolicitudARCO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSolicitudes = async () => {
      try {
        const res = await fetchAutenticado("/api/v1/arco/solicitudes");
        if (!res.ok) throw new Error("Error al obtener solicitudes ARCO+");
        const data = await res.json() as SolicitudARCOResponse[];
        
        // Mapeo snake_case a camelCase
        const mappedData: SolicitudARCO[] = data.map((item) => ({
          id: item.id,
          tipo: item.tipo_solicitud,
          estado: item.estado,
          solicitante: item.nombre_solicitante,
          cedula: item.cedula_solicitante,
          diasRestantes: diasHasta(item.fecha_vencimiento),
        }));
        
        setSolicitudes(mappedData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    };

    fetchSolicitudes();
  }, []);

  const getEstadoColor = (estado: EstadoSolicitud, diasRestantes: number) => {
    if (estado === "VENCIDA" || diasRestantes < 0) return "text-[#ff1744] bg-[#ff1744]/10 border-[#ff1744]/30";
    if (estado === "CONTESTADA") return "text-[#00c853] bg-[#00c853]/10 border-[#00c853]/30";
    if (diasRestantes <= 3) return "text-amber-400 bg-amber-400/10 border-amber-400/30";
    return "text-[#3892f3] bg-[#3892f3]/10 border-[#3892f3]/30";
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <UserCircle className="w-5 h-5 mr-2 text-[#3892f3]" />
          Derechos ARCO+ y Titulares
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Gestión de solicitudes de derechos con SLA normativo de 15 días (Art. 13 LOPDP).
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <Loader2 className="w-8 h-8 text-[#3892f3] animate-spin" />
          <span className="text-sm text-[var(--ui-texto-suave)] font-mono">Cargando solicitudes desde FastAPI...</span>
        </div>
      ) : error ? (
        <div className="p-4 bg-[#ff1744]/10 border border-[#ff1744]/30 rounded-xl flex items-center text-[#ff1744] text-sm">
          <AlertTriangle className="w-5 h-5 mr-3" />
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {solicitudes.length === 0 && (
             <div className="p-8 text-center text-[var(--ui-texto-suave)] text-sm border border-dashed border-[var(--ui-borde)] rounded-xl">
               No hay solicitudes ARCO+ registradas.
             </div>
          )}
          {solicitudes.map((s) => (
            <div key={s.id} className="p-4 bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl flex justify-between items-center hover:border-[#3892f3]/50 transition-colors">
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-lg border ${getEstadoColor(s.estado, s.diasRestantes)}`}>
                  {s.estado === "VENCIDA" ? <ShieldAlert className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                </div>
                <div>
                  <h4 className="font-medium text-sm text-zinc-200">{s.tipo} - {s.solicitante}</h4>
                  <div className="text-xs text-[var(--ui-texto-suave)] font-mono mt-1">ID: {s.id} | CC: {s.cedula}</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <div className="text-xs text-[var(--ui-texto-suave)]">SLA Normativo</div>
                  <div className={`text-sm font-bold flex items-center justify-end mt-0.5 ${s.diasRestantes < 0 ? "text-[#ff1744]" : s.diasRestantes <= 3 ? "text-amber-400" : "text-[#00c853]"}`}>
                    <Clock className="w-3.5 h-3.5 mr-1" />
                    {s.diasRestantes < 0 ? `Vencido por ${Math.abs(s.diasRestantes)} días` : `${s.diasRestantes} días restantes`}
                  </div>
                </div>
                <button className="px-3 py-1.5 bg-[var(--ui-borde)] hover:bg-[#3892f3]/20 text-zinc-200 hover:text-[#3892f3] border border-[var(--ui-borde)] hover:border-[#3892f3]/50 rounded text-xs font-medium transition-colors cursor-pointer">
                  Gestionar Expediente
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
