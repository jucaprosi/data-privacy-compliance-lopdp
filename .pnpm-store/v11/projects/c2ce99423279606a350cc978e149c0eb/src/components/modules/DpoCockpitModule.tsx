"use client";

import React, { useState, useEffect } from "react";
import { FileCheck, Shield, CheckCheck, Clock, AlertOctagon } from "lucide-react";
import { DictamenDPO } from "@/types";
import { getBitacoraDPO } from "@/lib/api";

export default function DpoCockpitModule() {
  const [bitacora, setBitacora] = useState<DictamenDPO[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarBitacora();
  }, []);

  const cargarBitacora = async () => {
    setCargando(true);
    try {
      const data = await getBitacoraDPO();
      setBitacora(data);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-zinc-800">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <FileCheck className="w-5 h-5 mr-2 text-sky-400" /> Cockpit del DPD/DPO · Bitácora Inviolable
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Supervisión independiente y registro histórico de asesorías con acuse de recibo directivo (Art. 48 LOPDP).
        </p>
      </div>

      {/* Banner SoD */}
      <div className="bg-sky-950/40 border border-sky-800/60 rounded-xl p-4 flex items-start space-x-3 text-xs">
        <Shield className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-sky-300">Garantía de Segregación de Funciones (SoD):</span>
          <p className="text-zinc-300 mt-0.5">
            Bajo el invariante constitucional <code className="font-mono bg-sky-900/50 px-1 py-0.5 rounded text-sky-200">INV_LOPDP_DPO_INDEPENDENCE</code>, 
            el DPO opera con independencia consultiva: no puede auto-aprobar políticas operativas ni ser juez y parte en remediaciones CAPA.
          </p>
        </div>
      </div>

      {/* Bitácora Timeline */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
          Historial Cronológico de Dictámenes y Advertencias
        </h3>

        {cargando ? (
          <div className="p-8 text-center text-zinc-500 text-xs">Cargando bitácora notarial...</div>
        ) : bitacora.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-xs">No hay dictámenes asentados en la bitácora.</div>
        ) : (
          <div className="space-y-3">
            {bitacora.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-lg bg-zinc-950/70 border border-zinc-800 hover:border-zinc-700 transition space-y-2 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-zinc-400 font-bold">{item.id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.tipo === "ADVERTENCIA_RIESGO"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : "bg-sky-950 text-sky-300 border border-sky-800"
                      }`}
                    >
                      {item.tipo}
                    </span>
                  </div>
                  <div className="flex items-center text-[11px] text-zinc-500">
                    <Clock className="w-3.5 h-3.5 mr-1" />
                    {item.fecha_emision ? new Date(item.fecha_emision).toLocaleDateString() : "Reciente"}
                  </div>
                </div>

                <div className="font-bold text-zinc-200 text-sm">{item.asunto}</div>
                <div className="text-[11px] text-zinc-400 font-mono">Referencia legal: {item.referencia_normativa}</div>
                <p className="text-zinc-300 leading-relaxed bg-zinc-900/60 p-2.5 rounded border border-zinc-800/80">
                  {item.cuerpo}
                </p>

                <div className="pt-2 flex items-center justify-between border-t border-zinc-900 text-[11px]">
                  <span className="text-zinc-500 italic">Doctrina: Carácter consultivo (No vinculante por ley)</span>
                  <div>
                    {item.acuse_recibo_alta_direccion ? (
                      <span className="text-emerald-400 font-semibold flex items-center">
                        <CheckCheck className="w-3.5 h-3.5 mr-1" /> Acuse de Recibo Directivo Asentado
                      </span>
                    ) : (
                      <span className="text-amber-400 font-medium flex items-center">
                        <AlertOctagon className="w-3.5 h-3.5 mr-1" /> Pendiente Acuse de Alta Dirección
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
