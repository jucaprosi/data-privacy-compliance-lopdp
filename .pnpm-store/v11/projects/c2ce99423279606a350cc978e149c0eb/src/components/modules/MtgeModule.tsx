"use client";

import React, { useState, useEffect } from "react";
import { Scale, Calculator, AlertTriangle, CheckCircle, ShieldAlert } from "lucide-react";

export default function MtgeModule() {
  const [params, setParams] = useState({
    numero_titulares: 25000,
    datos_sensibles_continuos: false,
    alcance_nacional: false,
    nuevas_tecnologias_ia: false,
  });

  const [puntaje, setPuntaje] = useState(0);
  const [esGranEscala, setEsGranEscala] = useState(false);

  // Semáforo en tiempo real
  useEffect(() => {
    let pts = 0;
    if (params.numero_titulares > 50000) pts += 50;
    else if (params.numero_titulares > 10000) pts += 20;

    if (params.datos_sensibles_continuos) pts += 40;
    if (params.alcance_nacional) pts += 25;
    if (params.nuevas_tecnologias_ia) pts += 35; // Novedad tecnológica sube el riesgo

    setPuntaje(pts);
    setEsGranEscala(pts >= 100);
  }, [params]);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="pb-4 border-b border-[#26262b] shrink-0">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <Scale className="w-5 h-5 mr-2 text-transparent bg-clip-text bg-gradient-to-r from-[#9a3bf1] to-[#3892f3] bg-gradient-to-r from-[#9a3bf1] to-[#3892f3]" /> 
          Matriz MTGE · Tratamientos a Gran Escala
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Calculadora visual de riesgo bajo Resolución SPDP-SPD-2026-0005-R. Determina obligación de EIPD y DPO.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controles de Variables (Sliders y Toggles) */}
        <div className="lg:col-span-2 bg-[#141417] border border-[#26262b] rounded-xl p-6 space-y-6 shadow-xl">
          <div className="font-bold text-zinc-200 flex items-center pb-3 border-b border-[#26262b] text-sm uppercase tracking-wider">
            <Calculator className="w-4 h-4 mr-2 text-[#9a3bf1]" /> Variables de Ponderación Reactivas
          </div>

          <div className="space-y-6">
            {/* Slider de Volumen */}
            <div className="space-y-3 p-4 rounded-lg bg-[#0a0a0c] border border-[#26262b]">
              <div className="flex justify-between items-end">
                <label className="text-xs font-semibold text-zinc-300">
                  Volumen Estimado de Titulares (Data Subjects)
                </label>
                <span className="text-lg font-mono font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#9a3bf1] to-[#3892f3]">
                  {params.numero_titulares.toLocaleString("es-EC")}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="200000"
                step="5000"
                value={params.numero_titulares}
                onChange={(e) => setParams({ ...params, numero_titulares: Number(e.target.value) })}
                className="w-full h-1.5 bg-[#26262b] rounded-lg appearance-none cursor-pointer accent-[#9a3bf1]"
              />
              <div className="flex justify-between text-[10px] text-zinc-500 font-mono">
                <span>0</span>
                <span>Umbral Crítico: &gt;50K (+50 pts)</span>
                <span>200K+</span>
              </div>
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ToggleCard
                label="Datos Sensibles y Continuos"
                desc="Tratamiento de categorías especiales con frecuencia permanente (+40 pts)"
                checked={params.datos_sensibles_continuos}
                onChange={(c) => setParams({ ...params, datos_sensibles_continuos: c })}
              />
              <ToggleCard
                label="Cobertura Nacional"
                desc="El alcance del tratamiento afecta a sujetos a nivel país (+25 pts)"
                checked={params.alcance_nacional}
                onChange={(c) => setParams({ ...params, alcance_nacional: c })}
              />
              <ToggleCard
                label="Nuevas Tecnologías e IA"
                desc="Uso de machine learning, perfilamiento o tecnologías invasivas (+35 pts)"
                checked={params.nuevas_tecnologias_ia}
                onChange={(c) => setParams({ ...params, nuevas_tecnologias_ia: c })}
              />
            </div>
          </div>
        </div>

        {/* Panel de Veredicto (Semáforo en tiempo real) */}
        <div className="bg-[#141417] border border-[#26262b] rounded-xl p-6 flex flex-col justify-between shadow-xl relative overflow-hidden">
          {/* Fondo gradiente condicional */}
          <div className={`absolute inset-0 opacity-10 transition-colors duration-500 ${esGranEscala ? "bg-[#ff1744]" : "bg-[#00c853]"}`} />
          
          <div className="relative z-10">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-4 flex items-center justify-between border-b border-[#26262b] pb-2">
              <span>Semáforo de Riesgo (Tiempo Real)</span>
              <span className="font-mono text-zinc-500">REQ-MTGE-01</span>
            </div>
            
            <div className="space-y-6">
              <div className="text-center p-6 rounded-xl bg-[#0a0a0c] border border-[#26262b] shadow-inner">
                <div className="text-5xl font-black font-mono tracking-tighter mb-1 transition-colors duration-300">
                  <span className={esGranEscala ? "text-[#ff1744]" : "text-[#00c853]"}>
                    {puntaje}
                  </span>
                  <span className="text-lg font-normal text-zinc-600"> / 100</span>
                </div>
                <div className="mt-4">
                  {esGranEscala ? (
                    <span className="px-3 py-1.5 bg-[#ff1744]/15 text-[#ff1744] border border-[#ff1744]/40 rounded-lg text-xs font-bold inline-flex items-center uppercase tracking-wide">
                      <AlertTriangle className="w-4 h-4 mr-1.5" /> Gran Escala Detectada
                    </span>
                  ) : (
                    <span className="px-3 py-1.5 bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/40 rounded-lg text-xs font-bold inline-flex items-center uppercase tracking-wide">
                      <CheckCircle className="w-4 h-4 mr-1.5" /> Tratamiento Ordinario
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-xs font-medium">
                <div className="flex justify-between p-3 rounded-lg bg-[#0a0a0c] border border-[#26262b]">
                  <span className="text-zinc-400">DPO Obligatorio (Art. 48):</span>
                  <span className={esGranEscala ? "text-[#ff1744] font-bold animate-pulse" : "text-zinc-500"}>
                    {esGranEscala ? "REQUERIDO INMEDIATO" : "Facultativo"}
                  </span>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-[#0a0a0c] border border-[#26262b]">
                  <span className="text-zinc-400">EIPD Previa:</span>
                  <span className={esGranEscala ? "text-[#ff1744] font-bold animate-pulse" : "text-zinc-500"}>
                    {esGranEscala ? "IMPERATIVA" : "Según Evaluación"}
                  </span>
                </div>
              </div>

              <p className="text-[10px] text-zinc-500 italic leading-relaxed border-l-2 border-[#3892f3] pl-3">
                {esGranEscala
                  ? "La combinación de factores sobrepasa el umbral legal de 100 puntos. El sistema asienta el flag de EIPD forzosa irreversible para esta actividad."
                  : "El volumen y sensibilidad actual se mantienen dentro del margen de tratamiento ordinario. No se detonan controles críticos perentorios."}
              </p>
            </div>
          </div>
          <div className="pt-4 border-t border-[#26262b] text-[10px] text-zinc-500 flex items-center mt-4 relative z-10">
            <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-[#3892f3]" />
            Cualquier cambio se refleja inmediatamente en el RAT.
          </div>
        </div>
      </div>
    </div>
  );
}

function ToggleCard({ label, desc, checked, onChange }: { label: string, desc: string, checked: boolean, onChange: (c: boolean) => void }) {
  return (
    <div
      onClick={() => onChange(!checked)}
      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
        checked 
          ? "bg-gradient-to-br from-[#9a3bf1]/10 to-[#3892f3]/10 border-[#9a3bf1]/50 shadow-sm shadow-[#9a3bf1]/10" 
          : "bg-[#0a0a0c] border-[#26262b] hover:border-[#3a3a42]"
      }`}
    >
      <div className="flex items-start justify-between">
        <span className={`text-xs font-bold ${checked ? "text-zinc-100" : "text-zinc-400"}`}>{label}</span>
        <div className={`w-8 h-4 rounded-full flex items-center p-0.5 transition-colors ${checked ? "bg-[#9a3bf1]" : "bg-zinc-700"}`}>
          <div className={`w-3 h-3 bg-white rounded-full transition-transform ${checked ? "translate-x-4 shadow-sm" : "translate-x-0"}`} />
        </div>
      </div>
      <p className="text-[10px] text-zinc-500 leading-snug">{desc}</p>
    </div>
  );
}
