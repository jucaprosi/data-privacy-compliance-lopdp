"use client";

import React, { useState, useEffect } from "react";
import useSWR from "swr";
import { Bot, AlertTriangle, ShieldCheck, Clock, ChevronRight, Zap } from "lucide-react";

// --- Tipos ---
export type ImpactoRiesgo = "ALTO" | "MEDIO" | "BAJO";
export type EstadoMitigacion = "PENDIENTE" | "EN_PROGRESO" | "COMPLETADO";

export interface Mitigacion {
  id: string;
  titulo: string;
  descripcion: string;
  impacto_riesgo: ImpactoRiesgo;
  estado: EstadoMitigacion;
}

// --- Lógica de Red (Fetchers) ---
const MOCK_JWT = "jwt_mock_tenant_123";

const fetcher = async (url: string) => {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${MOCK_JWT}`,
    },
  });
  if (!res.ok) {
    throw new Error("Error al cargar mitigaciones");
  }
  return res.json() as Promise<Mitigacion[]>;
};

const detonarDiagnostico = async () => {
  const res = await fetch("/api/v1/ai/diagnosticar", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${MOCK_JWT}`,
    },
  });
  if (!res.ok) {
    throw new Error("Error al detonar diagnóstico IA");
  }
  return res.json();
};

// --- Subcomponentes de UI ---
const KanbanColumn = ({ titulo, color, icono: Icon, mitigaciones }: { titulo: string, color: string, icono: React.ElementType, mitigaciones: Mitigacion[] }) => (
  <div className="flex flex-col bg-[#141417] border border-[#26262b] rounded-xl overflow-hidden h-full min-h-[300px]">
    <div className={`flex items-center px-4 py-3 border-b border-[#26262b] bg-[#0a0a0c] shrink-0`}>
      <Icon className={`w-4 h-4 mr-2 ${color}`} />
      <h3 className="font-semibold text-zinc-200 text-sm">{titulo}</h3>
      <span className="ml-auto bg-[#1e1e24] text-zinc-400 text-[10px] font-mono px-2 py-0.5 rounded-full border border-[#26262b]">
        {mitigaciones.length}
      </span>
    </div>
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      {mitigaciones.length === 0 ? (
        <div className="text-center py-8 text-zinc-600 text-xs font-medium">
          No hay tareas en esta categoría.
        </div>
      ) : (
        mitigaciones.map(m => (
          <div key={m.id} className="bg-[#1e1e24] border border-[#26262b] rounded-lg p-3 hover:border-zinc-700 transition group cursor-pointer shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-zinc-200 text-xs font-semibold leading-relaxed group-hover:text-white transition">
                {m.titulo}
              </h4>
            </div>
            <p className="text-[#a0a0ab] text-[11px] line-clamp-2 mb-3">
              {m.descripcion}
            </p>
            <div className="flex items-center justify-between mt-auto pt-2 border-t border-[#26262b]">
              <span className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                m.estado === 'PENDIENTE' ? 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30' :
                m.estado === 'EN_PROGRESO' ? 'bg-blue-500/10 text-blue-400 border-blue-500/30' :
                'bg-[#00c853]/10 text-[#00c853] border-[#00c853]/30'
              }`}>
                {m.estado}
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-[#9a3bf1] transition" />
            </div>
          </div>
        ))
      )}
    </div>
  </div>
);

const Skeleton = () => (
  <div className="w-full h-full flex flex-col space-y-4 animate-pulse">
    <div className="flex justify-between items-center bg-[#141417] p-4 rounded-xl border border-[#26262b]">
      <div className="h-6 bg-[#26262b] rounded w-48"></div>
      <div className="h-8 bg-[#26262b] rounded w-32"></div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-[#141417] border border-[#26262b] rounded-xl h-[400px]"></div>
      ))}
    </div>
  </div>
);

// --- Componente Principal ---
export default function MitigationTracker() {
  const [mounted, setMounted] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Prevención Hydration Mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetching & Polling nativo vía SWR
  const { data: mitigaciones, error, isLoading, mutate } = useSWR<Mitigacion[]>(
    mounted ? "/api/v1/ai/mitigaciones" : null,
    fetcher,
    { refreshInterval: 5000 } // Polling cada 5 seg para capturar el progreso de la IA
  );

  const handleGenerarPlan = async () => {
    setIsGenerating(true);
    try {
      await detonarDiagnostico();
      await mutate(); // Refrescar tablero tras el inicio del análisis
    } catch (err) {
      console.error("Error detonando diagnóstico cognitivo:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!mounted) return <Skeleton />;

  const altas = mitigaciones?.filter(m => m.impacto_riesgo === 'ALTO') || [];
  const medias = mitigaciones?.filter(m => m.impacto_riesgo === 'MEDIO') || [];
  const bajas = mitigaciones?.filter(m => m.impacto_riesgo === 'BAJO') || [];

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header AI Copilot */}
      <div className="flex items-center justify-between bg-[#141417] border border-[#26262b] rounded-xl p-4 shadow-sm shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#9a3bf1] to-[#3892f3] flex items-center justify-center shadow-[0_0_15px_rgba(154,59,241,0.3)]">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-zinc-100 font-bold text-sm">AI Copilot Tracker</h2>
            <p className="text-zinc-400 text-xs">Gestión automatizada de remediación LOPDP</p>
          </div>
        </div>
        
        <button
          onClick={handleGenerarPlan}
          disabled={isGenerating || isLoading}
          className={`flex items-center px-4 py-2 text-xs font-semibold rounded-lg border transition-all ${
            isGenerating
              ? "bg-[#1e1e24] border-[#26262b] text-zinc-500 cursor-not-allowed"
              : "bg-[#0a0a0c] hover:bg-[#1e1e24] border-[#26262b] hover:border-[#9a3bf1]/50 text-white shadow-sm cursor-pointer"
          }`}
        >
          {isGenerating ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin mr-2" />
              Razonando...
            </>
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 mr-2 text-[#9a3bf1]" />
              Generar Plan Inteligente
            </>
          )}
        </button>
      </div>

      {/* Tablero Kanban */}
      {error ? (
        <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-[#ff1744]/30 bg-[#ff1744]/5 rounded-xl text-[#ff1744] p-6">
          <AlertTriangle className="w-8 h-8 mb-2 opacity-80" />
          <p className="text-sm font-semibold">Error de Conexión</p>
          <p className="text-xs opacity-80 mt-1">No se lograron contactar los endpoints del motor cognitivo.</p>
        </div>
      ) : isLoading && !mitigaciones ? (
        <Skeleton />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1">
          <KanbanColumn 
            titulo="Riesgo ALTO (Crítico)" 
            color="text-[#ff1744]" 
            icono={AlertTriangle} 
            mitigaciones={altas} 
          />
          <KanbanColumn 
            titulo="Riesgo MEDIO (Moderado)" 
            color="text-amber-500" 
            icono={Clock} 
            mitigaciones={medias} 
          />
          <KanbanColumn 
            titulo="Riesgo BAJO (Aceptable)" 
            color="text-[#00c853]" 
            icono={ShieldCheck} 
            mitigaciones={bajas} 
          />
        </div>
      )}
    </div>
  );
}
