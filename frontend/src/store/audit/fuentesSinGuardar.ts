// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Fuentes de cambios sin guardar ajenas al diagnóstico (BIB-110).
 *
 * El aviso de cambio de organización (FE-21) lee `useAuditStore.cambiosSinGuardar`. Otras salas
 * (Biblioteca) que tengan cambios pendientes se registran aquí con un identificador; mientras haya
 * alguna, `useAuditStore` mantiene `cambiosSinGuardar` en true, sin que el aviso cambie. Es memoria
 * de la pestaña: nunca se persiste, así que no puede heredarla otra organización tras recargar.
 */
type Oyente = (hay: boolean) => void;

const fuentes = new Set<string>();
const oyentes = new Set<Oyente>();

function avisar(antes: boolean): void {
  const ahora = fuentes.size > 0;
  if (ahora !== antes) oyentes.forEach((oyente) => oyente(ahora));
}

/** Marca (o desmarca) que la fuente `id` tiene cambios sin guardar. */
export function marcarFuenteSinGuardar(id: string, hay: boolean): void {
  const antes = fuentes.size > 0;
  if (hay) fuentes.add(id);
  else fuentes.delete(id);
  avisar(antes);
}

/** Olvida todas las fuentes cuyo id empieza por `prefijo` (una sala entera al cambiar de organización). */
export function olvidarFuentesSinGuardar(prefijo: string): void {
  const antes = fuentes.size > 0;
  [...fuentes].filter((id) => id.startsWith(prefijo)).forEach((id) => fuentes.delete(id));
  avisar(antes);
}

export function haySinGuardarExterno(): boolean {
  return fuentes.size > 0;
}

/** Se avisa solo cuando pasa de no haber ninguna a haber alguna, o al revés. Devuelve cómo dejar de oír. */
export function alCambiarFuentesSinGuardar(oyente: Oyente): () => void {
  oyentes.add(oyente);
  return () => oyentes.delete(oyente);
}
