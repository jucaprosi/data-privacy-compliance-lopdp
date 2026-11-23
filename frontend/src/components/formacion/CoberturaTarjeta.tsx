// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤evidencias ¤rbac-tenant
import React, { useState, useEffect } from "react";
import { CoberturaDatos, obtenerCobertura } from "@/lib/formacion/formacion";

export const CoberturaTarjeta: React.FC = () => {
  const [datos, setDatos] = useState<CoberturaDatos | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = async () => {
    setCargando(true);
    setError(null);
    try {
      const c = await obtenerCobertura();
      setDatos(c);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al cargar cobertura");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  if (cargando) {
    return (
      <div role="status" className="p-4 text-sm text-slate-500">
        Cargando cobertura de formación...
      </div>
    );
  }

  if (error || !datos) {
    return (
      <div role="alert" className="p-4 bg-rose-50 text-rose-800 rounded-lg text-sm border border-rose-200">
        {error || "No pudimos cargar la cobertura."}
      </div>
    );
  }

  const porcentaje = datos.obligadas > 0 ? Math.round(datos.cobertura * 100) : 0;

  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
          Cobertura de formación
        </h2>
        <p className="text-xs text-slate-500">
          Cobertura sobre todas las personas activas del inventario
        </p>
      </div>

      {datos.obligadas === 0 ? (
        <p className="text-sm text-slate-500 italic">
          Aún no hay personas con tratamientos asignados. La cobertura se calcula cuando las haya.
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">
              {datos.formadas} de {datos.obligadas} personas formadas
            </span>
            <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
              {porcentaje} %
            </span>
          </div>

          <div
            role="progressbar"
            aria-label="Personas formadas"
            aria-valuenow={datos.formadas}
            aria-valuemin={0}
            aria-valuemax={datos.obligadas}
            aria-valuetext={`${datos.formadas} de ${datos.obligadas}`}
            className="w-full h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden"
          >
            <div
              className="bg-indigo-600 h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, porcentaje)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
