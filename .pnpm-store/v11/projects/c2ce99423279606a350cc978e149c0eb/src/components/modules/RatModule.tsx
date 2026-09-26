"use client";

import React, { useState, useEffect } from "react";
import { FileSpreadsheet, Plus, Database } from "lucide-react";


import { ActividadRAT } from "@/types";
import { getActividadesRAT, crearActividadRAT } from "@/lib/api";

export default function RatModule() {
  const [actividades, setActividades] = useState<ActividadRAT[]>([]);
  const [cargando, setCargando] = useState(true);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [nueva, setNueva] = useState<ActividadRAT>({
    codigo: "RAT-OPER-001",
    nombre: "Facturación Electrónica y Pagos",
    area_responsable: "Contabilidad y Finanzas",
    finalidad: "Emisión de comprobantes SRI y cobro de cartera",
    base_legal: "OBLIGACION_LEGAL",
    categorias_titulares: ["CLIENTES", "PROVEEDORES"],
    datos_sensibles: false,
    volumen_titulares_estimado: 12000,
    transferencia_internacional: false,
    requiere_eipd: false,
    es_gran_escala: false,
  });

  useEffect(() => {
    cargarActividades();
  }, []);

  const cargarActividades = async () => {
    setCargando(true);
    try {
      const data = await getActividadesRAT();
      setActividades(data);
    } finally {
      setCargando(false);
    }
  };

  const guardarActividad = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const guardada = await crearActividadRAT(nueva);
      setActividades([...actividades, guardada]);
      setModalAbierto(false);
    } catch (err) {
      console.error("Error guardando en el RAT:", err);
      alert("Error guardando en el RAT");
    }

  };

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center pb-4 border-b border-zinc-800">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center">
            <FileSpreadsheet className="w-5 h-5 mr-2 text-emerald-400" /> RAT Maestro (Compliance Graph SSOT)
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Registro unificado de actividades de tratamiento (Art. 41 LOPDP). Fuente única de verdad.
          </p>
        </div>
        <button
          onClick={() => setModalAbierto(true)}
          className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg flex items-center shadow-lg transition"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Nueva Actividad
        </button>
      </div>

      {/* Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-zinc-950/70 text-zinc-400 border-b border-zinc-800 font-semibold">
            <tr>
              <th className="p-3">Código</th>
              <th className="p-3">Actividad / Tratamiento</th>
              <th className="p-3">Área</th>
              <th className="p-3">Base Legal</th>
              <th className="p-3 text-center">Titulares Est.</th>
              <th className="p-3 text-center">Datos Sensibles</th>
              <th className="p-3 text-center">Gran Escala</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/40">
            {cargando ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-zinc-500">
                  Cargando inventario maestro...
                </td>
              </tr>
            ) : actividades.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-zinc-500">
                  No hay actividades registradas en el RAT.
                </td>
              </tr>
            ) : (
              actividades.map((act) => (
                <tr key={act.codigo} className="hover:bg-zinc-800/30 transition">
                  <td className="p-3 font-mono text-zinc-400 font-bold">{act.codigo}</td>
                  <td className="p-3">
                    <div className="font-semibold text-zinc-200">{act.nombre}</div>
                    <div className="text-[11px] text-zinc-500 line-clamp-1">{act.finalidad}</div>
                  </td>
                  <td className="p-3">{act.area_responsable}</td>
                  <td className="p-3">
                    <span className="bg-zinc-800 px-2 py-0.5 rounded text-[11px] font-mono text-emerald-400 border border-zinc-700">
                      {act.base_legal}
                    </span>
                  </td>
                  <td className="p-3 text-center font-mono">{act.volumen_titulares_estimado.toLocaleString()}</td>
                  <td className="p-3 text-center">
                    {act.datos_sensibles ? (
                      <span className="text-rose-400 font-semibold">SÍ</span>
                    ) : (
                      <span className="text-zinc-600">NO</span>
                    )}
                  </td>
                  <td className="p-3 text-center">
                    {act.es_gran_escala ? (
                      <span className="bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded text-[10px] font-bold">
                        MTGE
                      </span>
                    ) : (
                      <span className="text-zinc-500 text-[11px]">Estándar</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Nueva Actividad */}
      {modalAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 max-w-lg w-full text-zinc-100 shadow-2xl">
            <h3 className="text-sm font-bold text-emerald-400 mb-3 flex items-center">
              <Database className="w-4 h-4 mr-2" /> Registrar Nueva Actividad de Tratamiento
            </h3>
            <form onSubmit={guardarActividad} className="space-y-3 text-xs">
              <div>
                <label className="block text-zinc-400 mb-1">Código Identificador</label>
                <input
                  type="text"
                  value={nueva.codigo}
                  onChange={(e) => setNueva({ ...nueva, codigo: e.target.value })}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-zinc-200"
                  required
                />
              </div>
              <div>
                <label className="block text-zinc-400 mb-1">Nombre del Tratamiento</label>
                <input
                  type="text"
                  value={nueva.nombre}
                  onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-zinc-200"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-zinc-400 mb-1">Área Custodia</label>
                  <input
                    type="text"
                    value={nueva.area_responsable}
                    onChange={(e) => setNueva({ ...nueva, area_responsable: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-zinc-200"
                    required
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">Base de Legitimación</label>
                  <select
                    value={nueva.base_legal}
                    onChange={(e) => setNueva({ ...nueva, base_legal: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-zinc-200"
                  >
                    <option value="CONSENTIMIENTO">CONSENTIMIENTO</option>
                    <option value="OBLIGACION_LEGAL">OBLIGACION_LEGAL</option>
                    <option value="CUMPLIMIENTO_CONTRATO">CUMPLIMIENTO_CONTRATO</option>
                    <option value="INTERES_LEGITIMO">INTERES_LEGITIMO</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-zinc-400 mb-1">Finalidad Unívoca</label>
                <textarea
                  value={nueva.finalidad}
                  onChange={(e) => setNueva({ ...nueva, finalidad: e.target.value })}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-zinc-200 h-16"
                  required
                />
              </div>
              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={nueva.datos_sensibles}
                    onChange={(e) => setNueva({ ...nueva, datos_sensibles: e.target.checked })}
                    className="rounded border-zinc-700 text-emerald-500"
                  />
                  <span className="text-zinc-300">Trata datos sensibles</span>
                </label>
                <div className="space-x-2">
                  <button
                    type="button"
                    onClick={() => setModalAbierto(false)}
                    className="px-3 py-1.5 bg-zinc-800 text-zinc-400 rounded hover:bg-zinc-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-emerald-600 text-white rounded font-semibold hover:bg-emerald-500"
                  >
                    Guardar en RAT
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
