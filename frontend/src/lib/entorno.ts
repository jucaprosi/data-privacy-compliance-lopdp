/**
 * Identidad del entorno en el navegador (EP-02, PRD §5.5 y §5.6.1.6). ¤entorno-pruebas
 *
 * `NEXT_PUBLIC_APP_ENV` se fija al compilar y solo sirve para la primera pintura y para los
 * metadatos (`robots`). En el navegador manda la respuesta de `GET /api/v1/entorno` (EP-01).
 * Sin la variable, el frontend se comporta como desarrollo.
 */

export type Entorno = "development" | "test" | "pruebas" | "demo" | "production";

const ENTORNOS: readonly Entorno[] = ["development", "test", "pruebas", "demo", "production"];

export function normalizarEntorno(valor: unknown): Entorno | null {
  return typeof valor === "string" && (ENTORNOS as readonly string[]).includes(valor)
    ? (valor as Entorno)
    : null;
}

export function entornoCompilado(): Entorno {
  return normalizarEntorno(process.env.NEXT_PUBLIC_APP_ENV) ?? "development";
}

export function esProduccion(entorno: Entorno = entornoCompilado()): boolean {
  return entorno === "production";
}

/** Entornos con datos ficticios que muestran el aviso fijo: `pruebas` y `demo`. */
export function esEntornoDePruebas(entorno: Entorno = entornoCompilado()): boolean {
  return entorno === "pruebas" || entorno === "demo";
}

/**
 * El aviso consulta `GET /api/v1/entorno` solo donde puede pintarse: en builds `pruebas` o `demo`.
 * En desarrollo, el arnés lo pide con `window.__LOPDP_ENTORNO_PRUEBAS__`, igual que el de
 * identidad (`src/lib/auth/modo.ts`); un build de producción nunca lo atiende.
 */
export function debeConsultarEntorno(entorno: Entorno = entornoCompilado()): boolean {
  if (esEntornoDePruebas(entorno)) return true;
  if (entorno === "production" || typeof window === "undefined") return false;
  return Boolean((window as unknown as { __LOPDP_ENTORNO_PRUEBAS__?: boolean }).__LOPDP_ENTORNO_PRUEBAS__);
}
