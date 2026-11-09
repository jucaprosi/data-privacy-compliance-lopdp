"use client";

// ¤adpa ¤rbac-tenant
import React from "react";
import { listarEnlaces, type EnlaceDocumento } from "@/lib/biblioteca/enlaces";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  TEXTO_VEREDICTO, huellaDeArchivo, obtenerExpediente, registrarEvidencia, registrarVerificacion,
  type Expediente, type NuevaEvidencia,
} from "@/lib/biblioteca/verificacion";

const campo = "rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1";
const hoy = () => new Date().toISOString().slice(0, 10);

export default function PanelVerificacion() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [enlaces, setEnlaces] = React.useState<EnlaceDocumento[]>([]);
  const [accionId, setAccionId] = React.useState("");
  const [expediente, setExpediente] = React.useState<Expediente | null>(null);
  const [mensaje, setMensaje] = React.useState("");
  const [evidencia, setEvidencia] = React.useState({
    titulo: "", version: "1.0", sha256: "", clasificacion: "interna" as NuevaEvidencia["clasificacion"],
    permisos: "coordinador", fecha: hoy(),
  });
  const [revision, setRevision] = React.useState({
    evidencia_id: "", criterio: "", evidencia_legible: false, resultado: "no_conforme" as "conforme" | "no_conforme",
    eficacia_requerida: false, eficacia_conforme: false, fecha: hoy(), observaciones: "",
  });

  React.useEffect(() => {
    if (!documentoId) return;
    listarEnlaces(documentoId).then((lista) => {
      setEnlaces(lista);
      if (lista[0]) setAccionId((actual) => actual || lista[0].accion_id);
    }).catch(() => setEnlaces([]));
  }, [documentoId]);

  const cargar = React.useCallback(async (id: string) => {
    if (!id) return;
    try {
      const datos = await obtenerExpediente(id);
      setExpediente(datos);
      setRevision((r) => ({ ...r, evidencia_id: r.evidencia_id || datos.evidencias.at(-1)?.id || "" }));
      setMensaje("");
    } catch (error) {
      setExpediente(null);
      setMensaje(error instanceof Error ? error.message : "No se pudo consultar el expediente.");
    }
  }, []);

  React.useEffect(() => { void cargar(accionId); }, [accionId, cargar]);
  if (!documentoId) return null;

  const ejecutar = async (accion: () => Promise<unknown>) => {
    try { await accion(); await cargar(accionId); } catch (error) {
      setMensaje(error instanceof Error ? error.message : "No se pudo guardar.");
    }
  };

  const guardarEvidencia = () => ejecutar(() => registrarEvidencia(accionId, {
    ...evidencia, permisos: evidencia.permisos.split(",").map((p) => p.trim()).filter(Boolean),
  }));
  const guardarVerificacion = () => ejecutar(() => registrarVerificacion(accionId, {
    ...revision, eficacia_conforme: revision.eficacia_requerida ? revision.eficacia_conforme : null,
    observaciones: revision.observaciones || undefined,
  }));

  return (
    <section aria-label="Evidencias y verificación" className="mt-2 rounded-md border border-[var(--ui-borde)] p-3">
      <h4 className="font-semibold">Evidencias y verificación</h4>
      <p className="text-[11px] text-[var(--ui-texto-suave)]">
        Un documento aprobado no equivale a implementación. La huella comprueba que el archivo no cambió desde que se registró; la acción
        solo se cierra con una verificación conforme registrada por otra persona.
      </p>
      <label className="mt-2 flex flex-wrap items-center gap-2">
        <span>Acción</span>
        <input aria-label="Acción a verificar" list="acciones-verificables" value={accionId}
          onChange={(e) => setAccionId(e.target.value)} className={`min-w-56 ${campo}`} />
        <datalist id="acciones-verificables">
          {enlaces.map((e) => <option key={e.id} value={e.accion_id}>{e.accion_titulo}</option>)}
        </datalist>
      </label>
      {mensaje && <p role="status" className="mt-2 text-red-600">{mensaje}</p>}
      {expediente && (
        <>
          <p data-testid="veredicto" className="mt-2 font-medium">{TEXTO_VEREDICTO[expediente.veredicto]}</p>
          <ul aria-label="Evidencias registradas" className="mt-2 space-y-1">
            {expediente.evidencias.map((ev) => (
              <li key={ev.id} className="rounded border border-[var(--ui-borde)] p-2">
                <strong>{ev.titulo}</strong> · versión {ev.version} · {ev.clasificacion} · {ev.fecha}
                <br />Huella de integridad (SHA-256) {ev.sha256.slice(0, 12)}… · permisos {ev.permisos.join(", ")}
                {ev.control_ref && <> · control {ev.control_ref}</>}
              </li>
            ))}
          </ul>
          <ol aria-label="Historial de verificaciones" className="mt-2 space-y-1">
            {expediente.verificaciones.map((v) => (
              <li key={v.id} className="rounded border border-[var(--ui-borde)] p-2">
                {v.fecha} · {v.resultado === "conforme" ? "Conforme" : "No conforme"} · revisor {v.revisor}
                <br />Criterio: {v.criterio} · legible {v.evidencia_legible ? "sí" : "no"}
                {v.eficacia_requerida && <> · eficacia {v.eficacia_conforme ? "conforme" : "no conforme"}</>}
                {v.observaciones && <><br />{v.observaciones}</>}
              </li>
            ))}
          </ol>
          <fieldset className="mt-3 flex flex-wrap gap-2 border-t border-[var(--ui-borde)] pt-2">
            <legend className="font-medium">Registrar evidencia</legend>
            <input aria-label="Título de la evidencia" value={evidencia.titulo} className={campo}
              onChange={(e) => setEvidencia({ ...evidencia, titulo: e.target.value })} />
            <input aria-label="Versión" value={evidencia.version} className={`w-20 ${campo}`}
              onChange={(e) => setEvidencia({ ...evidencia, version: e.target.value })} />
            <input aria-label="Archivo de evidencia" type="file" onChange={(e) => {
              const archivo = e.target.files?.[0];
              if (archivo) void huellaDeArchivo(archivo).then((sha256) => setEvidencia((v) => ({ ...v, sha256 })));
            }} />
            <input aria-label="Huella de integridad (SHA-256)" value={evidencia.sha256} className={`min-w-72 ${campo}`}
              onChange={(e) => setEvidencia({ ...evidencia, sha256: e.target.value.trim().toLowerCase() })} />
            <select aria-label="Clasificación" value={evidencia.clasificacion} className={campo}
              onChange={(e) => setEvidencia({ ...evidencia, clasificacion: e.target.value as NuevaEvidencia["clasificacion"] })}>
              <option value="publica">Pública</option><option value="interna">Interna</option>
              <option value="confidencial">Confidencial</option><option value="restringida">Restringida</option>
            </select>
            <input aria-label="Permisos (roles)" value={evidencia.permisos} className={campo}
              onChange={(e) => setEvidencia({ ...evidencia, permisos: e.target.value })} />
            <input aria-label="Fecha de la evidencia" type="date" value={evidencia.fecha} className={campo}
              onChange={(e) => setEvidencia({ ...evidencia, fecha: e.target.value })} />
            <button type="button" onClick={() => void guardarEvidencia()}
              className="rounded border border-[var(--ui-borde)] px-2 py-1 font-medium">Guardar evidencia</button>
          </fieldset>
          {expediente.evidencias.length > 0 && (
            <fieldset className="mt-3 flex flex-wrap gap-2 border-t border-[var(--ui-borde)] pt-2">
              <legend className="font-medium">Registrar verificación</legend>
              <select aria-label="Evidencia revisada" value={revision.evidencia_id} className={campo}
                onChange={(e) => setRevision({ ...revision, evidencia_id: e.target.value })}>
                {expediente.evidencias.map((ev) => <option key={ev.id} value={ev.id}>{ev.titulo} v{ev.version}</option>)}
              </select>
              <input aria-label="Criterio de aceptación" value={revision.criterio} className={`min-w-72 ${campo}`}
                onChange={(e) => setRevision({ ...revision, criterio: e.target.value })} />
              <label><input type="checkbox" checked={revision.evidencia_legible}
                onChange={(e) => setRevision({ ...revision, evidencia_legible: e.target.checked })} /> Evidencia legible</label>
              <select aria-label="Resultado" value={revision.resultado} className={campo}
                onChange={(e) => setRevision({ ...revision, resultado: e.target.value as "conforme" | "no_conforme" })}>
                <option value="no_conforme">No conforme</option><option value="conforme">Conforme</option>
              </select>
              <label><input type="checkbox" checked={revision.eficacia_requerida}
                onChange={(e) => setRevision({ ...revision, eficacia_requerida: e.target.checked })} /> Exige eficacia</label>
              {revision.eficacia_requerida && (
                <label><input type="checkbox" checked={revision.eficacia_conforme}
                  onChange={(e) => setRevision({ ...revision, eficacia_conforme: e.target.checked })} /> Eficacia conforme</label>
              )}
              <input aria-label="Fecha de verificación" type="date" value={revision.fecha} className={campo}
                onChange={(e) => setRevision({ ...revision, fecha: e.target.value })} />
              <input aria-label="Observaciones" value={revision.observaciones} className={campo}
                onChange={(e) => setRevision({ ...revision, observaciones: e.target.value })} />
              <button type="button" onClick={() => void guardarVerificacion()}
                className="rounded border border-[var(--ui-borde)] px-2 py-1 font-medium">Guardar verificación</button>
            </fieldset>
          )}
        </>
      )}
    </section>
  );
}
