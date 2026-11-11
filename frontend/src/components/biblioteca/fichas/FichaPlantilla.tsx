"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Ficha de una plantilla (BIB-103): propósito, versión, fuentes, variables con su disponibilidad, vista
 * previa demostrativa y las acciones «Usar en esta organización» y «Editar como Mi plantilla». Se monta en
 * la ranura `plantilla:ficha` y lee la plantilla elegida del registro (`useSeleccionBiblioteca`).
 * El estado editorial de la plantilla y el de los documentos de la organización se muestran por separado.
 */
import React from "react";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";
import {
  crearCopia, obtenerFicha, usarEnOrganizacion,
  type DocumentoCreado, type FichaPlantilla as Ficha, type OrigenVariable,
} from "@/lib/biblioteca/fichas";
import { useSeleccionBiblioteca, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";

const VALIDACION = {
  pendiente: "Pendiente de validación legal", en_revision: "Validación legal en revisión",
  validada: "Validada legalmente", con_observaciones: "Validación legal con observaciones",
} as const;
const SIN_DATO: Record<OrigenVariable, string> = {
  organizacion: "Falta este dato en la organización", delegado: "La organización no tiene delegado vigente",
  persona: "Lo completa la persona al crear el documento", al_crear: "Se completa al crear el documento",
  al_aprobar: "Se completa al aprobar el documento",
};

function estadoDeVariable(v: Ficha["variables"][number]): { texto: string; clase: string } {
  if (v.origen === "organizacion" || v.origen === "delegado") {
    return v.disponible
      ? { texto: "La organización ya tiene este dato", clase: "text-green-700 dark:text-green-300" }
      : { texto: SIN_DATO[v.origen], clase: "text-amber-700 dark:text-amber-300" };
  }
  return { texto: SIN_DATO[v.origen], clase: "text-[var(--ui-texto-suave)]" };
}

const mensajeDe = (e: unknown) => (e instanceof ErrorBiblioteca ? e.message : "No se pudo completar la operación.");

export default function FichaPlantilla({ variante }: PropsVistaBiblioteca) {
  const plantillaId = useSeleccionBiblioteca((s) => s.plantillaId);
  const elegirPlantilla = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const elegirDocumento = useSeleccionBiblioteca((s) => s.elegirDocumento);
  const [ficha, setFicha] = React.useState<Ficha | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [ocupada, setOcupada] = React.useState(false);
  const [creado, setCreado] = React.useState<DocumentoCreado | null>(null);

  React.useEffect(() => {
    setFicha(null); setError(null); setCreado(null);
    if (!plantillaId) return;
    let vigente = true;
    obtenerFicha(plantillaId).then((f) => { if (vigente) setFicha(f); }).catch((e) => { if (vigente) setError(mensajeDe(e)); });
    return () => { vigente = false; };
  }, [plantillaId]);

  if (!plantillaId) return null;

  async function accion(hacer: () => Promise<void>) {
    setOcupada(true); setError(null);
    try { await hacer(); } catch (e) { setError(mensajeDe(e)); } finally { setOcupada(false); }
  }
  const usar = () => accion(async () => {
    const documento = await usarEnOrganizacion(plantillaId);
    setCreado(documento); elegirDocumento(documento.id);
  });
  const copiar = () => accion(async () => { elegirPlantilla((await crearCopia(plantillaId)).id); });

  return (
    <article aria-label="Ficha de plantilla" data-testid={`ficha-plantilla-${variante}`} className="flex flex-col gap-3 text-xs">
      {error && <p role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300">{error}</p>}
      {!ficha && !error && <p role="status">Cargando la ficha…</p>}
      {ficha && (
        <>
          <header className="flex flex-col gap-1">
            <h3 className="text-sm font-semibold">{ficha.nombre}</h3>
            <p className="text-[var(--ui-texto-suave)]">
              {ficha.codigo} · versión {ficha.version} · formato {ficha.formato} ·{" "}
              {ficha.fuente === "smartcidi" ? "Modelo de plantilla" : "Mi plantilla"}
            </p>
            <p>
              <span className="font-medium">Estado editorial de la plantilla:</span>{" "}
              {ficha.estado_editorial === "publicada" ? "Publicada" : "Copia de la organización"} · {VALIDACION[ficha.validacion_legal]}
            </p>
            <p className="text-[var(--ui-texto-suave)]">
              Normativa vigente al {ficha.fecha_corte_normativo} · revisión cada {ficha.revision_meses} meses
              {ficha.origen_plantilla_id && ` · copia de la versión ${ficha.origen_version}`}
            </p>
          </header>

          {ficha.avisos.map((a) => (
            <p key={a.cuando} role="note" className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2">{a.texto}</p>
          ))}

          {ficha.ficha && (
            <dl aria-label="Datos de la ficha" className="grid gap-1">
              {([["Propósito", ficha.ficha.objetivo], ["Fuentes", ficha.ficha.fuentes], ["Fecha de revisión", ficha.ficha.fecha_revision],
                ["Instrucciones", ficha.ficha.instrucciones], ["Dependencias", ficha.ficha.dependencias],
                ["Restricciones", ficha.ficha.restricciones]] as const).map(([titulo, valor]) => (
                <div key={titulo}><dt className="font-medium">{titulo}</dt><dd className="text-[var(--ui-texto-suave)]">{valor}</dd></div>
              ))}
            </dl>
          )}

          <section aria-label="Variables de la plantilla">
            <h4 className="font-medium">Variables</h4>
            <ul className="grid gap-1">
              {ficha.variables.map((v) => {
                const e = estadoDeVariable(v);
                return (
                  <li key={v.clave} data-testid={`variable-${v.clave}`} className="flex flex-wrap justify-between gap-2">
                    <span>{v.etiqueta}</span><span className={e.clase}>{e.texto}</span>
                  </li>
                );
              })}
            </ul>
          </section>

          <section aria-label="Vista previa demostrativa">
            <h4 className="font-medium">Vista previa demostrativa</h4>
            <p role="note" className="text-[var(--ui-texto-suave)]">{ficha.vista_previa.aviso}</p>
            <pre className="whitespace-pre-wrap rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3">{ficha.vista_previa.markdown}</pre>
          </section>

          <div className="flex flex-wrap items-center gap-2">
            {ficha.acciones.usar && (
              <button type="button" disabled={ocupada} onClick={usar}
                className="cursor-pointer rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton-hover)] px-3 py-1.5 font-medium disabled:opacity-60">
                Usar en esta organización
              </button>
            )}
            {ficha.acciones.copiar && (
              <button type="button" disabled={ocupada} onClick={copiar}
                className="cursor-pointer rounded-md border border-[var(--ui-borde)] px-3 py-1.5 disabled:opacity-60">
                Editar como «Mi plantilla»
              </button>
            )}
          </div>
          {ficha.acciones.copiar && <p className="text-[var(--ui-texto-suave)]">Editar un modelo de plantilla crea una copia de tu organización; la original no cambia.</p>}
          {creado && (
            <p role="status" className="rounded-md border border-green-500/40 bg-green-500/10 px-3 py-2">
              Documento creado en borrador
              {creado.variables_faltantes.length > 0 && ` · faltan ${creado.variables_faltantes.length} datos para pasar a revisión`}.
              Su estado se ve en «Documentos de la organización».
            </p>
          )}
        </>
      )}
    </article>
  );
}
