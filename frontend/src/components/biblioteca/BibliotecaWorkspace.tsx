"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Biblioteca con sus dos pestañas (BIB-101, `docs/biblioteca-pmv.md` §0): «Documentos de la
 * organización» (vista principal) y «Plantillas». Se monta como vista del menú BIBLIOTECA y dentro
 * del panel lateral; las dos comparten la pestaña elegida.
 *
 * Esta tarea solo da el acceso. El contenido de cada pestaña lo aportan otras fichas: documentos de
 * la organización (BIB-107) y catálogo de plantillas (BIB-102).
 */
import React from "react";
import { FileText, LibraryBig } from "lucide-react";
import { PESTANAS, type PestanaBiblioteca } from "@/lib/biblioteca/contexto";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";

interface Props {
  variante?: "completa" | "panel";
}

const VACIO: Record<PestanaBiblioteca, { icono: typeof FileText; titulo: string; texto: string }> = {
  documentos: {
    icono: FileText,
    titulo: "Todavía no hay documentos de la organización",
    texto: "Aquí aparecerán los documentos creados desde una plantilla, redactados o subidos para esta organización.",
  },
  plantillas: {
    icono: LibraryBig,
    titulo: "El catálogo de plantillas aún no está disponible",
    texto: "Aquí aparecerán las plantillas publicadas y las copias «Mi plantilla» de la organización.",
  },
};

export default function BibliotecaWorkspace({ variante = "completa" }: Props) {
  const pestana = useBibliotecaStore((s) => s.pestana);
  const elegirPestana = useBibliotecaStore((s) => s.elegirPestana);
  const estado = useBibliotecaStore((s) => s.estadoPendientes);
  const mensaje = useBibliotecaStore((s) => s.mensaje);
  const sincronizarOrganizacion = useBibliotecaStore((s) => s.sincronizarOrganizacion);
  const base = React.useId();
  const refs = React.useRef<Partial<Record<PestanaBiblioteca, HTMLButtonElement | null>>>({});

  // La vista puede abrirse sin pasar por el botón: también aquí se descarta lo de otra organización.
  React.useEffect(() => {
    sincronizarOrganizacion();
  }, [sincronizarOrganizacion]);

  function moverCon(evento: React.KeyboardEvent<HTMLDivElement>) {
    if (evento.key !== "ArrowRight" && evento.key !== "ArrowLeft") return;
    evento.preventDefault();
    const i = PESTANAS.findIndex((p) => p.id === pestana);
    const siguiente = PESTANAS[(i + (evento.key === "ArrowRight" ? 1 : PESTANAS.length - 1)) % PESTANAS.length].id;
    elegirPestana(siguiente);
    refs.current[siguiente]?.focus();
  }

  const vacio = VACIO[pestana];
  const Icono = vacio.icono;
  return (
    <section
      aria-label={variante === "panel" ? "Biblioteca en el panel" : "Biblioteca"}
      data-testid={`biblioteca-${variante}`}
      className="flex flex-col gap-3 text-xs"
    >
      {variante === "completa" && (
        <h2 className="text-base font-semibold">Biblioteca</h2>
      )}
      <div role="tablist" aria-label="Pestañas de Biblioteca" onKeyDown={moverCon} className="flex gap-1 border-b border-[var(--ui-borde)]">
        {PESTANAS.map((p) => {
          const elegida = p.id === pestana;
          return (
            <button
              key={p.id}
              ref={(el) => { refs.current[p.id] = el; }}
              type="button"
              role="tab"
              id={`${base}-tab-${p.id}`}
              aria-selected={elegida}
              aria-controls={`${base}-panel-${p.id}`}
              tabIndex={elegida ? 0 : -1}
              onClick={() => elegirPestana(p.id)}
              className={`-mb-px rounded-t-md border px-3 py-1.5 font-medium cursor-pointer ${
                elegida
                  ? "border-[var(--ui-borde)] border-b-[var(--ui-campo)] bg-[var(--ui-campo)]"
                  : "border-transparent text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
              }`}
            >
              {p.nombre}
            </button>
          );
        })}
      </div>

      {estado === "denegado" && (
        <p role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300">
          {mensaje}
        </p>
      )}

      {PESTANAS.map((p) => (
        <div
          key={p.id}
          role="tabpanel"
          id={`${base}-panel-${p.id}`}
          aria-labelledby={`${base}-tab-${p.id}`}
          hidden={p.id !== pestana}
          tabIndex={0}
        >
          {p.id === pestana && (
            <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--ui-borde)] px-4 py-8 text-center">
              <Icono className="h-6 w-6 text-[var(--ui-texto-suave)]" aria-hidden="true" />
              <p className="font-semibold">{vacio.titulo}</p>
              <p className="max-w-md text-[var(--ui-texto-suave)]">{vacio.texto}</p>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
