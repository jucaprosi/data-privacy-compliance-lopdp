// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
"use client";
/**
 * BIB-414 · Diálogo «Conceder capacidad a {nombre}» y «Retirar {capacidad} a {nombre}» (UX/UI §2 y §6).
 * Foco inicial en «Cancelar»; Escape cierra; el foco vuelve al botón que lo abrió. El motivo es obligatorio
 * (al menos 10 caracteres): sin él no se envía nada. Los errores salen con su texto fijo, nunca el del servidor.
 */
import { useEffect, useRef, useState, type FormEvent } from "react";
import { DESCRIPCION } from "@/components/biblioteca/editorial/PermisosEditorialesPropios";
import { ETIQUETAS_CAPACIDAD } from "@/lib/biblioteca/capacidadesEditoriales";
import {
  CAPACIDADES_CONCEDIBLES, MOTIVO_MINIMO, TEXTO_CAPACIDAD, TEXTO_MOTIVO, TEXTO_SIN_VIGENTE, TEXTO_VIGENTE,
  conceder, retirar, textoDeError, type CapacidadConcedible, type MiembroEquipo,
} from "@/lib/plataforma/capacidadesEditoriales";

export type Modo = { tipo: "conceder" } | { tipo: "retirar"; capacidad: CapacidadConcedible };

const minuscula = (c: CapacidadConcedible) => ETIQUETAS_CAPACIDAD[c].toLowerCase();

export default function DialogoCapacidad({ miembro, modo, onCerrar, onHecho }: {
  miembro: MiembroEquipo; modo: Modo; onCerrar: () => void; onHecho: () => void;
}) {
  const cancelar = useRef<HTMLButtonElement>(null);
  const [elegidas, setElegidas] = useState<CapacidadConcedible[]>([]);
  const [motivo, setMotivo] = useState("");
  const [errorMotivo, setErrorMotivo] = useState(false);
  const [error, setError] = useState("");
  const [estado, setEstado] = useState("");
  const [ocupada, setOcupada] = useState(false);
  const [hecho, setHecho] = useState(false);

  useEffect(() => { cancelar.current?.focus(); }, []);
  useEffect(() => {
    const cerrar = (e: KeyboardEvent) => { if (e.key === "Escape") onCerrar(); };
    document.addEventListener("keydown", cerrar);
    return () => document.removeEventListener("keydown", cerrar);
  }, [onCerrar]);

  const esConceder = modo.tipo === "conceder";
  const titulo = esConceder ? `Conceder capacidad a ${miembro.nombre}` : `Retirar ${minuscula(modo.capacidad)} a ${miembro.nombre}`;
  const aviso = esConceder && elegidas.includes("editor") && elegidas.some((c) => c !== "editor");

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(""); setEstado("");
    if (motivo.trim().length < MOTIVO_MINIMO) { setErrorMotivo(true); return; }
    setErrorMotivo(false);
    const capacidades = esConceder ? elegidas : [modo.capacidad];
    if (capacidades.length === 0) { setError(TEXTO_CAPACIDAD); return; }
    setOcupada(true);
    try {
      const repetidas: string[] = [];
      for (const capacidad of capacidades) {
        const resultado = esConceder ? await conceder(miembro.usuario_id, capacidad, motivo.trim())
          : await retirar(miembro.usuario_id, capacidad, motivo.trim());
        if (resultado === "vigente") repetidas.push(TEXTO_VIGENTE);
        if (resultado === "sin_vigente") repetidas.push(TEXTO_SIN_VIGENTE);
      }
      setHecho(true);
      setEstado(repetidas.length ? repetidas[0]
        : esConceder ? `Capacidad concedida a ${miembro.nombre}.` : `Capacidad retirada a ${miembro.nombre}.`);
      onHecho();
    } catch (err) {
      setError(textoDeError(err));
    } finally {
      setOcupada(false);
    }
  }

  return <div className="fixed inset-0 z-50 grid place-items-center bg-[color-mix(in_srgb,var(--foreground)_50%,transparent)] p-4">
    <div role="dialog" aria-modal="true" aria-labelledby="titulo-dialogo-capacidad"
      className="grid max-h-full w-full max-w-lg gap-3 overflow-y-auto rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5">
      <h2 id="titulo-dialogo-capacidad" className="text-lg font-semibold">{titulo}</h2>
      {error && <p role="alert" className="rounded border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] p-3 text-[var(--ui-error-texto)]">{error}</p>}
      {hecho ? <p role="status">{estado}</p> : <form className="grid gap-3" onSubmit={enviar} noValidate>
        {esConceder && <fieldset className="grid gap-2">
          <legend className="font-medium">Capacidades</legend>
          {CAPACIDADES_CONCEDIBLES.map((c) => <label key={c} className="flex items-start gap-2">
            <input type="checkbox" checked={elegidas.includes(c)} className="mt-1"
              onChange={(e) => setElegidas(e.target.checked ? [...elegidas, c] : elegidas.filter((x) => x !== c))} />
            <span><span className="font-medium">{ETIQUETAS_CAPACIDAD[c]}</span>
              <span className="block text-sm text-[var(--ui-texto-suave)]">{DESCRIPCION[c]}</span></span>
          </label>)}
        </fieldset>}
        {aviso && <p role="status" className="rounded border border-[var(--ui-aviso-borde)] bg-[var(--ui-aviso-fondo)] p-3 text-[var(--ui-aviso-texto)]">Recuerda: nadie puede revisar ni publicar las versiones que creó.</p>}
        <label className="grid gap-1">Motivo
          <span id="ayuda-motivo-capacidad" className="text-sm text-[var(--ui-texto-suave)]">
            {esConceder ? "Explica por qué se concede. Queda en el historial." : "Explica por qué se retira. Queda en el historial."}
          </span>
          <textarea className="rounded border p-2" value={motivo} maxLength={4000} aria-describedby="ayuda-motivo-capacidad"
            aria-invalid={errorMotivo} onChange={(e) => setMotivo(e.target.value)} />
        </label>
        {errorMotivo && <p role="alert" className="rounded border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] p-3 text-[var(--ui-error-texto)]">{TEXTO_MOTIVO}</p>}
        <div className="flex gap-3">
          <button ref={cancelar} type="button" onClick={onCerrar} className="rounded border p-2">Cancelar</button>
          <button disabled={ocupada} className="rounded bg-[var(--ui-primario)] p-2 text-[var(--ui-primario-texto)]">
            {esConceder ? "Conceder" : "Retirar"}</button>
        </div>
      </form>}
      {hecho && <button ref={cancelar} type="button" onClick={onCerrar} className="justify-self-start rounded border p-2">Cerrar</button>}
    </div>
  </div>;
}
