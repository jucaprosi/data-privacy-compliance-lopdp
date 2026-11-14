"use client";
// ¤incidentes
// Campos de los pasos 1 a 6 del asistente de vulneración (INC-02). Solo presentación: el borrador vive
// en el asistente y el servidor valida de nuevo al guardar.
import React from "react";

export type Borrador = Record<string, unknown>;

export const ETIQUETAS: Record<string, string> = {
  fecha_conocimiento: "Fecha en que se conoció",
  detectado_por: "Quién la detectó",
  contacto_dpo: "Contacto del DPO",
  tratamiento_ids: "Tratamientos afectados",
  titulares_aproximados: "Número aproximado de titulares",
  registros_aproximados: "Número aproximado de registros",
  categorias_datos: "Categorías de datos",
  descripcion: "Descripción",
  tipo: "Tipo de vulneración",
  efectos: "Efectos",
  medidas: "Medidas adoptadas",
  recomendaciones_titulares: "Recomendaciones para los titulares",
  resolucion: "Resolución",
};

export const TIPOS: { valor: string; texto: string }[] = [
  { valor: "confidencialidad", texto: "Confidencialidad (alguien accedió a datos sin permiso)" },
  { valor: "integridad", texto: "Integridad (los datos se alteraron sin permiso)" },
  { valor: "disponibilidad", texto: "Disponibilidad (los datos dejaron de estar accesibles)" },
];

const CAMPOS_POR_PASO: Record<number, string[]> = {
  1: ["fecha_conocimiento", "detectado_por", "contacto_dpo"],
  2: ["tratamiento_ids"],
  3: ["titulares_aproximados", "registros_aproximados", "categorias_datos"],
  4: ["descripcion", "tipo"],
  5: ["efectos", "medidas", "recomendaciones_titulares"],
  6: ["resolucion"],
};
const LISTAS = new Set(["tratamiento_ids", "categorias_datos", "lecciones"]);
const NUMEROS = new Set(["titulares_aproximados", "registros_aproximados"]);

function vacio(campo: string, valor: unknown): boolean {
  if (LISTAS.has(campo)) return !Array.isArray(valor) || valor.filter((x) => String(x).trim()).length === 0;
  if (NUMEROS.has(campo)) return valor === undefined || valor === null || valor === "" || Number.isNaN(Number(valor));
  return typeof valor !== "string" || valor.trim() === "";
}

/** Etiquetas de los campos que faltan en el paso (vacío si está completo). */
export function faltantes(paso: number, borrador: Borrador): string[] {
  return (CAMPOS_POR_PASO[paso] ?? []).filter((c) => vacio(c, borrador[c])).map((c) => ETIQUETAS[c]);
}

/** Cuerpo que se envía al servidor para un paso 1 a 6. */
export function cuerpoDe(paso: number, borrador: Borrador): Borrador {
  const salida: Borrador = {};
  for (const campo of [...(CAMPOS_POR_PASO[paso] ?? []), ...(paso === 6 ? ["lecciones"] : [])]) {
    const valor = borrador[campo];
    if (LISTAS.has(campo)) salida[campo] = Array.isArray(valor) ? valor.map((x) => String(x).trim()).filter(Boolean) : [];
    else if (NUMEROS.has(campo)) salida[campo] = valor === "" || valor === undefined ? null : Number(valor);
    else if (campo === "fecha_conocimiento" && typeof valor === "string" && valor) salida[campo] = new Date(valor).toISOString();
    else salida[campo] = typeof valor === "string" ? valor.trim() : valor;
  }
  return salida;
}

const CLASE_CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-2 text-sm text-[var(--ui-texto)] disabled:opacity-60";

interface CampoProps {
  id: string;
  campo: string;
  borrador: Borrador;
  cambiar: (campo: string, valor: unknown) => void;
  soloLectura: boolean;
  ayuda?: string;
  tipo?: "texto" | "area" | "numero" | "fecha" | "lineas";
}

function Campo({ id, campo, borrador, cambiar, soloLectura, ayuda, tipo = "texto" }: CampoProps) {
  const idCampo = `${id}-${campo}`;
  const idAyuda = ayuda ? `${idCampo}-ayuda` : undefined;
  const valor = borrador[campo];
  const comunes = {
    id: idCampo,
    disabled: soloLectura,
    "aria-describedby": idAyuda,
    className: CLASE_CAMPO,
  };
  let control: React.ReactNode;
  if (tipo === "area") {
    control = <textarea {...comunes} rows={3} value={String(valor ?? "")} onChange={(e) => cambiar(campo, e.target.value)} />;
  } else if (tipo === "lineas") {
    control = (
      <textarea
        {...comunes}
        rows={3}
        value={Array.isArray(valor) ? valor.join("\n") : ""}
        onChange={(e) => cambiar(campo, e.target.value.split("\n"))}
      />
    );
  } else {
    control = (
      <input
        {...comunes}
        type={tipo === "numero" ? "number" : tipo === "fecha" ? "datetime-local" : "text"}
        min={tipo === "numero" ? 0 : undefined}
        inputMode={tipo === "numero" ? "numeric" : undefined}
        value={valor === null || valor === undefined ? "" : String(valor)}
        onChange={(e) => cambiar(campo, e.target.value)}
      />
    );
  }
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={idCampo} className="text-sm font-medium">
        {ETIQUETAS[campo]}
        {tipo === "lineas" ? " (uno por línea)" : ""}
      </label>
      {control}
      {ayuda ? (
        <p id={idAyuda} className="text-xs text-[var(--ui-texto-suave)]">
          {ayuda}
        </p>
      ) : null}
    </div>
  );
}

