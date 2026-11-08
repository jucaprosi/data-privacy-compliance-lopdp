// ¤adpa
// ¤¤frontend-architect
/** BIB-118 · «Tus permisos editoriales»: franja de solo lectura en la cabecera de la Administración editorial. */
import { ETIQUETAS_CAPACIDAD, type CapacidadEditorial } from "@/lib/biblioteca/capacidadesEditoriales";

export const SIN_PERMISOS_EDITORIALES =
  "No tienes permisos editoriales en la Biblioteca. Los asigna el equipo de la plataforma.";

const DESCRIPCION: Record<CapacidadEditorial, string> = {
  editor: "Crea versiones y carga el archivo maestro.",
  revisor_tecnico: "Aprueba o rechaza el contenido técnico.",
  revisor_juridico: "Aprueba o rechaza el contenido jurídico.",
  publicador: "Publica o retira versiones con ambas revisiones aprobadas.",
};
const ORDEN = Object.keys(ETIQUETAS_CAPACIDAD) as CapacidadEditorial[];

export function PermisosEditorialesPropios({ capacidades }: { capacidades: readonly string[] }) {
  const propias = ORDEN.filter((c) => capacidades.includes(c));
  if (propias.length === 0) return <p role="status">{SIN_PERMISOS_EDITORIALES}</p>;
  const recordar = propias.includes("editor") && propias.some((c) => c !== "editor");
  return (
    <section aria-label="Tus permisos editoriales" className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">Tus permisos editoriales</span>
        <ul aria-label="Tus permisos editoriales" className="flex flex-wrap gap-2">
          {propias.map((c) => (
            <li key={c} tabIndex={0} title={DESCRIPCION[c]} aria-description={DESCRIPCION[c]}
              className="rounded-full border border-[var(--ui-borde)] px-2 py-0.5 text-sm">
              {ETIQUETAS_CAPACIDAD[c]}
            </li>
          ))}
        </ul>
      </div>
      {recordar && (
        <p className="text-[var(--ui-texto-suave)]">Recuerda: no puedes revisar ni publicar las versiones que tú creaste.</p>
      )}
    </section>
  );
}
