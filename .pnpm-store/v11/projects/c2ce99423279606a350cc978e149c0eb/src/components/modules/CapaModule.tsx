"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle, UserCheck } from "lucide-react";



import { TicketCAPA } from "@/types";
import { getTicketsCAPA } from "@/lib/api";

export default function CapaModule() {
  const [tickets, setTickets] = useState<TicketCAPA[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarTickets();
  }, []);

  const cargarTickets = async () => {
    setCargando(true);
    try {
      const data = await getTicketsCAPA();
      setTickets(data);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-zinc-800">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2 text-rose-400" /> Auditoría & Acciones Correctivas (CAPA)
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Gestión de no conformidades, análisis de causa raíz y verificación independiente con estricta Segregación de Funciones (SoD).
        </p>
      </div>

      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="p-4 bg-zinc-950/60 border-b border-zinc-800 flex justify-between items-center text-xs">
          <span className="font-semibold text-zinc-300">Plan de Acción y Tickets Abiertos</span>
          <span className="text-amber-400 font-medium">Invariante: Auto-verificación prohibida</span>
        </div>

        <div className="divide-y divide-zinc-800/50">
          {cargando ? (
            <div className="p-8 text-center text-zinc-500 text-xs">Cargando tickets de auditoría...</div>
          ) : tickets.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-xs">No hay no conformidades abiertas.</div>
          ) : (
            tickets.map((t) => (
              <div key={t.id} className="p-4 hover:bg-zinc-800/20 transition space-y-2 text-xs">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-zinc-400 font-bold">{t.id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">
                        {t.severidad}
                      </span>
                      <span className="text-[11px] text-zinc-500">Control: {t.control_id}</span>
                    </div>
                    <div className="font-semibold text-zinc-200 text-sm">{t.descripcion_hallazgo}</div>
                  </div>
                  <span className="px-2 py-1 rounded text-[11px] font-medium bg-amber-950 text-amber-300 border border-amber-800">
                    {t.estado}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-zinc-950/60 p-3 rounded-lg border border-zinc-800">
                  <div>
                    <span className="text-[10px] text-zinc-500 block uppercase font-bold">Causa Raíz</span>
                    <span className="text-zinc-300">{t.causa_raiz}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-500 block uppercase font-bold">Plan de Remediación</span>
                    <span className="text-zinc-300">{t.accion_correctiva}</span>
                  </div>
                </div>

                <div className="flex justify-between items-center text-[11px] text-zinc-400 pt-1">
                  <span>Dueño Implementador: <strong className="text-zinc-200">{t.responsable_implementacion_id}</strong></span>
                  <span className="text-emerald-400 font-medium flex items-center">
                    <UserCheck className="w-3.5 h-3.5 mr-1" /> Requiere Auditor Independiente para Cierre
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
