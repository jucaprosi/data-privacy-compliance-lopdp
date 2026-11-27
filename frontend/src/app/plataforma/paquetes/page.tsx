// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import * as React from "react";
import Link from "next/link";
import { RefreshCw, ShieldAlert } from "lucide-react";

import { ErrorPaquetes, ETIQUETA_ESTADO, paquetesApi, type Paquete } from "@/lib/plataforma/paquetes";

export default function PaquetesNormativosPage() {
  const [paquetes, setPaquetes] = React.useState<Paquete[]>([]);
  const [cargando, setCargando] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [denegado, setDenegado] = React.useState(false);

  const cargar = React.useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setPaquetes(await paquetesApi.listar());
      setDenegado(false);
    } catch (err) {
      if (err instanceof ErrorPaquetes && err.status === 403) setDenegado(true);
      else setError(err instanceof Error ? err.message : "No se pudo cargar la lista.");
    } finally {
      setCargando(false);
    }
  }, []);

  React.useEffect(() => {
    void cargar();
  }, [cargar]);

  if (denegado) {
    return (
      <main className="min-h-screen bg-[var(--background)] px-6 py-16 text-[var(--foreground)]">
        <section className="mx-auto max-w-xl rounded-2xl border border-[color:var(--ui-error-borde)] bg-[var(--ui-superficie)] p-8 text-center">
          <ShieldAlert className="mx-auto h-10 w-10 text-[var(--ui-error-texto)]" aria-hidden="true" />
          <h1 className="mt-4 text-2xl font-semibold">Acceso denegado</h1>
          <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">Esta sección está reservada para operadores de la plataforma.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-5 py-8 text-[var(--foreground)]">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--ui-texto-suave)]">Administración global</p>
            <h1 className="mt-2 text-3xl font-semibold">Paquetes normativos</h1>
            <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">
              Plazos, requisitos y controles comunes de cada normativa. Un valor sin verificar no se publica.
            </p>
          </div>
          <button
            onClick={() => void cargar()}
            className="inline-flex items-center gap-2 rounded-lg border border-[color:var(--ui-borde-control)] px-3 py-2 text-sm hover:bg-[var(--ui-boton-hover)]"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" /> Actualizar
          </button>
        </header>

        {error && (
          <p role="alert" className="rounded-lg border border-[color:var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-4 py-3 text-sm text-[var(--ui-error-texto)]">
            {error}
          </p>
        )}

        <section className="rounded-2xl border border-[color:var(--ui-borde)] bg-[var(--ui-superficie)]">
          {cargando ? (
            <p className="p-5 text-sm text-[var(--ui-texto-suave)]">Cargando…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Paquetes normativos y sus versiones</caption>
                <thead className="bg-[var(--ui-superficie-2)] text-xs uppercase text-[var(--ui-texto-suave)]">
                  <tr>
                    <th scope="col" className="p-3">Nombre</th>
                    <th scope="col" className="p-3">Versión</th>
                    <th scope="col" className="p-3">Estado</th>
                    <th scope="col" className="p-3">Parámetros sin verificar</th>
                  </tr>
                </thead>
                <tbody>
                  {paquetes.map((p) => (
                    <tr key={p.id} className="border-t border-[color:var(--ui-borde)]">
                      <td className="p-3">
                        <Link href={`/plataforma/paquetes/${encodeURIComponent(p.id)}`} className="text-[var(--ui-primario)] hover:underline">
                          {p.nombre}
                        </Link>
                      </td>
                      <td className="p-3">{p.version}</td>
                      <td className="p-3">{ETIQUETA_ESTADO[p.estado]}</td>
                      <td className="p-3">{p.sin_verificar > 0 ? `${p.sin_verificar} sin verificar` : "Todos verificados"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
