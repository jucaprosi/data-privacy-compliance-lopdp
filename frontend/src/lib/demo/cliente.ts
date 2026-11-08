/**
 * Cliente de la API de la demo (DEMO-04). ¤demo
 *
 * Habla solo con las rutas congeladas de FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.7. Todo pasa por
 * `fetchAutenticado`, que lleva la identidad y convierte un 401 DEMO_VENCIDA en la pantalla de fin.
 */
import { cabecerasDeTenant } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { RUTAS_DEMO, type CodigoErrorDemo, type EstadoDemo, type PersonaDemo } from "./contrato";
import { guardarPersonaActiva } from "./estado";

export type Resultado<T> = { ok: true; valor: T } | { ok: false; status: number; codigo: CodigoErrorDemo | null };

async function codigoDe(r: Response): Promise<CodigoErrorDemo | null> {
  try {
    const cuerpo = (await r.json()) as { codigo?: string; detail?: { codigo?: string } };
    const codigo = cuerpo?.codigo ?? cuerpo?.detail?.codigo;
    return typeof codigo === "string" ? (codigo as CodigoErrorDemo) : null;
  } catch {
    return null;
  }
}

async function leer<T>(r: Response): Promise<Resultado<T>> {
  if (r.ok) return { ok: true, valor: (await r.json()) as T };
  return { ok: false, status: r.status, codigo: await codigoDe(r) };
}

const JSON_POST = (cuerpo?: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json", Accept: "application/json" },
  body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  cache: "no-store",
});

/** `true` solo si el backend confirma `entorno = demo`. Ante la duda, no hay demo. */
export async function entornoEsDemo(): Promise<boolean> {
  try {
    const r = await fetch(RUTAS_DEMO.entorno, { headers: { Accept: "application/json" }, cache: "no-store" });
    if (!r.ok) return false;
    const cuerpo = (await r.json()) as { entorno?: unknown };
    return cuerpo?.entorno === "demo";
  } catch {
    return false;
  }
}

export async function consultarEstado(): Promise<Resultado<EstadoDemo>> {
  try {
    const r = await fetchAutenticado(RUTAS_DEMO.estado, { headers: { Accept: "application/json" }, cache: "no-store" });
    const res = await leer<EstadoDemo>(r);
    if (res.ok) guardarPersonaActiva(res.valor.persona_activa);
    return res;
  } catch {
    return { ok: false, status: 0, codigo: null };
  }
}

/** Pide al servidor la persona y adopta la que devuelve. */
export async function cambiarPersona(persona_usuario_id: string): Promise<Resultado<PersonaDemo>> {
  try {
    const r = await fetchAutenticado(RUTAS_DEMO.persona, JSON_POST({ persona_usuario_id }));
    const res = await leer<{ persona_activa?: PersonaDemo } & Partial<PersonaDemo>>(r);
    if (!res.ok) return res;
    const persona = (res.valor.persona_activa ?? res.valor) as PersonaDemo;
    guardarPersonaActiva(persona);
    return { ok: true, valor: persona };
  } catch {
    return { ok: false, status: 0, codigo: null };
  }
}

/** Un 401 DEMO_VENCIDA cuenta como éxito: ya estaba cerrada. */
export async function terminarDemo(): Promise<boolean> {
  try {
    const init = JSON_POST();
    const r = await fetch(RUTAS_DEMO.terminar, {
      ...init,
      headers: { ...cabecerasDeTenant(), ...(init.headers as Record<string, string>) },
    });
    return r.ok || r.status === 401;
  } catch {
    return false;
  }
}

/** Entrada con el token de Google; el servidor copia la plantilla y responde una sola vez. */
export async function entrarEnDemo(token: string, senal?: AbortSignal): Promise<Resultado<EstadoDemo>> {
  try {
    const init = JSON_POST();
    const r = await fetch(RUTAS_DEMO.entrar, {
      ...init,
      headers: { ...(init.headers as Record<string, string>), Authorization: `Bearer ${token}` },
      signal: senal,
    });
    return await leer<EstadoDemo>(r);
  } catch {
    return { ok: false, status: 503, codigo: "DEMO_NO_DISPONIBLE" };
  }
}
