"use client";

import React, { useEffect, useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { cabecerasDeRol, fetchAutenticado } from "@/lib/auth";
import { obtenerContextoRolesCapa } from "@/lib/capa";
import { useRoadmapStore } from "@/store/useRoadmapStore";

/**
 * Exportación del RAT (RAT-06): XLSX o PDF con las fichas vigentes. Tras descargar muestra la huella SHA-256 del
 * XLSX, que el PDF lleva en su pie.
 */

type Formato = "xlsx" | "pdf";

const ROLES_EXPORTACION = ["coordinador", "implementador", "dpo", "admin_organizacion"];
const NOMBRE_POR_DEFECTO = "rat";

function nombreDe(disposicion: string | null, formato: Formato): string {
  return disposicion?.match(/filename="([^"]+)"/)?.[1] ?? `${NOMBRE_POR_DEFECTO}.${formato}`;
}

function descargar(archivo: Blob, nombre: string): void {
  const url = URL.createObjectURL(archivo);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

export default function ExportarRat() {
  const sesion = useRoadmapStore((s) => s.session);
  const [roles, setRoles] = useState<string[]>(sesion.role ? [sesion.role] : []);
  const [uid, setUid] = useState(sesion.userId);
  const [enCurso, setEnCurso] = useState<Formato | null>(null);
  const [huella, setHuella] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    obtenerContextoRolesCapa()
      .then((contexto) => {
        setRoles(contexto.roles);
        setUid((actual) => contexto.user_id || actual);
      })
      .catch(() => {
        // Sin /organizacion/me/roles se conserva el rol de la sesión local.
      });
  }, []);

  const rol = ROLES_EXPORTACION.find((r) => roles.includes(r));
  if (!rol) return null;

  async function exportar(formato: Formato) {
    setEnCurso(formato);
    setError(null);
    setHuella(null);
    try {
      const res = await fetchAutenticado(`/api/v1/rat/exportar?formato=${formato}`, {
        method: "GET",
        headers: { ...cabecerasDeRol(rol as string, uid) },
      });
      if (!res.ok) {
        const cuerpo = (await res.json().catch(() => null)) as { detail?: unknown } | null;
        throw new Error(typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo exportar el RAT.");
      }
      descargar(await res.blob(), nombreDe(res.headers.get("Content-Disposition"), formato));
      setHuella(res.headers.get("X-Huella-SHA256"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo exportar el RAT.");
    } finally {
      setEnCurso(null);
    }
  }

  const boton = (formato: Formato, etiqueta: string) => (
    <button
      type="button"
      onClick={() => exportar(formato)}
      disabled={enCurso !== null}
      className="inline-flex items-center gap-1.5 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 font-semibold hover:bg-[var(--ui-boton-hover)] disabled:opacity-50"
    >
      {enCurso === formato ? (
        <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
      ) : (
        <Download className="w-4 h-4" aria-hidden="true" />
      )}
      {etiqueta}
    </button>
  );

  return (
    <section aria-label="Exportar" className="flex flex-wrap items-center gap-2 text-xs">
      {boton("xlsx", "Exportar XLSX")}
      {boton("pdf", "Exportar PDF")}
      {huella && (
        <p role="status" className="break-all text-[var(--ui-texto-suave)]">
          Huella SHA-256 del XLSX: <code>{huella}</code>
        </p>
      )}
      {error && (
        <p role="alert" className="text-[var(--status-danger)]">
          {error}
        </p>
      )}
    </section>
  );
}
