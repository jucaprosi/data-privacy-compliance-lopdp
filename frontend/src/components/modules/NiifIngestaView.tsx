// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
      <div className="flex items-center justify-between bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-6 shadow-md">
        <div>
          <h2 className="text-xl font-bold text-[var(--foreground)] flex items-center">
            <UploadCloud className="w-5 h-5 mr-2 text-[var(--ui-exito-texto)]" />
            Ingesta de Balance NIIF 18
          </h2>
          <p className="text-sm text-[var(--ui-texto-suave)] mt-1">
            Sube el Balance de Comprobación en formato Excel o CSV. El motor mapeará las cuentas automáticamente a las categorías mandatorias.
          </p>
        </div>
      </div>

      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-6 shadow-sm space-y-4">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-4 ${
            isDragActive
              ? "border-[var(--ui-exito-borde)] bg-[var(--ui-exito-fondo)]"
              : errorMessage
              ? "border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)]"
              : "border-[var(--ui-borde)] hover:border-[var(--ui-exito-borde)] bg-[var(--ui-campo)]"
          }`}
        >
          <input {...getInputProps()} />
          <div className="w-16 h-16 rounded-full bg-[var(--ui-boton)] flex items-center justify-center text-[var(--ui-texto-suave)] shadow-md">
            <FileSpreadsheet className="w-8 h-8 text-[var(--ui-exito-texto)]" />
          </div>
          <div>
            <span className="text-sm font-semibold text-[var(--foreground)] block">
              Haz clic para seleccionar o arrastra el Balance aquí
            </span>
            <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
              Formatos soportados: .xlsx, .csv
            </p>
          </div>
        </div>

        {errorMessage && (
          <div className="flex items-center space-x-2.5 p-3 rounded-lg bg-[var(--ui-error-fondo)] border border-[var(--ui-error-borde)] text-[var(--ui-error-texto)] text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {localFiles.length > 0 && (
          <div className="px-4 py-3 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="w-5 h-5 text-[var(--ui-enlace)]" />
              <span className="text-sm text-[var(--foreground)] font-medium">{localFiles[0].name}</span>
            </div>
            <CheckCircle className="w-5 h-5 text-[var(--ui-exito-texto)]" />
          </div>
        )}
      </div>

      {mensajePoda && (
        <div className="flex items-center space-x-2.5 p-3 rounded-lg bg-[var(--ui-exito-fondo)] border border-[var(--ui-exito-borde)] text-[var(--ui-exito-texto)] text-xs animate-pulse">
          <UploadCloud className="w-4 h-4 shrink-0 animate-bounce" />
          <span>{mensajePoda}</span>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={handleProcesar}
          disabled={localFiles.length === 0 || isProcessing}
          style={{ background: localFiles.length > 0 ? "var(--ui-primario)" : "var(--ui-boton)" }}
          className={`px-6 py-2.5 text-sm font-semibold rounded-lg flex items-center justify-center transition shadow-md ${
            localFiles.length === 0
              ? "text-[var(--ui-texto-suave)] cursor-not-allowed"
              : isProcessing
              ? "text-[var(--ui-primario-texto)] cursor-not-allowed"
              : "text-[var(--ui-primario-texto)] hover:opacity-95 cursor-pointer"
          }`}
        >
          <span>{isProcessing ? "Procesando..." : "Clasificar Balance"}</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </button>
      </div>
    </div>
  );
}
