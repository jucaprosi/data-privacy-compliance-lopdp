// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function BuscarSeguimientoPage() {
  const router = useRouter();
  const [codigo, setCodigo] = useState("");

  const handleBuscar = (e: React.FormEvent) => {
    e.preventDefault();
    const c = codigo.trim();
    if (c) {
      router.push(`/solicitud/seguir/${encodeURIComponent(c)}`);
    }
  };

  return (
    <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl p-6 sm:p-8 shadow-sm">
        <header className="text-center mb-6">
          <div className="w-10 h-10 bg-[var(--ui-info-fondo)] text-[var(--ui-enlace)] rounded-full flex items-center justify-center mx-auto mb-3 font-semibold">
            🔍
          </div>
          <h1 className="text-xl font-bold">Seguimiento de Solicitud</h1>
          <p className="text-xs text-[var(--color-text-secondary)] mt-1">
            Ingrese el código asignado al momento de presentar su solicitud de derechos ARCO+.
          </p>
        </header>

        <form onSubmit={handleBuscar} className="space-y-4">
          <div>
            <label htmlFor="codigo" className="block text-xs font-medium mb-1.5">
              Código de Seguimiento
            </label>
            <input
              id="codigo"
              type="text"
              required
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="Ej. sol_1a2b3c4d5e6f..."
              className="w-full px-3.5 py-2.5 bg-[var(--color-bg-base)] border border-[var(--color-border-subtle)] rounded-lg text-sm font-mono focus:ring-2 focus:ring-[var(--ui-primario)] focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 px-4 bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] font-medium rounded-lg text-sm transition-colors shadow-sm"
          >
            Consultar Trámite
          </button>
        </form>

        <div className="text-center pt-6 mt-6 border-t border-[var(--color-border-subtle)]">
          <Link
            href="/"
            className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:underline"
          >
            Volver a la página principal
          </Link>
        </div>
      </div>
    </main>
  );
}
