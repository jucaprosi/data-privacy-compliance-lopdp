"use client";

import React, { useState } from 'react';
import { PieChart, FileText, Calculator } from 'lucide-react';
import { useAuditStore, MpmRecord } from "@/store/useAuditStore";

export default function NiifMpmView() {
  const { niif18Data, mpmRecords, setMpmRecords } = useAuditStore();
  const [nombre, setNombre] = useState('');
  const [subtotalBase, setSubtotalBase] = useState('1. Resultado Operativo');
  const [ajuste, setAjuste] = useState('');
  const [justificacion, setJustificacion] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const subtotales = niif18Data?.subtotales || {
    "1_resultado_operativo": 0,
    "2_resultado_antes_fin_imp": 0,
    "3_resultado_periodo": 0
  };

  const getValorBase = () => {
    if (subtotalBase.startsWith('1')) return subtotales["1_resultado_operativo"];
    if (subtotalBase.startsWith('2')) return subtotales["2_resultado_antes_fin_imp"];
    return subtotales["3_resultado_periodo"];
  };

  const handleGuardarMpm = async () => {
    if (!nombre || !ajuste || !justificacion.trim()) return alert("Completa el nombre, el ajuste y la justificación (exigida por la NIIF 18)");
    setIsSaving(true);
    
    try {
      const response = await fetch("/api/v1/niif18/mpm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre,
          subtotal_base: subtotalBase,
          valor_base: getValorBase(),
          ajuste: parseFloat(ajuste),
          justificacion
        })
      });

      if (!response.ok) throw new Error("Error guardando MPM");
      const nuevoMpm = await response.json();
      
      setMpmRecords([...mpmRecords, nuevoMpm]);
      setNombre('');
      setAjuste('');
      setJustificacion('');
    } catch (err) {
      console.error(err);
      alert("Error en el cálculo del MPM");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 bg-[#0a0a0c] text-white min-h-screen">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <PieChart className="w-6 h-6 text-blue-500" />
        Gestión de Medidas de Rendimiento de la Gerencia (MPM)
      </h1>

      <div className="bg-[#141417] p-6 rounded-lg shadow-lg mb-8 border border-[#26262b]">
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-zinc-400">Nombre del MPM</label>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                className="w-full bg-[#0a0a0c] border border-zinc-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                placeholder="Ej. EBITDA Ajustado"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-zinc-400">Subtotal de Anclaje</label>
              <select 
                value={subtotalBase}
                onChange={(e) => setSubtotalBase(e.target.value)}
                className="w-full bg-[#0a0a0c] border border-zinc-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="1. Resultado Operativo">Resultado Operativo ({formatCurrency(subtotales["1_resultado_operativo"])})</option>
                <option value="2. Antes de Fin. e Imp.">Resultado antes de Fin. e Imp. ({formatCurrency(subtotales["2_resultado_antes_fin_imp"])})</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-zinc-400 flex items-center gap-2">
                <Calculator className="w-4 h-4" />
                Valor del Ajuste (Impacto en P&L)
              </label>
              <input
                type="number"
                value={ajuste}
                onChange={(e) => setAjuste(e.target.value)}
                className="w-full bg-[#0a0a0c] border border-zinc-700 rounded p-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                placeholder="Ej. 1200000"
              />
            </div>
          </div>
          
          <div className="flex flex-col">
            <label className="block text-sm font-medium mb-1 text-zinc-400 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Justificación Doctrinal
            </label>
            <textarea
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              className="w-full flex-grow bg-[#0a0a0c] border border-zinc-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
              placeholder="Explique cómo este MPM proporciona información útil a los inversores..."
            />
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={handleGuardarMpm}
                disabled={isSaving}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded transition-colors disabled:opacity-50"
              >
                {isSaving ? "Calculando Fiscal..." : "Añadir Ajuste MPM"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-[#141417] p-6 rounded-lg shadow-lg border border-[#26262b]">
        <h2 className="text-xl font-semibold mb-4 border-b border-zinc-800 pb-2">Registro de Medidas (Conciliación)</h2>
        {mpmRecords.length === 0 ? (
          <p className="text-zinc-500 text-sm">No se han registrado medidas MPM.</p>
        ) : (
          <div className="space-y-4">
            {mpmRecords.map((rec: MpmRecord, i: number) => (
              <div key={i} className="bg-[#0a0a0c] border border-zinc-800 rounded-lg p-4 grid grid-cols-5 gap-4 items-center">
                <div className="col-span-2">
                  <h4 className="font-bold text-white">{rec.nombre}</h4>
                  <p className="text-xs text-zinc-500 truncate">{rec.justificacion}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] uppercase text-zinc-500">Valor Base</p>
                  <p className="font-mono text-sm text-zinc-300">{formatCurrency(rec.valor_base)}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] uppercase text-zinc-500">Ajuste (Neto -25%)</p>
                  <p className="font-mono text-sm text-yellow-500">+{formatCurrency(rec.ajuste - rec.efecto_fiscal)}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] uppercase text-zinc-500">Total MPM</p>
                  <p className="font-mono text-base font-bold text-blue-400">{formatCurrency(rec.total_mpm)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-end mt-6">
        <button
          type="button"
          onClick={() => useAuditStore.getState().setActiveView("niif_diagnostico")}
          className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
        >
          Siguiente Paso: Exportar
          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
        </button>
      </div>
    </div>
  );
}
