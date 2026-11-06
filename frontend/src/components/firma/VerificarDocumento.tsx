"use client";

import * as React from "react";
import { CheckCircle2, FileSearch, UploadCloud, XCircle } from "lucide-react";

import { verificarDocumento, ErrorAceptacion, type ResultadoVerificar } from "@/lib/firma/aceptaciones";

type Estado =
  | { tipo: "idle" }
  | { tipo: "verificando" }
  | { tipo: "resultado"; datos: ResultadoVerificar; nombre: string }
  | { tipo: "error"; mensaje: string };

const TIPO_ETIQUETA: Record<string, string> = {
  documento: "Documento aprobado",
  acuse: "Acuse de aceptación",
};

export function VerificarDocumento() {
  const [estado, setEstado] = React.useState<Estado>({ tipo: "idle" });
  const inputRef = React.useRef<HTMLInputElement>(null);

  async function handleArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    setEstado({ tipo: "verificando" });
    try {
      const res = await verificarDocumento(archivo);
      setEstado({ tipo: "resultado", datos: res, nombre: archivo.name });
    } catch (err) {
      const msg =
        err instanceof ErrorAceptacion ? err.message : "No se pudo verificar el archivo.";
      setEstado({ tipo: "error", mensaje: msg });
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function handleZona(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const archivo = e.dataTransfer.files[0];
    if (!archivo) return;
    setEstado({ tipo: "verificando" });
    verificarDocumento(archivo)
      .then((res) => setEstado({ tipo: "resultado", datos: res, nombre: archivo.name }))
      .catch((err) => {
        const msg =
          err instanceof ErrorAceptacion ? err.message : "No se pudo verificar el archivo.";
        setEstado({ tipo: "error", mensaje: msg });
      });
  }

  return (
    <section
      aria-labelledby="titulo-verificar"
      className="rounded-xl border border-[var(--ui-border,#3f3f46)] bg-[var(--ui-surface,#18181b)] p-6"
    >
      <div className="flex items-center gap-2">
        <FileSearch className="h-5 w-5 text-[var(--ui-accent,#8b5cf6)]" aria-hidden="true" />
        <h2 id="titulo-verificar" className="text-base font-semibold">
          Verificar documento
        </h2>
      </div>
      <p className="mt-1 text-sm text-[var(--ui-muted,#a1a1aa)]">
        Sube o arrastra un archivo para comprobar si su huella coincide con un documento aprobado o un
        acuse de esta organización.
      </p>

      <div
        data-testid="zona-arrastre"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleZona}
        onClick={() => inputRef.current?.click()}
        className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-[var(--ui-border,#3f3f46)] p-8 text-center hover:border-[var(--ui-accent,#8b5cf6)] transition-colors"
        role="button"
        tabIndex={0}
        aria-label="Zona para arrastrar o seleccionar archivo"
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      >
        <UploadCloud className="h-8 w-8 text-[var(--ui-muted,#a1a1aa)]" aria-hidden="true" />
        <p className="text-sm text-[var(--ui-muted,#a1a1aa)]">
          Arrastra aquí o <span className="text-[var(--ui-accent,#8b5cf6)]">elige un archivo</span>
        </p>
        <p className="text-xs text-[var(--ui-muted,#a1a1aa)]">Máximo 10 MB</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        aria-hidden="true"
        onChange={handleArchivo}
      />

      {estado.tipo === "verificando" && (
        <p className="mt-4 text-sm text-[var(--ui-muted,#a1a1aa)]" aria-live="polite">
          Verificando…
        </p>
      )}

      {estado.tipo === "resultado" && (
        <div
          data-testid="resultado-verificacion"
          role="status"
          className="mt-4 flex items-start gap-3 rounded-lg border border-[var(--ui-border,#3f3f46)] p-4"
        >
          {estado.datos.coincide ? (
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" aria-hidden="true" />
          ) : (
            <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" aria-hidden="true" />
          )}
          <div>
            <p className="text-sm font-medium">
              {estado.datos.coincide ? "Coincide" : "No coincide"}
            </p>
            <p className="text-xs text-[var(--ui-muted,#a1a1aa)]">{estado.nombre}</p>
            {estado.datos.tipo && (
              <p className="mt-1 text-xs">
                Tipo: {TIPO_ETIQUETA[estado.datos.tipo] ?? estado.datos.tipo}
              </p>
            )}
          </div>
        </div>
      )}

      {estado.tipo === "error" && (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-red-900 bg-red-950/30 px-3 py-2 text-sm text-red-200"
        >
          {estado.mensaje}
        </p>
      )}
    </section>
  );
}
