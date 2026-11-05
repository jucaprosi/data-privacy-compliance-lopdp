"use client";

// ¤adpa ¤rbac-tenant ¤rat ¤hallazgos
/**
 * Panel «Vínculos» de la ficha del documento (BIB-402): tratamientos, controles P1–P80 y tareas.
 * Escriben `implementador` y `coordinador`; los demás solo leen. Un vínculo «Revisar» indica que su
 * tratamiento cambió de versión o se dio de baja.
 */
import React from "react";
import {
  guardarVinculos, listarVinculos, misRoles, puedeVincular, separarVinculos,
  type EntradaVinculos, type TipoVinculo, type Vinculo,
} from "@/lib/biblioteca/vinculos";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import DocumentosDelTratamiento from "@/components/biblioteca/vinculos/DocumentosDelTratamiento";

const LISTAS: { tipo: TipoVinculo; clave: keyof EntradaVinculos; titulo: string; ayuda: string }[] = [
  { tipo: "tratamiento", clave: "tratamientos", titulo: "Tratamientos", ayuda: "ID del tratamiento del RAT" },
  { tipo: "control", clave: "controles", titulo: "Controles", ayuda: "Control P1 a P80" },
  { tipo: "tarea", clave: "tareas", titulo: "Tareas", ayuda: "ID de la tarea de la hoja de ruta" },
];

export default function VinculosDocumento() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [vinculos, setVinculos] = React.useState<Vinculo[]>([]);
  const [escribe, setEscribe] = React.useState(false);
  const [nuevos, setNuevos] = React.useState<Record<TipoVinculo, string>>({ tratamiento: "", control: "", tarea: "" });
  const [abierto, setAbierto] = React.useState<string | null>(null);
  const [aviso, setAviso] = React.useState("");

  const recargar = React.useCallback(async () => {
    if (!documentoId) return;
    try {
      setVinculos(await listarVinculos(documentoId));
      setAviso("");
    } catch (e) {
      setAviso(e instanceof Error ? e.message : "No se pudieron consultar los vínculos.");
    }
  }, [documentoId]);

  React.useEffect(() => { void recargar(); }, [recargar]);
  React.useEffect(() => { void misRoles().then((r) => setEscribe(puedeVincular(r))); }, []);
  if (!documentoId) return null;

  const guardar = async (entrada: EntradaVinculos) => {
    try {
      setVinculos(await guardarVinculos(documentoId, entrada));
      setAviso("Vínculos guardados.");
    } catch (e) {
      setAviso(e instanceof Error ? e.message : "No se pudieron guardar los vínculos.");
    }
  };

  const agregar = (tipo: TipoVinculo, clave: keyof EntradaVinculos) => {
    const ref = nuevos[tipo].trim();
    if (!ref) return;
    const entrada = separarVinculos(vinculos);
    if (!entrada[clave].includes(ref)) entrada[clave] = [...entrada[clave], ref];
    setNuevos({ ...nuevos, [tipo]: "" });
    void guardar(entrada);
  };

  const quitar = (v: Vinculo, clave: keyof EntradaVinculos) => {
    const entrada = separarVinculos(vinculos);
    entrada[clave] = entrada[clave].filter((r) => r !== v.ref);
    void guardar(entrada);
  };

  return (
    <section aria-label="Vínculos" className="mt-2 rounded-md border border-[var(--ui-borde)] p-3">
      <h4 className="font-semibold">Vínculos</h4>
      <p className="text-[11px] text-[var(--ui-texto-suave)]">
        Al aprobar el documento, queda como evidencia de sus tareas; la tarea no se cierra sola.
      </p>
      {aviso && <p role="status" className="mt-1">{aviso}</p>}
      <div className="mt-2 grid gap-3 md:grid-cols-3">
        {LISTAS.map(({ tipo, clave, titulo, ayuda }) => (
          <div key={tipo} aria-label={titulo} role="group">
            <h5 className="font-medium">{titulo}</h5>
            <ul className="space-y-1" data-testid={`vinculos-${tipo}`}>
              {vinculos.filter((v) => v.tipo === tipo).map((v) => (
                <li key={v.id} className="rounded border border-[var(--ui-borde)] p-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span>{v.ref}</span>
                    {v.estado === "revisar" && <span className="badge-render-warning rounded px-1 text-[11px]">Revisar</span>}
                    {tipo === "tratamiento" && (
                      <button type="button" className="underline" onClick={() => setAbierto(abierto === v.ref ? null : v.ref)}>
                        Documentos que lo usan
                      </button>
                    )}
                    {escribe && (
                      <button type="button" aria-label={`Quitar ${v.ref}`} onClick={() => quitar(v, clave)}>Quitar</button>
                    )}
                  </div>
                  {abierto === v.ref && <DocumentosDelTratamiento tratamientoId={v.ref} />}
                </li>
              ))}
            </ul>
            {escribe && (
              <div className="mt-1 flex gap-1">
                <input aria-label={ayuda} placeholder={ayuda} value={nuevos[tipo]}
                  onChange={(e) => setNuevos({ ...nuevos, [tipo]: e.target.value })}
                  className="min-w-0 flex-1 rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1" />
                <button type="button" onClick={() => agregar(tipo, clave)}
                  className="rounded border border-[var(--ui-borde)] px-2 py-1">Vincular</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
