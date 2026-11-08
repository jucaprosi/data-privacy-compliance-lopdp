"use client";

/**
 * Bloque de la entrada en modo demo (DEMO-04, UX_DEMO_EVYDENTIA §4 y §5). ¤demo
 *
 * La pantalla de login le pasa la credencial de Google (`registrar`); este bloque llama a
 * `POST /api/v1/demo/entrar`, muestra los cinco pasos por tiempo y los errores en línea.
 * Fuera de `demo` (según `GET /api/v1/entorno`) no pinta nada ni recibe credenciales.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import {
  PASOS_DE_ENTRADA,
  TEXTOS_DEMO,
  TEXTO_DE_ERROR,
  TIEMPOS_DE_ENTRADA,
  type CodigoErrorDemo,
} from "@/lib/demo/contrato";
import { entornoEsDemo, entrarEnDemo } from "@/lib/demo/cliente";
import { guardarPersonaActiva, marcarBienvenida } from "@/lib/demo/estado";
import { leerCredencial } from "@/lib/auth/sesion";
import { entrarEnOrganizacion } from "@/store/datosDeTrabajo";
import PantallaDemoMensaje from "./PantallaDemoMensaje";

/** Resuelve true si tomó la credencial (hay demo); false si la entrada normal debe seguir. */
export type ReceptorDeCredencial = (credential: string) => Promise<boolean>;

/**
 * Señal sin red: el servidor solo pinta el aviso en `demo` si su APP_ENV lo es. Sin ella (producción,
 * sin entorno) no se consulta nada; con ella, `GET /api/v1/entorno` confirma al recibir la credencial.
 */
function avisoDiceDemo(): boolean {
  return document.querySelector('[data-testid="aviso-entorno"][data-entorno="demo"]') !== null;
}

interface Props {
  registrar: (receptor: ReceptorDeCredencial | null) => void;
}

type Fase = { tipo: "inactiva" } | { tipo: "cargando"; paso: number; tardando: boolean } | { tipo: "error"; codigo: CodigoErrorDemo };

export default function EntradaDemo({ registrar }: Props) {
  const [demo, setDemo] = useState(false);
  const [terminada, setTerminada] = useState(false);
  const [fase, setFase] = useState<Fase>({ tipo: "inactiva" });
  const [fallos503, setFallos503] = useState(0);
  const [espera409, setEspera409] = useState(false);
  const token = useRef<string | null>(null);
  const enCurso = useRef(false);

  const intentar = useCallback(async () => {
    const credential = token.current;
    if (!credential || enCurso.current) return;
    enCurso.current = true;
    setFase({ tipo: "cargando", paso: 0, tardando: false });
    const inicio = Date.now();
    const control = new AbortController();
    const reloj = setInterval(() => {
      const t = Date.now() - inicio;
      setFase((f) =>
        f.tipo === "cargando"
          ? {
              tipo: "cargando",
              paso: Math.min(PASOS_DE_ENTRADA.length - 1, Math.floor(t / TIEMPOS_DE_ENTRADA.pasoMs)),
              tardando: t > TIEMPOS_DE_ENTRADA.tardandoMs,
            }
          : f,
      );
    }, 250);
    const limite = setTimeout(() => control.abort(), TIEMPOS_DE_ENTRADA.limiteMs);
    const r = await entrarEnDemo(credential, control.signal);
    clearInterval(reloj);
    clearTimeout(limite);
    enCurso.current = false;

    if (r.ok) {
      const credencial = leerCredencial(credential);
      const { organizacion, persona_activa } = r.valor;
      guardarPersonaActiva(persona_activa);
      marcarBienvenida();
      entrarEnOrganizacion(credential, credencial?.email ?? "", {
        tenant_id: organizacion.tenant_id,
        nombre_comercial: organizacion.nombre,
        roles: [persona_activa.rol],
      });
      window.location.assign("/dashboard");
      return;
    }
    const codigo: CodigoErrorDemo =
      r.codigo === "DEMO_NO_AUTORIZADO" || r.codigo === "DEMO_OCUPADA" ? r.codigo : "DEMO_NO_DISPONIBLE";
    if (codigo === "DEMO_NO_DISPONIBLE") setFallos503((n) => n + 1);
    else setFallos503(0);
    if (codigo === "DEMO_OCUPADA") setEspera409(true);
    setFase({ tipo: "error", codigo });
  }, []);

  useEffect(() => {
    setTerminada(new URLSearchParams(window.location.search).get("demo") === "terminada");
    const posible = avisoDiceDemo();
    setDemo(posible);
    registrar(
      posible
        ? async (credential) => {
            if (enCurso.current) return true;
            if (!(await entornoEsDemo())) {
              setDemo(false);
              return false;
            }
            token.current = credential;
            void intentar();
            return true;
          }
        : null,
    );
    return () => {
      registrar(null);
    };
  }, [registrar, intentar]);

  useEffect(() => {
    if (!espera409) return;
    const t = setTimeout(() => setEspera409(false), 30_000);
    return () => clearTimeout(t);
  }, [espera409]);

  if (!demo && !terminada) return null;

  return (
    <div className="flex w-full flex-col items-center gap-3" data-testid="demo-entrada">
      {terminada && (
        <p role="status" data-testid="demo-terminada" className="w-full rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {TEXTOS_DEMO.terminada}
        </p>
      )}
      {demo && fase.tipo === "inactiva" && (
        <div className="text-center">
          <h2 className="text-base font-semibold">Demostración de EVYDENTIA</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Recorre la plataforma con una cooperativa ficticia. Nada de lo que hagas afecta datos reales.
          </p>
        </div>
      )}
      {fase.tipo === "cargando" && (
        <div role="status" aria-live="polite" data-testid="demo-progreso" className="w-full">
          <ol className="flex flex-col gap-1.5 text-sm">
            {PASOS_DE_ENTRADA.map((texto, i) => (
              <li key={texto} className={`flex items-center gap-2 ${i > fase.paso ? "text-zinc-400" : ""}`}>
                {i < fase.paso ? (
                  <Check aria-hidden="true" className="h-4 w-4 text-emerald-600" />
                ) : i === fase.paso ? (
                  <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
                ) : (
                  <span aria-hidden="true" className="h-4 w-4" />
                )}
                <span aria-current={i === fase.paso ? "step" : undefined}>{texto}</span>
              </li>
            ))}
          </ol>
          {fase.tardando && <p className="mt-2 text-xs text-zinc-500">{TEXTOS_DEMO.tardando}</p>}
        </div>
      )}
      {fase.tipo === "error" && (
        <PantallaDemoMensaje
          codigo={fase.codigo}
          titulo={TEXTO_DE_ERROR[fase.codigo]}
          extra={fase.codigo === "DEMO_NO_DISPONIBLE" && fallos503 >= 3 ? TEXTOS_DEMO.sigueFallando : null}
          accion={
            fase.codigo === "DEMO_NO_AUTORIZADO" ? (
              <button
                type="button"
                onClick={() => {
                  token.current = null;
                  setFase({ tipo: "inactiva" });
                }}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm"
              >
                Usar otra cuenta
              </button>
            ) : (
              <button
                type="button"
                data-testid="demo-reintentar"
                disabled={fase.codigo === "DEMO_OCUPADA" && espera409}
                onClick={() => void intentar()}
                className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
              >
                {fase.codigo === "DEMO_OCUPADA" ? "Reintentar" : "Intentar de nuevo"}
              </button>
            )
          }
        />
      )}
    </div>
  );
}
