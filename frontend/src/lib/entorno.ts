/**
 * Identidad del entorno en el frontend (EP-02, PRD §5.5 y §5.6.1.6). ¤entorno-pruebas
 *
 * El entorno se lee al ejecutar, no al compilar: la misma imagen, con el mismo digest, corre en
 * pruebas, demo y producción (§5.5). El servidor lee `APP_ENV`, el mismo nombre que usa el backend
 * (EP-01), en cada petición. El cliente nunca lee variables de entorno: recibe el valor como prop.
 * Si `APP_ENV` falta o no es válido, se trata como «desconocido»: no se indexa y no hay aviso.
 */

export type Entorno = "development" | "test" | "pruebas" | "demo" | "production";

const ENTORNOS: readonly Entorno[] = ["development", "test", "pruebas", "demo", "production"];

export function normalizarEntorno(valor: unknown): Entorno | null {
  return typeof valor === "string" && (ENTORNOS as readonly string[]).includes(valor)
    ? (valor as Entorno)
    : null;
}

/** Solo en el servidor y en tiempo de ejecución. `null` si `APP_ENV` falta o no es válido. */
export function entornoDelServidor(): Entorno | null {
  return normalizarEntorno(process.env["APP_ENV"]);
}

export function esProduccion(entorno: Entorno | null): boolean {
  return entorno === "production";
}

/** Entornos con datos ficticios que muestran el aviso fijo: `pruebas` y `demo`. */
export function esEntornoDePruebas(entorno: Entorno | null): entorno is "pruebas" | "demo" {
  return entorno === "pruebas" || entorno === "demo";
}
