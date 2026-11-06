"use client";

// ¤adpa ¤rbac-tenant ¤rat
/**
 * «Documentos que lo usan» de un tratamiento (BIB-402). Lo monta la ficha del documento junto a cada
 * tratamiento vinculado, y queda listo para la pestaña del RAT.
 */
import React from "react";
import { documentosDeTratamiento, type DocumentoVinculado } from "@/lib/biblioteca/vinculos";

export default function DocumentosDelTratamiento({ tratamientoId }: { tratamientoId: string }) {
  const [documentos, setDocumentos] = React.useState<DocumentoVinculado[] | null>(null);
  const [aviso, setAviso] = React.useState("");

  React.useEffect(() => {
    let vivo = true;
    documentosDeTratamiento(tratamientoId)
      .then((lista) => { if (vivo) { setDocumentos(lista); setAviso(""); } })
      .catch((e) => { if (vivo) setAviso(e instanceof Error ? e.message : "No se pudo consultar."); });
    return () => { vivo = false; };
  }, [tratamientoId]);

  return (
    <section aria-label={`Documentos que lo usan ${tratamientoId}`} className="mt-1 rounded border border-[var(--ui-borde)] p-2">
      <h5 className="font-semibold">Documentos que lo usan</h5>
      {aviso && <p role="status" className="text-[var(--ui-texto-suave)]">{aviso}</p>}
      {documentos && documentos.length === 0 && <p className="text-[var(--ui-texto-suave)]">Ningún documento lo usa.</p>}
      <ul className="mt-1 space-y-1">
        {(documentos ?? []).map((d) => (
          <li key={d.documento_id} className="flex flex-wrap items-center gap-2">
            <span>{d.nombre}</span>
            <span className="text-[var(--ui-texto-suave)]">{d.codigo} · {d.estado_documento}</span>
            {d.estado === "revisar" && <span className="badge-render-warning rounded px-1 text-[11px]">Revisar</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}
