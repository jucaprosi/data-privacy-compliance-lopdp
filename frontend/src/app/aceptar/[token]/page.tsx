// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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

// Textos cerrados por UX/UI (2026-11-15) para la descarga del comprobante.
const TEXTO_DESCARGA = {
  etiqueta: "Descargar el comprobante (PDF)",
  nombreAccesible: "Descargar el comprobante de aceptación en PDF",
  linea: "Aceptación registrada. Descarga y guarda tu comprobante: es tu constancia de que aceptaste el documento.",
  preparando: "Preparando el comprobante…",
  huella: (sha: string) => `Huella de integridad: ${sha.slice(0, 8)}`,
  errorFallo: "No pudimos descargar el comprobante. Inténtalo de nuevo.",
  errorSinPdf:
    "Tu aceptación quedó registrada, pero el comprobante aún no está disponible. Vuelve a cargar esta página en unos minutos.",
};

function nombreArchivo(): string {
  return `comprobante-aceptacion-${new Date().toISOString().slice(0, 10)}.pdf`;
}

function descargarAcuse(acuse: ResultadoAceptar): void {
  const binario = atob(acuse.acuse_pdf);
  const bytes = Uint8Array.from(binario, (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo();
  enlace.click();
  URL.revokeObjectURL(url);
}

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
  const [errorDescarga, setErrorDescarga] = React.useState(false);
  const [descargando, setDescargando] = React.useState(false);

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
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-4 py-10 text-[var(--foreground)]">
      <section
        aria-labelledby="titulo-aceptacion"
        className="w-full max-w-lg rounded-2xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-7 shadow-2xl"
      >
        <FileText className="h-9 w-9 text-[var(--ui-primario)]" aria-hidden="true" />

        {estado.tipo === "cargando" && (
          <p className="mt-6 text-sm text-[var(--ui-texto-suave)]" aria-live="polite">
            Cargando información del documento…
          </p>
        )}

        {estado.tipo === "listo" && (
          <>
            <h1 id="titulo-aceptacion" className="mt-4 text-2xl font-semibold">
              Aceptar documento
            </h1>
            <p className="mt-1 text-sm text-[var(--ui-texto-suave)]">
              {estado.info.organizacion} solicita tu aceptación.
            </p>

            <div className="mt-6 rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie-2)] p-4 space-y-2">
              <p className="text-sm font-medium">{estado.info.nombre_documento}</p>
              <p className="font-mono text-xs text-[var(--ui-texto-suave)] break-all">
                SHA-256: {estado.info.sha256}
              </p>
            </div>

            <p className="mt-4 text-sm text-[var(--ui-texto-suave)]">
              Al pulsar «Acepto» se registrarán tu nombre, correo, fecha, hora e IP como constancia de
              aceptación. El acuse quedará custodiado en la plataforma.
            </p>

            <button
              data-testid="btn-acepto"
              onClick={handleAceptar}
              disabled={aceptando}
              className="mt-6 w-full rounded-lg bg-[var(--ui-primario)] px-4 py-2.5 text-sm font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
            >
              {aceptando ? "Registrando…" : "Acepto"}
            </button>
          </>
        )}

        {estado.tipo === "aceptado" && (
          <div data-testid="acuse-ok" className="mt-4 space-y-4">
            <CheckCircle2 className="h-9 w-9 text-[var(--ui-exito-texto)]" />
            <h1 id="titulo-aceptacion" className="text-2xl font-semibold">
              Aceptación registrada
            </h1>
            <p role="status" className="text-sm text-[var(--ui-texto-suave)]">
              {TEXTO_DESCARGA.linea}
            </p>
            {estado.acuse.acuse_pdf ? (
              <>
                <button
                  type="button"
                  data-testid="btn-descargar-acuse"
                  aria-label={TEXTO_DESCARGA.nombreAccesible}
                  aria-busy={descargando}
                  disabled={descargando}
                  onClick={() => {
                    setDescargando(true);
                    try {
                      descargarAcuse(estado.acuse);
                      setErrorDescarga(false);
                    } catch {
                      setErrorDescarga(true);
                    } finally {
                      setDescargando(false);
                    }
                  }}
                  className="w-full rounded-lg border border-[var(--ui-borde-control)] px-4 py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                >
                  {descargando ? TEXTO_DESCARGA.preparando : TEXTO_DESCARGA.etiqueta}
                </button>
                {errorDescarga && (
                  <p role="alert" data-testid="error-descarga" className="text-xs text-[var(--ui-error-texto)]">
                    {TEXTO_DESCARGA.errorFallo}
                  </p>
                )}
              </>
            ) : (
              <p role="alert" data-testid="sin-comprobante" className="text-xs text-[var(--ui-aviso-texto)]">
                {TEXTO_DESCARGA.errorSinPdf}
              </p>
            )}
            <p data-testid="acuse-sha256" className="font-mono text-xs text-[var(--ui-texto-suave)]">
              {TEXTO_DESCARGA.huella(estado.acuse.acuse_sha256)}
            </p>
          </div>
        )}

        {estado.tipo === "caducado" && (
          <div role="alert" data-testid="enlace-caducado" className="mt-4 space-y-3">
            <XCircle className="h-9 w-9 text-[var(--ui-aviso-texto)]" />
            <h1 id="titulo-aceptacion" className="text-xl font-semibold">Enlace no disponible</h1>
            <p className="text-sm text-[var(--ui-texto-suave)]">
              Este enlace ya fue utilizado o ha caducado. Contacta a quien lo envió para recibir uno
              nuevo.
            </p>
          </div>
        )}

        {estado.tipo === "error" && (
          <div role="alert" className="mt-4 space-y-3">
            <XCircle className="h-9 w-9 text-[var(--ui-error-texto)]" />
            <h1 id="titulo-aceptacion" className="text-xl font-semibold">Error</h1>
            <p className="text-sm text-[var(--ui-texto-suave)]">{estado.mensaje}</p>
          </div>
        )}
      </section>
    </main>
  );
}
