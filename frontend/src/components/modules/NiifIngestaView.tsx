"use client";

import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileSpreadsheet, ArrowRight, AlertCircle, CheckCircle } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";

export default function NiifIngestaView() {
  const { archivosCargados, setNiif18Data, setActiveView } = useAuditStore();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [mensajePoda, setMensajePoda] = useState<string | null>(null);
  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Sobrescribir el estado local
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: unknown[]) => {
    if (rejectedFiles.length > 0) {
      setErrorMessage("Algunos archivos no tienen un formato válido (.csv, .xlsx).");
    } else {
      setErrorMessage(null);
    }

    if (acceptedFiles.length > 0) {
      // Guardar localmente solo para esta ingesta
      setLocalFiles(acceptedFiles);
      useAuditStore.setState({ archivosCargados: acceptedFiles });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1, // Solo un balance a la vez
  });

  const handleProcesar = async () => {
    const file = archivosCargados.length > 0 ? archivosCargados[0] : null;
    if (!file) {
      setErrorMessage("Debes cargar un Balance de Comprobación (.xlsx, .csv).");
      return;
    }

    setIsProcessing(true);
    setMensajePoda("Procesando Balance con modelos matemáticos NIIF 18...");
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/niif18/procesar-balance", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Error al procesar el archivo en el servidor.");
      }

      const data = await res.json();
      setNiif18Data(data);
      setActiveView("niif_reclasificacion");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(String(err));
      }
    } finally {
      setIsProcessing(false);
      setMensajePoda(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10 animate-in fade-in zoom-in-95 duration-300">
      <div className="flex items-center justify-between bg-[#141417] border border-[#26262b] rounded-xl p-6 shadow-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <UploadCloud className="w-5 h-5 mr-2 text-[#00c853]" />
            Ingesta de Balance NIIF 18
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Sube el Balance de Comprobación en formato Excel o CSV. El motor mapeará las cuentas automáticamente a las categorías mandatorias.
          </p>
        </div>
      </div>

      <div className="bg-[#141417] border border-[#26262b] rounded-xl p-6 shadow-sm space-y-4">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-4 ${
            isDragActive
              ? "border-[#00c853] bg-[#00c853]/10"
              : errorMessage
              ? "border-[#ff1744] bg-[#ff1744]/5"
              : "border-[#26262b] hover:border-[#00c853]/60 bg-[#0a0a0c]"
          }`}
        >
          <input {...getInputProps()} />
          <div className="w-16 h-16 rounded-full bg-[#1e1e24] flex items-center justify-center text-zinc-300 shadow-md">
            <FileSpreadsheet className="w-8 h-8 text-[#00c853]" />
          </div>
          <div>
            <span className="text-sm font-semibold text-white block">
              Haz clic para seleccionar o arrastra el Balance aquí
            </span>
            <p className="text-xs text-zinc-400 mt-1">
              Formatos soportados: .xlsx, .csv
            </p>
          </div>
        </div>

        {errorMessage && (
          <div className="flex items-center space-x-2.5 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[#ff1744] text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {localFiles.length > 0 && (
          <div className="px-4 py-3 rounded-lg bg-[#0a0a0c] border border-[#26262b] flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="w-5 h-5 text-[#3892f3]" />
              <span className="text-sm text-white font-medium">{localFiles[0].name}</span>
            </div>
            <CheckCircle className="w-5 h-5 text-[#00c853]" />
          </div>
        )}
      </div>

      {mensajePoda && (
        <div className="flex items-center space-x-2.5 p-3 rounded-lg bg-[#00c853]/10 border border-[#00c853]/40 text-[#00c853] text-xs animate-pulse">
          <UploadCloud className="w-4 h-4 shrink-0 animate-bounce" />
          <span>{mensajePoda}</span>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={handleProcesar}
          disabled={localFiles.length === 0 || isProcessing}
          style={{ background: localFiles.length > 0 ? "linear-gradient(135deg, #00c853, #1de9b6)" : "#26262b" }}
          className={`px-6 py-2.5 text-sm font-semibold rounded-lg flex items-center justify-center transition shadow-md ${
            localFiles.length > 0 && !isProcessing
              ? "text-[#0a0a0c] hover:opacity-95 cursor-pointer"
              : "text-zinc-500 cursor-not-allowed"
          }`}
        >
          <span>{isProcessing ? "Procesando..." : "Clasificar Balance"}</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </button>
      </div>
    </div>
  );
}
