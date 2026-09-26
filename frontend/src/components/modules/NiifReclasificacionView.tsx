"use client";

import React, { useState } from "react";
import { useAuditStore, CuentaNIIF } from "@/store/useAuditStore";

const CATEGORIAS_NIIF18 = [
  "0. Balance General (No P&L / Excluir)",
  "1. Operación (Ingresos / Gastos Operativos)",
  "2. Inversión (Ingresos / Gastos por Inversiones)",
  "3. Financiación (Costos / Pasivos Financieros)",
  "4. Impuestos a las Ganancias",
  "5. Operaciones Discontinuadas"
];

export default function NiifReclasificacionView() {
  const { niif18Data, setNiif18Data } = useAuditStore();
  const [isUpdating, setIsUpdating] = useState(false);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const handleCategoriaChange = async (index: number, nuevaCategoria: string) => {
    if (!niif18Data) return;
    setIsUpdating(true);
    
    // Clonar las cuentas y modificar la específica
    const cuentasActualizadas = [...niif18Data.cuentas];
    cuentasActualizadas[index] = { ...cuentasActualizadas[index], categoria: nuevaCategoria };

    try {
      const response = await fetch("/api/v1/niif18/recalcular-subtotales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cuentasActualizadas),
      });

      if (!response.ok) throw new Error("Error recalculando NIIF 18");
      
      const resData = await response.json();
      
      setNiif18Data({
        ...niif18Data,
        subtotales: resData.subtotales,
        cuentas: resData.cuentas,
        diagnostico: resData.diagnostico,
        indicadores: resData.indicadores,
      });
    } catch (error) {
      console.error(error);
      alert("No se pudo recalcular la matriz.");
    } finally {
      setIsUpdating(false);
    }
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
      <div className="bg-[#141417] border border-[#26262b] rounded-xl overflow-hidden shadow-md">
        <div className="p-5 border-b border-[#26262b] flex items-center justify-between">
          <div>
            <h3 className="font-bold text-white text-lg">Matriz de Reclasificación NIIF 18</h3>
            <p className="text-xs text-zinc-400 mt-1">
              Las cuentas han sido mapeadas usando heurísticas y modelos matemáticos a las categorías mandatorias.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {isUpdating && <span className="text-xs text-blue-400 animate-pulse">Recalculando P&L...</span>}
            <div className="text-xs text-zinc-500 font-mono bg-[#0a0a0c] px-3 py-1.5 rounded-lg border border-[#26262b]">
              Confianza IA: <span className="text-[#00c853] font-bold">{niif18Data.inferencia_columnas?.confianza_porcentaje?.toFixed(1) || 100}%</span>
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-left text-sm text-zinc-400 relative">
            <thead className="bg-[#0a0a0c] text-xs uppercase font-semibold text-zinc-500 sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="px-5 py-4 border-b border-[#26262b]">Cuenta</th>
                <th className="px-5 py-4 border-b border-[#26262b]">Descripción</th>
                <th className="px-5 py-4 border-b border-[#26262b]">Categoría NIIF 18</th>
                <th className="px-5 py-4 border-b border-[#26262b] text-right">Saldo Original</th>
                <th className="px-5 py-4 border-b border-[#26262b] text-right">P&L Neto</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26262b]">
              {niif18Data.cuentas.map((cta: CuentaNIIF, i: number) => (
                <tr key={i} className="hover:bg-[#1e1e24] transition-colors">
                  <td className="px-5 py-3 font-mono text-xs">{cta.cuenta}</td>
                  <td className="px-5 py-3 text-zinc-300">{cta.descripcion}</td>
                  <td className="px-5 py-3">
                    <select 
                      value={cta.categoria}
                      onChange={(e) => handleCategoriaChange(i, e.target.value)}
                      disabled={isUpdating}
                      className="bg-[#0a0a0c] border border-[#26262b] text-xs text-zinc-300 rounded px-2 py-1.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 w-full max-w-[250px]"
                    >
                      {CATEGORIAS_NIIF18.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-5 py-3 text-right font-mono text-xs">{formatCurrency(cta.saldo_original)}</td>
                  <td className={`px-5 py-3 text-right font-mono text-xs font-semibold ${cta.pl_neto < 0 ? "text-red-400" : "text-green-400"}`}>
                    {formatCurrency(cta.pl_neto)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Enlace al siguiente proceso */}
        <div className="p-4 border-t border-[#26262b] flex justify-end bg-[#0a0a0c]">
          <button
            type="button"
            onClick={() => useAuditStore.getState().setActiveView("niif_subtotales")}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
          >
            Siguiente Paso: Árbol de Subtotales
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
