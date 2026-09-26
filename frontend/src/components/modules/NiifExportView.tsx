"use client";

import React, { useState } from 'react';
import { Download, FileSpreadsheet } from 'lucide-react';
import { useAuditStore } from "@/store/useAuditStore";

export default function NiifExportView() {
  const { niif18Data, mpmRecords, companyData } = useAuditStore();
  const [isExporting, setIsExporting] = useState(false);

  const cargaUtil = () => JSON.stringify({
    cuentas: niif18Data?.cuentas ?? [],
    mpm: mpmRecords,
    empresa: companyData.razonSocial,
  });

  const descargar = async (ruta: string, nombreArchivo: string) => {
    if (!niif18Data) return alert("No hay datos para exportar.");
    setIsExporting(true);
    try {
      const response = await fetch(`/api/v1/niif18/exportar/${ruta}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: cargaUtil(),
      });
      if (!response.ok) throw new Error("Error en la exportación");
      const url = window.URL.createObjectURL(await response.blob());
      const a = document.createElement('a');
      a.href = url;
      a.download = nombreArchivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("No se pudo generar el reporte.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportExcel = () => descargar("excel", "estado_resultados_niif18.xlsx");
  const handleExportPdf = () => descargar("pdf", "informe_niif18.pdf");
  const handleExportInforme =() => descargar("informe", "informe_niif18.md");

  return (
    <div className="p-6 bg-[#0a0a0c] text-white min-h-screen flex flex-col items-center justify-center">
      <div className="bg-[#141417] p-8 rounded-xl shadow-2xl border border-[#26262b] max-w-lg w-full text-center">
        <h1 className="text-2xl font-bold mb-2 text-blue-400">
          Centro de Exportación Regulatoria NIIF 18
        </h1>
        <p className="text-zinc-400 mb-8 text-sm">
          Genere los reportes financieros inmutables en los formatos requeridos por los reguladores e inversores.
        </p>

        <div className="flex flex-col gap-4">
          <button 
            onClick={handleExportExcel}
            disabled={isExporting}
            className="flex items-center justify-center gap-3 w-full bg-green-700 hover:bg-green-600 text-white py-3 px-4 rounded-lg font-semibold transition-colors disabled:opacity-50"
          >
            <FileSpreadsheet className="w-5 h-5" />
            {isExporting ? "Generando..." : "Paquete de cierre (Excel)"}
          </button>
          
          <button
            onClick={handleExportInforme}
            disabled={isExporting}
            className="flex items-center justify-center gap-3 w-full bg-blue-700 hover:bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold transition-colors disabled:opacity-50"
          >
            <Download className="w-5 h-5" />
            Informe de diagnóstico y recomendaciones (Markdown)
          </button>

          <button
            onClick={handleExportPdf}
            disabled={isExporting}
            className="flex items-center justify-center gap-3 w-full bg-purple-700 hover:bg-purple-600 text-white py-3 px-4 rounded-lg font-semibold transition-colors disabled:opacity-50"
          >
            <Download className="w-5 h-5" />
            Informe de diagnóstico y recomendaciones (PDF)
          </button>

          <button
            disabled
            className="flex items-center justify-center gap-2 bg-[#26262b] text-zinc-500 font-medium py-3 px-6 rounded-lg cursor-not-allowed"
          >
            <Download className="w-5 h-5" />
            Exportar a XBRL (Próximamente)
          </button>
        </div>
        
        <div className="mt-8 pt-4 border-t border-[#26262b] flex justify-end">
          <button
            type="button"
            onClick={() => useAuditStore.getState().setActiveView("niif_doctrina")}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
          >
            Siguiente Paso: Ver Doctrina
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
