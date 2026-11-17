"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface SeguimientoData {
  estado: string;
  recibida_en: string;
  respondida_en: string | null;
}

export default function SeguimientoCodigoPage({
  params,
}: {
  params: Promise<{ codigo: string }>;
}) {
  const resolvedParams = React.use(params);
  const codigo = resolvedParams.codigo;

  const [datos, setDatos] = useState<SeguimientoData | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function consultar() {
      try {
        setCargando(true);
        setError(null);
        const res = await fetch(`/api/v1/publico/solicitud/seguir/${encodeURIComponent(codigo)}`);
        if (!res.ok) {
          if (res.status === 404) {
            setError("No existe ninguna solicitud registrada con el código proporcionado.");
          } else {
            setError("Error al consultar el estado de la solicitud.");
          }
          return;
        }
        const data = await res.json();
        setDatos(data);
      } catch {
        setError("Error de conexión al consultar el seguimiento.");
      } finally {
        setCargando(false);
      }
    }
    consultar();
  }, [codigo]);

  const formatearFecha = (fechaStr: string | null) => {
    if (!fechaStr) return "Pendiente";
    try {
      const d = new Date(fechaStr);
      return d.toLocaleDateString("es-EC", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return fechaStr;
    }
  };

  const badgeEstado = (estado: string) => {
    switch (estado.toUpperCase()) {
      case "RECIBIDA":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "EN_ANALISIS":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "EN_REQUERIMIENTO":
        return "bg-orange-50 text-orange-700 border-orange-200";
      case "CONTESTADA":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "VENCIDA":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  return (
    <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl p-6 sm:p-8 shadow-sm">
        <header className="text-center mb-6">
          <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-3 font-semibold">
            🔍
          </div>
          <h1 className="text-xl font-bold">Estado de su Solicitud</h1>
          <p className="text-xs font-mono text-[var(--color-text-secondary)] mt-1 break-all">
            Código: {codigo}
          </p>
        </header>

        {cargando && (
          <div className="py-8 text-center">
            <div className="w-6 h-6 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs text-[var(--color-text-secondary)]">Consultando registro oficial...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm text-center mb-6">
            {error}
          </div>
        )}

        {datos && !cargando && (
          <div className="space-y-4 mb-6">
            <div className="flex items-center justify-between p-3 bg-[var(--color-bg-subtle)] rounded-lg">
              <span className="text-xs text-[var(--color-text-secondary)] font-medium">Estado del Trámite:</span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${badgeEstado(datos.estado)}`}>
                {datos.estado}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-[var(--color-bg-subtle)] rounded-lg">
              <span className="text-xs text-[var(--color-text-secondary)] font-medium">Fecha de Recepción:</span>
              <span className="text-xs font-medium">{formatearFecha(datos.recibida_en)}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-[var(--color-bg-subtle)] rounded-lg">
              <span className="text-xs text-[var(--color-text-secondary)] font-medium">Fecha de Respuesta:</span>
              <span className="text-xs font-medium">{formatearFecha(datos.respondida_en)}</span>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 leading-relaxed">
              Por confidencialidad y protección de datos, la resolución detallada se notifica directamente al correo electrónico consignado al registrar el trámite.
            </div>
          </div>
        )}

        <div className="text-center pt-4 border-t border-[var(--color-border-subtle)]">
          <Link
            href="/solicitud/seguir"
            className="text-xs text-indigo-600 hover:text-indigo-700 font-medium hover:underline"
          >
            Consultar otro código
          </Link>
        </div>
      </div>
    </main>
  );
}
