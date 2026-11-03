"use client";

import * as React from "react";
import { CheckCircle2, FileText, XCircle } from "lucide-react";

import {
  obtenerInfoPublica,
  aceptarEnlace,
  ErrorAceptacion,
  type InfoAceptacion,
  type ResultadoAceptar,
} from "@/lib/firma/aceptaciones";

type Estado =
  | { tipo: "cargando" }
  | { tipo: "listo"; info: InfoAceptacion }
  | { tipo: "aceptado"; acuse: ResultadoAceptar }
  | { tipo: "caducado" }
  | { tipo: "error"; mensaje: string };

function mensajeError(err: unknown): string {
  if (err instanceof ErrorAceptacion) {
    if (err.status === 410) return "Este enlace ya fue utilizado o ha caducado.";
    if (err.status === 404) return "El enlace no existe.";
    return err.message;
  }
  return "No se pudo procesar la solicitud.";
}

export default function AceptarPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = React.use(params);
  const [estado, setEstado] = React.useState<Estado>({ tipo: "cargando" });
  const [aceptando, setAceptando] = React.useState(false);

  React.useEffect(() => {
    obtenerInfoPublica(token)
      .then((info) => setEstado({ tipo: "listo", info }))
      .catch((err) => {
        if (err instanceof ErrorAceptacion && (err.status === 410 || err.code === "ACEPTACION_CADUCADA")) {
          setEstado({ tipo: "caducado" });
        } else {
          setEstado({ tipo: "error", mensaje: mensajeError(err) });
        }
      });
  }, [token]);

  async function handleAceptar() {
    setAceptando(true);
    try {
      const res = await aceptarEnlace(token);
      setEstado({ tipo: "aceptado", acuse: res });
    } catch (err) {
      if (err instanceof ErrorAceptacion && err.status === 410) {
        setEstado({ tipo: "caducado" });
      } else {
        setEstado({ tipo: "error", mensaje: mensajeError(err) });
      }
    } finally {
      setAceptando(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--ui-bg,#09090b)] px-4 py-10 text-[var(--ui-fg,#fafafa)]">
      <section
        aria-labelledby="titulo-aceptacion"
        className="w-full max-w-lg rounded-2xl border border-[var(--ui-border,#3f3f46)] bg-[var(--ui-surface,#18181b)] p-7 shadow-2xl"
      >
        <FileText className="h-9 w-9 text-[var(--ui-accent,#8b5cf6)]" aria-hidden="true" />

        {estado.tipo === "cargando" && (
          <p className="mt-6 text-sm text-[var(--ui-muted,#a1a1aa)]" aria-live="polite">
            Cargando información del documento…
          </p>
        )}

        {estado.tipo === "listo" && (
          <>
            <h1 id="titulo-aceptacion" className="mt-4 text-2xl font-semibold">
              Aceptar documento
            </h1>
            <p className="mt-1 text-sm text-[var(--ui-muted,#a1a1aa)]">
              {estado.info.organizacion} solicita tu aceptación.
            </p>

            <div className="mt-6 rounded-xl border border-[var(--ui-border,#3f3f46)] bg-[var(--ui-bg,#09090b)] p-4 space-y-2">
              <p className="text-sm font-medium">{estado.info.nombre_documento}</p>
              <p className="font-mono text-xs text-[var(--ui-muted,#a1a1aa)] break-all">
                SHA-256: {estado.info.sha256}
              </p>
            </div>

            <p className="mt-4 text-sm text-[var(--ui-muted,#a1a1aa)]">
              Al pulsar «Acepto» se registrarán tu nombre, correo, fecha, hora e IP como constancia de
              aceptación. El acuse quedará custodiado en la plataforma.
            </p>

            <button
              data-testid="btn-acepto"
              onClick={handleAceptar}
              disabled={aceptando}
              className="mt-6 w-full rounded-lg bg-[var(--ui-accent,#8b5cf6)] px-4 py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {aceptando ? "Registrando…" : "Acepto"}
            </button>
          </>
        )}

        {estado.tipo === "aceptado" && (
          <div role="status" data-testid="acuse-ok" className="mt-4 space-y-4">
            <CheckCircle2 className="h-9 w-9 text-emerald-400" />
            <h1 id="titulo-aceptacion" className="text-2xl font-semibold">
              Aceptación registrada
            </h1>
            <p className="text-sm text-[var(--ui-muted,#a1a1aa)]">
              Tu aceptación ha quedado custodiada. Guarda el sello de integridad:
            </p>
            <pre
              data-testid="acuse-sha256"
              className="overflow-x-auto rounded-lg border border-[var(--ui-border,#3f3f46)] bg-[var(--ui-bg,#09090b)] p-3 font-mono text-xs"
            >
              {estado.acuse.acuse_sha256}
            </pre>
            <p className="text-xs text-[var(--ui-muted,#a1a1aa)]">
              Este enlace ya no puede volver a utilizarse.
            </p>
          </div>
        )}

        {estado.tipo === "caducado" && (
          <div role="alert" data-testid="enlace-caducado" className="mt-4 space-y-3">
            <XCircle className="h-9 w-9 text-amber-400" />
            <h1 id="titulo-aceptacion" className="text-xl font-semibold">Enlace no disponible</h1>
            <p className="text-sm text-[var(--ui-muted,#a1a1aa)]">
              Este enlace ya fue utilizado o ha caducado. Contacta a quien lo envió para recibir uno
              nuevo.
            </p>
          </div>
        )}

        {estado.tipo === "error" && (
          <div role="alert" className="mt-4 space-y-3">
            <XCircle className="h-9 w-9 text-red-400" />
            <h1 id="titulo-aceptacion" className="text-xl font-semibold">Error</h1>
            <p className="text-sm text-[var(--ui-muted,#a1a1aa)]">{estado.mensaje}</p>
          </div>
        )}
      </section>
    </main>
  );
}