interface PasoProps {
  paso: number;
  borrador: Borrador;
  cambiar: (campo: string, valor: unknown) => void;
  soloLectura: boolean;
}

export function CamposDelPaso({ paso, borrador, cambiar, soloLectura }: PasoProps) {
  const id = `paso-${paso}`;
  const p = { id, borrador, cambiar, soloLectura };
  if (paso === 1)
    return (
      <div className="flex flex-col gap-3">
        <Campo {...p} campo="fecha_conocimiento" tipo="fecha" />
        <Campo {...p} campo="detectado_por" />
        <Campo {...p} campo="contacto_dpo" />
      </div>
    );
  if (paso === 2) return <Campo {...p} campo="tratamiento_ids" tipo="lineas" />;
  if (paso === 3)
    return (
      <div className="flex flex-col gap-3">
        <p id={`${id}-ayuda-general`} className="text-sm text-[var(--ui-texto-suave)]">
          Indica un número aproximado de titulares y de registros; si no lo sabes aún, escribe tu mejor estimación y
          anótalo en la descripción.
        </p>
        <Campo {...p} campo="titulares_aproximados" tipo="numero" />
        <Campo {...p} campo="registros_aproximados" tipo="numero" />
        <Campo {...p} campo="categorias_datos" tipo="lineas" />
      </div>
    );
  if (paso === 4)
    return (
      <div className="flex flex-col gap-3">
        <Campo {...p} campo="descripcion" tipo="area" />
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium">Tipo de vulneración</legend>
          <div role="radiogroup" aria-label="Tipo de vulneración" className="flex flex-col gap-2">
            {TIPOS.map((t) => (
              <label key={t.valor} className="flex items-start gap-2 text-sm">
                <input
                  type="radio"
                  name={`${id}-tipo`}
                  value={t.valor}
                  checked={borrador.tipo === t.valor}
                  disabled={soloLectura}
                  onChange={() => cambiar("tipo", t.valor)}
                />
                <span>{t.texto}</span>
              </label>
            ))}
          </div>
        </fieldset>
      </div>
    );
  if (paso === 5)
    return (
      <div className="flex flex-col gap-3">
        <Campo {...p} campo="efectos" tipo="area" />
        <Campo {...p} campo="medidas" tipo="area" />
        <Campo {...p} campo="recomendaciones_titulares" tipo="area" />
      </div>
    );
  return <PasoResolucion {...p} paso={paso} />;
}

function PasoResolucion({ id, borrador, cambiar, soloLectura }: PasoProps & { id: string }) {
  const lecciones = Array.isArray(borrador.lecciones) ? (borrador.lecciones as string[]) : [];
  return (
    <div className="flex flex-col gap-3">
      <Campo id={id} campo="resolucion" tipo="area" borrador={borrador} cambiar={cambiar} soloLectura={soloLectura} />
      <div className="flex flex-col gap-2">
        <p id={`${id}-lecciones`} className="text-sm font-medium">
          Lecciones aprendidas
        </p>
        <p className="text-xs text-[var(--ui-texto-suave)]">Cada lección se guarda como un hallazgo del plan de acción.</p>
        <ul aria-labelledby={`${id}-lecciones`} className="flex flex-col gap-2">
          {lecciones.map((texto, i) => (
            <li key={i}>
              <label className="sr-only" htmlFor={`${id}-leccion-${i}`}>
                Lección {i + 1}
              </label>
              <input
                id={`${id}-leccion-${i}`}
                className={CLASE_CAMPO}
                value={texto}
                disabled={soloLectura}
                onChange={(e) => cambiar("lecciones", lecciones.map((x, j) => (j === i ? e.target.value : x)))}
              />
            </li>
          ))}
        </ul>
        {soloLectura ? null : (
          <button
            type="button"
            onClick={() => cambiar("lecciones", [...lecciones, ""])}
            className="self-start rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]"
          >
            Añadir lección
          </button>
        )}
      </div>
    </div>
  );
}
