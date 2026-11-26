// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤cita-verificada
// ¤¤frontend-architect
/** BIB-408 · Comparación de una versión con la publicada, por sección y con la cita de cada cambio (BIB-407). */
import { fechaLarga, partirLeyenda, type CambioSeccion, type Comparacion, type Leyenda } from "@/lib/biblioteca/editorial";

/** R2: la versión de la IA no se aprueba si algún cambio tiene una cita sin verificar (o sin cita). */
export const hayCitasSinVerificar = (c: Comparacion | null) =>
  !!c && c.secciones.some(s => s.cambios.some(x => !x.cita || !x.cita.verificada));

export function MotivoDelCambio({ cambio }: { cambio: CambioSeccion }) {
  const cita = cambio.cita;
  if (!cita || !cita.verificada) return <p className="font-medium">Cita sin verificar</p>;
  const texto = [cita.norma, cita.articulo].filter(Boolean).join(", ");
  const vigencia = cita.fecha_vigencia ? ` · entra en vigencia el ${fechaLarga(cita.fecha_vigencia)}` : "";
  return <p>Motivo:{" "}
    {cita.url ? <a href={cita.url} target="_blank" rel="noopener noreferrer" className="underline">{texto}</a> : texto}{vigencia}</p>;
}

export function ComparacionVersion({ comparacion }: { comparacion: Comparacion }) {
  const cambiadas = comparacion.secciones.filter(s => s.cambiada);
  const iguales = comparacion.secciones.filter(s => !s.cambiada);
  if (comparacion.primera_version) {
    return <section aria-label="Comparación" className="grid gap-3">
      <h3 className="font-semibold">Primera versión</h3>
      {comparacion.secciones.map((s, i) => <div key={i} className="grid gap-1">
        {s.titulo && <h4 className="font-medium">{s.titulo}</h4>}
        <p className="whitespace-pre-wrap break-words">{s.texto ?? ""}</p></div>)}
    </section>;
  }
  return <section aria-label="Comparación" className="grid gap-4">
    {cambiadas.map((s, i) => <div key={i} className="grid gap-2">
      <h3 className="font-semibold">{s.titulo || "Encabezado"}</h3>
      {s.cambios.map((c, j) => <div key={j} className="grid gap-2 rounded border border-[var(--ui-borde)] p-3">
        <div><p className="font-medium">Texto actual</p>
          <p className="whitespace-pre-wrap break-words"><del className="bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-100">{c.antes}</del></p></div>
        <div><p className="font-medium">Texto propuesto</p>
          <p className="whitespace-pre-wrap break-words"><ins className="bg-green-100 text-green-900 no-underline dark:bg-green-950 dark:text-green-100">{c.despues}</ins></p></div>
        <MotivoDelCambio cambio={c} />
      </div>)}
    </div>)}
    {iguales.length > 0 && <details>
      <summary>{iguales.length === 1 ? "1 sección sin cambios" : `${iguales.length} secciones sin cambios`}</summary>
      <ul className="list-disc pl-5">{iguales.map((s, i) => <li key={i}>{s.titulo || "Encabezado"}</li>)}</ul>
    </details>}
  </section>;
}

/** BIB-410: la leyenda de redacción y aprobación, con su fecha en `<time datetime>`; sin aprobación registrada no se muestra. */
export function LeyendaNota({ leyenda }: { leyenda: Leyenda | null | undefined }) {
  if (!leyenda) return null;
  const partes = partirLeyenda(leyenda);
  return <p role="note" data-testid="leyenda-version" className="break-words">
    {partes ? <>{partes.antes}<time dateTime={partes.iso}>{partes.fecha}</time>{partes.despues}</> : leyenda.texto}</p>;
}
