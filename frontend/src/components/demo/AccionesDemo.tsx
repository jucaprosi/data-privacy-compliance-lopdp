"use client";

/**
 * Ranura `acciones` del aviso de entorno en la demo (DEMO-04, UX_DEMO_EVYDENTIA §2 y §3). ¤demo
 *
 * Se monta solo si `GET /api/v1/entorno` dice `demo` y `GET /api/v1/demo/estado` responde 200.
 * La persona la decide el servidor: la interfaz pide el cambio y adopta lo que vuelve.
 */
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Check, ChevronDown, Loader2, LogOut } from "lucide-react";
import {
  LINEA_DE_ROL,
  RECORRIDO_SUGERIDO,
  ROL_CORTO,
  TEXTOS_DEMO,
  TEXTO_DE_ERROR,
  etiquetaDePersona,
  iniciales,
  ordenarPersonas,
  type PersonaDemo,
} from "@/lib/demo/contrato";
import { cambiarPersona, terminarDemo } from "@/lib/demo/cliente";
import { olvidarPersonaActiva, tomarBienvenida } from "@/lib/demo/estado";
import { useDemo } from "@/lib/demo/store";
import { cerrarSesion } from "@/lib/auth/sesion";
import PantallaDemoMensaje from "./PantallaDemoMensaje";

const RUTA_ENTRADA = "/login";

function Toast({ texto, alCerrar }: { texto: string; alCerrar: () => void }) {
  useEffect(() => {
    const t = setTimeout(alCerrar, 6000);
    return () => clearTimeout(t);
  }, [alCerrar]);
  return (
    <div
      role="status"
      data-testid="demo-toast"
      className="fixed bottom-4 left-1/2 z-[90] w-[min(92vw,420px)] -translate-x-1/2 rounded-lg bg-zinc-900 px-4 py-3 text-sm text-white shadow-lg"
    >
      {texto}
    </div>
  );
}

