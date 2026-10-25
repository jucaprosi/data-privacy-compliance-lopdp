// ¤adpa
// ¤¤developer-architect
/** Cliente común Biblioteca: identidad existente y errores del servidor. */
import { cabecerasDePlataforma } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth";

export class ErrorBiblioteca extends Error {
  constructor(public codigo: string, mensaje: string, public estado: number) { super(mensaje); }
}

export async function httpBiblioteca<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const respuesta = await fetchAutenticado(`/api/v1/biblioteca${ruta}`, {
    ...init, cache: "no-store",
    headers: { "Content-Type": "application/json", ...init.headers },
  }, cabecerasDePlataforma());
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new ErrorBiblioteca(cuerpo?.code ?? "BIB_ERROR_HTTP",
      typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo completar la operación.", respuesta.status);
  }
  return cuerpo as T;
}
