// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
        return "bg-[var(--ui-info-fondo)] text-[var(--ui-info-texto)] border-[var(--ui-info-borde)]";
      case "EN_ANALISIS":
        return "bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)] border-[var(--ui-aviso-borde)]";
      case "EN_REQUERIMIENTO":
        return "bg-orange-50 text-orange-700 border-orange-200";
      case "CONTESTADA":
        return "bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border-[var(--ui-exito-borde)]";
      case "VENCIDA":
        return "bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] border-[var(--ui-error-borde)]";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  return (
    <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl p-6 sm:p-8 shadow-sm">
        <header className="text-center mb-6">
          <div className="w-10 h-10 bg-[var(--ui-info-fondo)] text-[var(--ui-enlace)] rounded-full flex items-center justify-center mx-auto mb-3 font-semibold">
            🔍
          </div>
          <h1 className="text-xl font-bold">Estado de su Solicitud</h1>
          <p className="text-xs font-mono text-[var(--color-text-secondary)] mt-1 break-all">
            Código: {codigo}
          </p>
        </header>

        {cargando && (
          <div className="py-8 text-center">
            <div className="w-6 h-6 border-3 border-[var(--ui-primario)] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs text-[var(--color-text-secondary)]">Consultando registro oficial...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-[var(--ui-error-fondo)] border border-[var(--ui-error-borde)] text-[var(--ui-error-texto)] rounded-lg text-sm text-center mb-6">
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

            <div className="p-3 bg-[var(--ui-aviso-fondo)] border border-[var(--ui-aviso-borde)] rounded-lg text-xs text-[var(--ui-aviso-texto)] leading-relaxed">
              Por confidencialidad y protección de datos, la resolución detallada se notifica directamente al correo electrónico consignado al registrar el trámite.
            </div>
          </div>
        )}

        <div className="text-center pt-4 border-t border-[var(--color-border-subtle)]">
          <Link
            href="/solicitud/seguir"
            className="text-xs text-[var(--ui-enlace)] hover:text-[var(--ui-enlace)] font-medium hover:underline"
          >
            Consultar otro código
          </Link>
        </div>
      </div>
    </main>
  );
}