function DialogoTerminar({ alCancelar }: { alCancelar: () => void }) {
  const cancelarRef = useRef<HTMLButtonElement>(null);
  const [terminando, setTerminando] = useState(false);
  useEffect(() => cancelarRef.current?.focus(), []);

  const confirmar = async () => {
    setTerminando(true);
    await terminarDemo();
    olvidarPersonaActiva();
    cerrarSesion();
    window.location.assign(`${RUTA_ENTRADA}?demo=terminada`);
  };

  return (
    <div className="fixed inset-0 z-[85] flex items-center justify-center bg-black/30 px-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="demo-terminar-titulo"
        aria-describedby="demo-terminar-cuerpo"
        data-testid="demo-terminar-dialogo"
        className="w-full max-w-[420px] rounded-xl bg-white p-6 text-zinc-800 shadow-xl"
        onKeyDown={(e) => e.key === "Escape" && !terminando && alCancelar()}
      >
        <h2 id="demo-terminar-titulo" className="text-base font-semibold">
          {TEXTOS_DEMO.confirmarTitulo}
        </h2>
        <p id="demo-terminar-cuerpo" className="mt-2 text-sm text-zinc-600">
          {TEXTOS_DEMO.confirmarCuerpo}
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            ref={cancelarRef}
            type="button"
            disabled={terminando}
            onClick={alCancelar}
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={terminando}
            onClick={confirmar}
            data-testid="demo-terminar-confirmar"
            className="inline-flex items-center gap-1.5 rounded-md bg-red-700 px-3 py-1.5 text-sm text-white"
          >
            {terminando && <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />}
            {terminando ? "Terminando…" : "Terminar demo"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Avatar({ persona }: { persona: PersonaDemo }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#7A5A00] text-[10px] font-semibold text-white"
    >
      {iniciales(persona.nombre)}
    </span>
  );
}

export default function AccionesDemo() {
  const router = useRouter();
  const { cargado, estado, vencida, iniciar, refrescar, adoptar } = useDemo();
  const [abierto, setAbierto] = useState(false);
  const [cambiando, setCambiando] = useState<string | null>(null);
  const [error, setError] = useState<"ajena" | "otro" | null>(null);
  const [confirmar, setConfirmar] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const contenedor = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void iniciar();
  }, [iniciar]);

  useEffect(() => {
    if (estado && tomarBienvenida()) setToast(TEXTOS_DEMO.bienvenida);
  }, [estado]);

  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => {
      if (contenedor.current && !contenedor.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", fuera);
    return () => document.removeEventListener("mousedown", fuera);
  }, [abierto]);

  if (vencida) {
    return (
      <PantallaDemoMensaje
        completa
        codigo="DEMO_VENCIDA"
        titulo={TEXTO_DE_ERROR.DEMO_VENCIDA}
        texto={TEXTOS_DEMO.vencidaDetalle}
        accion={
          <button
            type="button"
            onClick={() => {
              cerrarSesion();
              window.location.assign(RUTA_ENTRADA);
            }}
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white"
          >
            Empezar una nueva
          </button>
        }
      />
    );
  }
  if (!cargado || !estado) return null;

  const activa = estado.persona_activa;
  const personas = ordenarPersonas(estado.personas);

  const elegir = async (persona: PersonaDemo) => {
    if (cambiando || persona.usuario_id === activa.usuario_id) return;
    setError(null);
    setCambiando(persona.usuario_id);
    const r = await cambiarPersona(persona.usuario_id);
    setCambiando(null);
    if (r.ok) {
      adoptar(r.valor);
      setAbierto(false);
      setToast(`Ahora ves la plataforma como ${r.valor.rol_etiqueta}`);
      router.refresh();
    } else if (r.codigo === "DEMO_PERSONA_AJENA") {
      setError("ajena");
    } else if (r.codigo !== "DEMO_VENCIDA") {
      setError("otro");
    }
  };

  const recorrido = () => {
    const primera = personas.find((p) => p.rol === RECORRIDO_SUGERIDO[0]);
    if (primera) void elegir(primera);
  };

  return (
    <div ref={contenedor} className="relative flex items-center gap-2" data-testid="demo-acciones">
      <button
        type="button"
        data-testid="demo-ver-como"
        aria-haspopup="listbox"
        aria-expanded={abierto}
        aria-label={`Ver como: ${activa.nombre} · ${etiquetaDePersona(activa)}`}
        onClick={() => setAbierto((v) => !v)}
        className="inline-flex h-6 items-center gap-1.5 rounded px-1.5 hover:bg-black/5 focus-visible:outline focus-visible:outline-2"
      >
        <Avatar persona={activa} />
        <span className="hidden lg:inline" data-testid="demo-persona-activa">
          Ver como: {activa.nombre} · {activa.rol_etiqueta}
        </span>
        <span className="hidden sm:inline lg:hidden">{ROL_CORTO[activa.rol]}</span>
        <ChevronDown aria-hidden="true" className="h-3.5 w-3.5" />
      </button>

      <button
        type="button"
        data-testid="demo-terminar"
        onClick={() => setConfirmar(true)}
        aria-label="Terminar demo"
        className="hidden h-6 items-center gap-1 rounded px-1.5 underline-offset-2 hover:underline sm:inline-flex"
      >
        <LogOut aria-hidden="true" className="h-3.5 w-3.5 lg:hidden" />
        <span className="hidden lg:inline">Terminar demo</span>
      </button>

      {abierto && (
        <div
          data-testid="demo-panel"
          className="fixed inset-x-0 bottom-0 z-[70] rounded-t-xl border border-zinc-200 bg-white p-3 text-zinc-800 shadow-xl sm:absolute sm:inset-x-auto sm:bottom-auto sm:right-0 sm:top-7 sm:w-[360px] sm:rounded-xl"
        >
          <p className="px-2 pb-2 text-xs font-semibold text-zinc-500">Ver la plataforma como…</p>
          <ul role="listbox" aria-label="Personas de la demostración" className="flex flex-col">
            {personas.map((p) => {
              const seleccionada = p.usuario_id === activa.usuario_id;
              return (
                <li key={p.usuario_id} role="option" aria-selected={seleccionada}>
                  <button
                    type="button"
                    data-testid="demo-persona"
                    data-rol={p.rol}
                    disabled={cambiando !== null && cambiando !== p.usuario_id}
                    onClick={() => void elegir(p)}
                    className="flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left hover:bg-zinc-50 disabled:opacity-50"
                  >
                    <Avatar persona={p} />
                    <span className="min-w-0 flex-1">
                      <span className="flex justify-between gap-2 text-sm">
                        <span className="font-medium">{p.nombre}</span>
                        <span className="text-zinc-500" data-testid="demo-persona-rol">
                          {etiquetaDePersona(p)}
                        </span>
                      </span>
                      <span className="block text-xs text-zinc-500">{LINEA_DE_ROL[p.rol]}</span>
                    </span>
                    {cambiando === p.usuario_id ? (
                      <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
                    ) : (
                      seleccionada && <Check aria-hidden="true" className="h-4 w-4" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
          {error && (
            <div role="alert" className="mt-2 flex items-center gap-2 px-2 text-xs text-red-700" data-testid="demo-panel-error">
              <AlertCircle aria-hidden="true" className="h-4 w-4 shrink-0" />
              <span>{error === "ajena" ? `${TEXTO_DE_ERROR.DEMO_PERSONA_AJENA}.` : TEXTOS_DEMO.errorCambio}</span>
              {error === "ajena" && (
                <button type="button" className="underline" onClick={() => void refrescar()}>
                  Actualizar
                </button>
              )}
            </div>
          )}
          <button
            type="button"
            data-testid="demo-recorrido"
            onClick={recorrido}
            className="mt-2 w-full border-t border-zinc-100 px-2 pt-2 text-left text-xs text-[#7A5A00] underline-offset-2 hover:underline"
          >
            Recorrido sugerido: Responsable de área → Coordinador → DPO → Auditor
          </button>
          <button
            type="button"
            data-testid="demo-terminar-panel"
            onClick={() => setConfirmar(true)}
            className="mt-2 w-full rounded-md border border-zinc-200 px-2 py-1.5 text-sm sm:hidden"
          >
            Terminar demo
          </button>
        </div>
      )}

      {confirmar && <DialogoTerminar alCancelar={() => setConfirmar(false)} />}
      {toast && <Toast texto={toast} alCerrar={() => setToast(null)} />}
    </div>
  );
}

/** Ranura `organizacion`: texto plano, registrada para la cuenta profesional (§5.6.6). */
export function OrganizacionDemo() {
  const estado = useDemo((s) => s.estado);
  if (!estado) return null;
  return <span data-testid="demo-organizacion">{estado.organizacion.nombre}</span>;
}
