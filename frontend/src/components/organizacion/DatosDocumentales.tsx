"use client";

import React, { useEffect, useId, useState } from "react";
import { FileText } from "lucide-react";
import {
  CAMPOS_DOCUMENTALES,
  DEFINICION_CAMPOS,
  cambiosRespectoDe,
  datosDocumentalesApi,
  validarCampo,
  type CampoDocumental,
  type DatosDocumentales as Datos,
} from "@/lib/organizacion/datosDocumentales";
import type { OrganizacionRole } from "@/types/roadmap";

type Borrador = Record<CampoDocumental, string>;

type Estado =
  | { fase: "cargando" }
  | { fase: "lista"; guardado: Datos }
  | { fase: "error"; mensaje: string };

const borradorDe = (datos: Datos): Borrador =>
  Object.fromEntries(CAMPOS_DOCUMENTALES.map((c) => [c, datos[c] ?? ""])) as Borrador;

const GRUPOS = [
  { grupo: "organizacion", titulo: "Organización" },
  { grupo: "representante", titulo: "Representante legal" },
] as const;

interface Props {
  /** Rol con el que se consulta y, si es administrador, se guarda. */
  rol: OrganizacionRole;
  /** Solo el administrador de la organización edita; los demás ven los datos en solo lectura. */
  puedeEditar: boolean;
  className?: string;
}

/**
 * Formulario «Datos para documentos» (ORG-14): domicilio, contactos y representante legal que la
 * Biblioteca usa para rellenar las plantillas. Todos los campos son opcionales.
 */
