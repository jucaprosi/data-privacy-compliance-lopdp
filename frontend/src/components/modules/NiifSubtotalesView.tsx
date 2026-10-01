"use client";

import React from "react";
import { useAuditStore } from "@/store/useAuditStore";
import { Activity, TrendingUp, DollarSign } from "lucide-react";

export default function NiifSubtotalesView() {
  const { niif18Data } = useAuditStore();

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  if (!niif18Data) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500">
        No hay datos de balance. Por favor ingresa a Configuración e ingesta un archivo.
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
      <div className="flex items-center justify-between bg-[#141417] border border-[#26262b] rounded-xl p-6 shadow-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Activity className="w-5 h-5 mr-2 text-[#3892f3]" />
            Árbol de EEFF (Subtotales Mandatorios NIIF 18)
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Los siguientes subtotales han sido calculados de forma estricta según el estándar.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-[#141417] to-[#1e1e24] border border-[#26262b] rounded-xl p-6 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Activity className="w-24 h-24" />
          </div>
          <div className="flex items-center space-x-2 text-zinc-400 mb-4">
            <span className="w-6 h-6 rounded-full bg-[#3892f3]/20 text-[#3892f3] flex items-center justify-center text-xs font-bold">1</span>
            <span className="text-sm font-semibold uppercase tracking-wider text-zinc-300">Resultado Operativo</span>
          </div>
          <div className="text-4xl font-bold text-white mb-2">
            {formatCurrency(niif18Data.subtotales["1_resultado_operativo"])}
          </div>
          <div className="text-xs text-zinc-500 mt-4 border-t border-[#26262b] pt-3">
            Base para medir el desempeño principal de la organización.
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#141417] to-[#1e1e24] border border-[#26262b] rounded-xl p-6 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <TrendingUp className="w-24 h-24" />
          </div>
          <div className="flex items-center space-x-2 text-zinc-400 mb-4">
            <span className="w-6 h-6 rounded-full bg-[#9a3bf1]/20 text-[#9a3bf1] flex items-center justify-center text-xs font-bold">2</span>
            <span className="text-sm font-semibold uppercase tracking-wider text-zinc-300">Antes de Fin. e Imp.</span>
          </div>
          <div className="text-4xl font-bold text-white mb-2">
            {formatCurrency(niif18Data.subtotales["2_resultado_antes_fin_imp"])}
          </div>
          <div className="text-xs text-zinc-500 mt-4 border-t border-[#26262b] pt-3">
            Aísla el efecto del apalancamiento y las tasas impositivas.
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#141417] to-[#1e1e24] border border-[#26262b] rounded-xl p-6 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <DollarSign className="w-24 h-24" />
          </div>
          <div className="flex items-center space-x-2 text-zinc-400 mb-4">
            <span className="w-6 h-6 rounded-full bg-[#00c853]/20 text-[#00c853] flex items-center justify-center text-xs font-bold">3</span>
            <span className="text-sm font-semibold uppercase tracking-wider text-zinc-300">Resultado del Periodo</span>
          </div>
          <div className="text-4xl font-bold text-[#00c853] mb-2">
            {formatCurrency(niif18Data.subtotales["3_resultado_periodo"])}
          </div>
          <div className="text-xs text-zinc-500 mt-4 border-t border-[#26262b] pt-3">
            Línea final después de todos los efectos e impuestos.
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={() => useAuditStore.getState().setActiveView("niif_mpm")}
          className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
        >
          Siguiente Paso: Conciliación MPM
          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
        </button>
      </div>
    </div>
  );
}
