"use client";

import React, { useState } from "react";
import { FileText, Download, Gauge, Clock } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { descargarReporteAssessment } from "@/lib/reportes/generarReporteAssessment";

interface ReporteDisponible {
  id: string;
  nombre: string;
  descripcion: string;
  icono: React.ElementType;
  disponible: boolean;
}

export default function ReportesModule() {
  const { calcularResultadoAssessment, companyData } = useAuditStore();
  const [descargando, setDescargando] = useState<string | null>(null);

  const reportes: ReporteDisponible[] = [
    {
      id: "assessment",
      nombre: "Assessment de Madurez SGPDP",
      descripcion:
        "Score ponderado, nivel de madurez ajustado, matriz por dimensión y registro de brechas detectadas.",
      icono: Gauge,
      disponible: true,
    },
  ];

  const manejarDescarga = (id: string) => {
    if (id !== "assessment") return;
    setDescargando(id);
    try {
      const resultado = calcularResultadoAssessment("declarado");
      const verificado = calcularResultadoAssessment("verificado");
      descargarReporteAssessment(resultado, verificado, companyData);
    } finally {
      setDescargando(null);
    }
  };

  return (
    <div className="space-y-4 font-sans">
      <div className="rounded-xl bg-[#141417] border border-[#26262b] shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-[#26262b] flex items-center space-x-2">
          <FileText className="w-4 h-4 text-[#9a3bf1]" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Reportes Disponibles
          </h3>
        </div>

        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {reportes.map((reporte) => {
            const Icon = reporte.icono;
            return (
              <div
                key={reporte.id}
                className="p-4 rounded-lg border border-[#26262b] bg-[#1e1e24] space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start space-x-2.5 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-[#9a3bf1]/15 border border-[#9a3bf1]/30 flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-[#9a3bf1]" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[12px] font-bold text-white leading-snug">
                        {reporte.nombre}
                      </p>
                      <p className="text-[10px] text-zinc-400 leading-relaxed mt-1">
                        {reporte.descripcion}
                      </p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => manejarDescarga(reporte.id)}
                  disabled={!reporte.disponible || descargando === reporte.id}
                  className="flex items-center justify-center space-x-2 w-full h-8 rounded-md bg-[#9a3bf1] hover:bg-[#8a2be2] disabled:opacity-40 disabled:cursor-not-allowed text-white text-[11px] font-semibold transition cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>
                    {descargando === reporte.id ? "Generando..." : "Descargar Reporte"}
                  </span>
                </button>
              </div>
            );
          })}

          {/* Placeholder de reportes futuros */}
          <div className="p-4 rounded-lg border border-dashed border-[#26262b] bg-[#0a0a0c]/40 flex flex-col items-center justify-center text-center space-y-1.5">
            <Clock className="w-5 h-5 text-zinc-600" />
            <p className="text-[10px] text-zinc-500 leading-relaxed">
              Próximos reportes (RAT, MTGE, CAPA) se incorporarán a esta bóveda.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
