/**
 * Cliente de la bitácora de incidentes (INC-01). Lee y registra en el servidor; nada se guarda en
 * un archivo ni en el navegador.
 */
import { fetchAutenticado } from "@/lib/auth";
import type { BitacoraIncidentes, Incidente, NuevoIncidente } from "@/types/incidente";
import { cabecerasComo } from "./roles";

const RUTA = "/api/v1/incidentes";

async function errorDe(respuesta: Response, porDefecto: string): Promise<Error> {
  const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: unknown } | null;
  const detalle = cuerpo?.detail;
  if (typeof detalle === "string") return new Error(detalle);
  if (Array.isArray(detalle)) {
    const mensajes = detalle
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: unknown }).msg) : ""))
      .filter(Boolean);
    if (mensajes.length > 0) return new Error(mensajes.join(" · "));
  }
  return new Error(`${porDefecto} (HTTP ${respuesta.status})`);
}

export async function consultarBitacora(rol: string): Promise<BitacoraIncidentes> {
  const respuesta = await fetchAutenticado(RUTA, { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo leer la bitácora de incidentes");
  return (await respuesta.json()) as BitacoraIncidentes;
}

export async function registrarIncidente(rol: string, datos: NuevoIncidente): Promise<Incidente> {
  const respuesta = await fetchAutenticado(
    RUTA,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos) },
    cabecerasComo(rol)
  );
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo registrar el incidente");
  return (await respuesta.json()) as Incidente;
}
