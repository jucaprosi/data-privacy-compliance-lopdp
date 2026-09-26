"use client";

import React, { useState, useEffect } from "react";
import { Server, Globe, AlertTriangle, ShieldCheck, Loader2 } from "lucide-react";

type RolTercero = "ENCARGADO" | "SUBENCARGADO" | "DESTINATARIO";
type NivelProteccion = "ADECUADO" | "ESTANDAR" | "NO_ADECUADO";

interface Tercero {
  id: string;
  nombre: string;
  rol: RolTercero;
  pais: string;
  nivelProteccion: NivelProteccion;
  clausulasFirmadas: boolean;
  auditoriaAlDia: boolean;
}

interface TerceroResponse {
  id: string;
  nombre: string;
  rol: RolTercero;
  pais: string;
  nivel_proteccion: NivelProteccion;
  clausulas_firmadas: boolean;
  auditoria_al_dia: boolean;
}

export default function TercerosModule() {
  const [terceros, setTerceros] = useState<Tercero[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTerceros = async () => {
      try {
        const res = await fetch("/api/v1/terceros", {
          headers: {
            "Authorization": "Bearer jwt_mock_tenant_123",
          },
        });
        if (!res.ok) throw new Error("Error al obtener transferencias y terceros");
        const data = await res.json() as TerceroResponse[];
        
        // Mapeo snake_case a camelCase
        const mappedData: Tercero[] = data.map((item) => ({
          id: item.id,
          nombre: item.nombre,
          rol: item.rol,
          pais: item.pais,
          nivelProteccion: item.nivel_proteccion,
          clausulasFirmadas: item.clausulas_firmadas,
          auditoriaAlDia: item.auditoria_al_dia,
        }));
        
        setTerceros(mappedData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    };

    fetchTerceros();
  }, []);

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[#26262b]">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <Server className="w-5 h-5 mr-2 text-[#9a3bf1]" />
          Terceros, Encargados y Transferencias
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Inventario de proveedores, flujo transfronterizo de datos y Cláusulas Contractuales Tipo (SCC).
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <Loader2 className="w-8 h-8 text-[#9a3bf1] animate-spin" />
          <span className="text-sm text-zinc-400 font-mono">Cargando terceros desde FastAPI...</span>
        </div>
      ) : error ? (
        <div className="p-4 bg-[#ff1744]/10 border border-[#ff1744]/30 rounded-xl flex items-center text-[#ff1744] text-sm">
          <AlertTriangle className="w-5 h-5 mr-3" />
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {terceros.length === 0 && (
             <div className="p-8 text-center text-zinc-500 text-sm border border-dashed border-[#26262b] rounded-xl">
               No hay terceros ni transferencias registradas.
             </div>
          )}
          {terceros.map((t) => {
            const isRiesgoAlto = t.nivelProteccion === "NO_ADECUADO" && !t.clausulasFirmadas;
            return (
              <div key={t.id} className={`p-4 bg-[#141417] border ${isRiesgoAlto ? 'border-[#ff1744]/50' : 'border-[#26262b]'} rounded-xl flex justify-between items-center transition-colors`}>
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-lg border ${isRiesgoAlto ? 'text-[#ff1744] bg-[#ff1744]/10 border-[#ff1744]/30' : 'text-[#9a3bf1] bg-[#9a3bf1]/10 border-[#9a3bf1]/30'}`}>
                    {isRiesgoAlto ? <AlertTriangle className="w-5 h-5" /> : <Globe className="w-5 h-5" />}
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-zinc-200">{t.nombre}</h4>
                    <div className="text-xs text-zinc-500 font-mono mt-1">
                      {t.rol} | País: {t.pais}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <div className="text-xs text-zinc-400">Garantías (SCC)</div>
                    <div className={`text-sm font-bold flex items-center justify-end mt-0.5 ${t.clausulasFirmadas ? "text-[#00c853]" : "text-amber-400"}`}>
                      {t.clausulasFirmadas ? <ShieldCheck className="w-3.5 h-3.5 mr-1" /> : <AlertTriangle className="w-3.5 h-3.5 mr-1" />}
                      {t.clausulasFirmadas ? "Firmadas" : "Pendientes"}
                    </div>
                  </div>
                  {isRiesgoAlto && (
                    <div className="px-3 py-1 bg-[#ff1744]/20 text-[#ff1744] border border-[#ff1744]/30 rounded text-xs font-bold">
                      RIESGO TRANSFERENCIA ILEGAL
                    </div>
                  )}
                  <button className="px-3 py-1.5 bg-[#26262b] hover:bg-[#9a3bf1]/20 text-zinc-200 hover:text-[#9a3bf1] border border-[#26262b] hover:border-[#9a3bf1]/50 rounded text-xs font-medium transition-colors cursor-pointer">
                    Ver Ficha
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