export default function DatosDocumentales({ rol, puedeEditar, className = "" }: Props) {
  const idBase = useId();
  const [estado, setEstado] = useState<Estado>({ fase: "cargando" });
  const [borrador, setBorrador] = useState<Borrador | null>(null);
  const [errores, setErrores] = useState<Partial<Record<CampoDocumental, string>>>({});
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);

  useEffect(() => {
    let cancelado = false;
    setEstado({ fase: "cargando" });
    datosDocumentalesApi
      .obtener(rol)
      .then((datos) => {
        if (cancelado) return;
        setEstado({ fase: "lista", guardado: datos });
        setBorrador(borradorDe(datos));
      })
      .catch((err: unknown) => {
        if (cancelado) return;
        setEstado({
          fase: "error",
          mensaje: err instanceof Error ? err.message : "No se pudieron consultar los datos para documentos.",
        });
      });
    return () => {
      cancelado = true;
    };
  }, [rol]);

  const guardar = async () => {
    if (estado.fase !== "lista" || !borrador || !puedeEditar) return;
    const nuevosErrores: Partial<Record<CampoDocumental, string>> = {};
    for (const definicion of DEFINICION_CAMPOS) {
      const error = validarCampo(definicion, borrador[definicion.campo]);
      if (error) nuevosErrores[definicion.campo] = error;
    }
    setErrores(nuevosErrores);
    if (Object.keys(nuevosErrores).length > 0) {
      setAviso({ tipo: "error", texto: "Revise los campos marcados antes de guardar." });
      return;
    }
    const cambios = cambiosRespectoDe(estado.guardado, borrador);
    if (Object.keys(cambios).length === 0) {
      setAviso({ tipo: "ok", texto: "No hay cambios que guardar." });
      return;
    }
    setGuardando(true);
    setAviso(null);
    try {
      const guardado = await datosDocumentalesApi.guardar(cambios, "admin_organizacion");
      setEstado({ fase: "lista", guardado });
      setBorrador(borradorDe(guardado));
      setAviso({ tipo: "ok", texto: "Datos para documentos guardados." });
    } catch (err: unknown) {
      setAviso({
        tipo: "error",
        texto: err instanceof Error ? err.message : "No se pudieron guardar los datos para documentos.",
      });
    } finally {
      setGuardando(false);
    }
  };

  const faltantes = estado.fase === "lista" ? estado.guardado.faltantes.length : 0;

  return (
    <section
      aria-labelledby={`${idBase}-titulo`}
      data-testid="datos-documentales"
      className={`bg-white dark:bg-[var(--ui-superficie)] border border-zinc-200 dark:border-[var(--ui-borde)] rounded-xl p-5 shadow-sm space-y-4 ${className}`}
    >
      <div className="flex items-center justify-between border-b border-zinc-200 dark:border-[var(--ui-borde)] pb-2.5">
        <h3 id={`${idBase}-titulo`} className="text-xs font-bold uppercase tracking-wider text-white flex items-center">
          <FileText className="w-4 h-4 mr-1.5 text-[#3892f3]" />
          Datos para documentos
        </h3>
        {estado.fase === "lista" && (
          <span data-testid="datos-documentales-faltantes" className="text-[10px] text-[var(--ui-texto-suave)]">
            {faltantes === 0 ? "Completos" : `${faltantes} de ${CAMPOS_DOCUMENTALES.length} sin registrar`}
          </span>
        )}
      </div>
      <p className="text-[11px] text-[var(--ui-texto-suave)]">
        La Biblioteca usa estos datos para completar las plantillas de documentos. Los que falten aparecerán marcados en el borrador.
      </p>

      {estado.fase === "cargando" && <p role="status" className="text-xs text-[var(--ui-texto-suave)]">Consultando los datos para documentos…</p>}
      {estado.fase === "error" && (
        <p role="alert" className="text-xs text-amber-700">
          No se pudieron consultar los datos para documentos ({estado.mensaje}).
        </p>
      )}

      {estado.fase === "lista" && borrador && (
        <form
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            void guardar();
          }}
          className="space-y-4"
        >
          {GRUPOS.map(({ grupo, titulo }) => (
            <fieldset key={grupo} className="space-y-3">
              <legend className="text-[11px] font-semibold text-[var(--ui-texto-suave)] mb-1">{titulo}</legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
                {DEFINICION_CAMPOS.filter((d) => d.grupo === grupo).map((d) => {
                  const id = `${idBase}-${d.campo}`;
                  const error = errores[d.campo];
                  const descripcion = error ? `${id}-error` : d.ayuda ? `${id}-ayuda` : undefined;
                  return (
                    <div key={d.campo} className={d.campo === "direccion" ? "sm:col-span-2" : undefined}>
                      <label htmlFor={id} className="block text-[var(--ui-texto-suave)] mb-1 font-medium">
                        {d.etiqueta}
                      </label>
                      <input
                        id={id}
                        name={d.campo}
                        type={d.tipo === "correo" ? "email" : d.tipo === "url" ? "url" : d.tipo === "telefono" ? "tel" : "text"}
                        inputMode={d.tipo === "identificacion" ? "numeric" : undefined}
                        maxLength={d.maximo}
                        readOnly={!puedeEditar}
                        aria-readonly={!puedeEditar}
                        aria-invalid={Boolean(error)}
                        aria-describedby={descripcion}
                        value={borrador[d.campo]}
                        placeholder={puedeEditar ? undefined : "Sin registrar"}
                        onChange={(e) => {
                          setBorrador({ ...borrador, [d.campo]: e.target.value });
                          if (error) setErrores({ ...errores, [d.campo]: undefined });
                        }}
                        className={`w-full bg-zinc-50 dark:bg-[var(--ui-campo)] border rounded-lg px-3 py-2 text-white placeholder-zinc-400 text-xs focus:outline-none focus:border-[#9a3bf1] transition ${
                          error ? "border-red-500" : "border-zinc-300 dark:border-[var(--ui-borde)]"
                        }`}
                      />
                      {error ? (
                        <p id={`${id}-error`} className="mt-1 text-[10px] text-red-600">
                          {error}
                        </p>
                      ) : (
                        d.ayuda && (
                          <p id={`${id}-ayuda`} className="mt-1 text-[10px] text-[var(--ui-texto-suave)] dark:text-zinc-400">
                            {d.ayuda}
                          </p>
                        )
                      )}
                    </div>
                  );
                })}
              </div>
            </fieldset>
          ))}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="text-[11px]" data-testid="datos-documentales-aviso">
              {!puedeEditar && (
                <p className="text-[var(--ui-texto-suave)]">Solo el administrador de la organización puede cambiar estos datos.</p>
              )}
              {aviso && (
                <p role={aviso.tipo === "error" ? "alert" : "status"} className={aviso.tipo === "error" ? "text-red-600" : "text-[#00c853]"}>
                  {aviso.texto}
                </p>
              )}
            </div>
            {puedeEditar && (
              <button
                type="submit"
                disabled={guardando}
                className="text-white px-4 py-2 text-xs font-semibold rounded-lg bg-[#3892f3] hover:opacity-95 transition disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {guardando ? "Guardando…" : "Guardar datos para documentos"}
              </button>
            )}
          </div>
        </form>
      )}
    </section>
  );
}
