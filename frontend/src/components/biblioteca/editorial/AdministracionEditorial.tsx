// ¤adpa
// ¤¤developer-architect
"use client";
import { useCallback, useEffect, useState } from "react";
import {
  cambiarEstado, cargarArchivo, crearVersion, dictaminar, guardarFicha, leerHistorial, listarEditorial,
  type CatalogoEditorial, type EventoEditorial, type Version,
} from "@/lib/biblioteca/editorial";
import { camposFicha, FichaEditorial } from "./FichaEditorial";

const estados = { en_revision: "En revisión", publicada: "Publicada", retirada: "Retirada", sustituida: "Sustituida" };
const permisos = { editor: "Editor", revisor_tecnico: "Revisor técnico", revisor_juridico: "Revisor jurídico", publicador: "Publicador" };

export function AdministracionEditorial() {
  const [datos, setDatos] = useState<CatalogoEditorial | null>(null);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [ocupada, setOcupada] = useState(false);
  const [seleccion, setSeleccion] = useState("");
  const [historial, setHistorial] = useState<EventoEditorial[] | null>(null);
  const [codigo, setCodigo] = useState("");
  const [numero, setNumero] = useState("");
  const [formato, setFormato] = useState("DOCX");
  const [sustituye, setSustituye] = useState("");
  const [comentario, setComentario] = useState("");
  const [aprobado, setAprobado] = useState(true);
  const [motivo, setMotivo] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const recargar = useCallback(async () => { setDatos(await listarEditorial()); }, []);
  useEffect(() => { recargar().catch(e => setError(e.message)); }, [recargar]);
  async function operar(accion: () => Promise<unknown>, texto: string) {
    setOcupada(true); setError(""); setMensaje("");
    try { await accion(); await recargar(); setMensaje(texto); setHistorial(null); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo completar la operación."); }
    finally { setOcupada(false); }
  }
  const tiene = (capacidad: string) => datos?.capacidades.some(c => c === capacidad) ?? false;
  const version = datos?.versiones.find(v => v.id === seleccion);
  const independiente = version && !version.autores.includes(datos?.actor_id ?? "");
  const revisiones = datos?.revisiones.filter(r => r.version_id === version?.id) ?? [];
  const actuales = revisiones.filter(r => r.generacion === version?.generacion);
  const lista = version?.estado === "en_revision";
  const completa = version?.sha256 && version.ficha && actuales.some(r => r.tipo === "tecnica" && r.aprobado)
    && actuales.some(r => r.tipo === "juridica" && r.aprobado);
  function prepararSucesora(v: Version) { setSustituye(v.id); setCodigo(v.codigo); setFormato(v.formato); setNumero(""); }
  return <main aria-label="Administración editorial" className="mx-auto h-dvh max-w-6xl space-y-6 overflow-y-auto bg-[var(--ui-superficie)] p-6 text-zinc-100">
    <header><h1 className="text-2xl font-bold">Administración editorial</h1>
      <p>Versiones maestras de EVYDENTIA. Publicar requiere archivo, ficha y ambas revisiones independientes.</p></header>
    {error && <p role="alert" className="rounded border border-red-500 p-3">{error}</p>}
    {mensaje && <p role="status">{mensaje}</p>}
    {!datos && !error && <p role="status">Cargando administración editorial…</p>}
    <button onClick={() => void operar(recargar, "Listado actualizado")} disabled={ocupada}>Actualizar listado</button>
    {datos && <>
      <p>Permisos editoriales: {datos.capacidades.map(c => permisos[c]).join(", ") || "Sin asignación"}.</p>
      {tiene("editor") && <form className="flex flex-wrap items-end gap-3 rounded border p-4" onSubmit={e => {
        e.preventDefault(); void operar(async () => {
          const nueva = await crearVersion(codigo, numero, formato, sustituye || null); setSeleccion(nueva.id);
          setNumero(""); setSustituye("");
        }, "Versión creada en revisión; no está publicada.");
      }}>
        <label>Código<input aria-label="Código" className="block rounded border p-2" required pattern="[A-Z][A-Z0-9-]{1,39}"
          value={codigo} onChange={e => setCodigo(e.target.value)} readOnly={!!sustituye} /></label>
        <label>Versión<input aria-label="Versión nueva" className="block rounded border p-2" required pattern="[0-9]+\.[0-9]+(\.[0-9]+)?"
          value={numero} onChange={e => setNumero(e.target.value)} /></label>
        <label>Formato<select className="block rounded border p-2" value={formato} onChange={e => setFormato(e.target.value)}>
          <option>DOCX</option><option>XLSX</option></select></label>
        <button disabled={ocupada} className="rounded bg-purple-700 p-2 text-[var(--ui-primario-texto)]">Crear versión en revisión</button>
        {sustituye && <button type="button" onClick={() => setSustituye("")}>Cancelar sustitución</button>}
      </form>}
      <ul aria-label="Versiones maestras" className="grid gap-2">
        {datos.versiones.map(v => <li key={v.id} className="rounded border p-3">
          <button aria-pressed={seleccion === v.id} onClick={() => { setSeleccion(v.id); setHistorial(null); setArchivo(null); }}>
            {v.codigo} · {v.version} · {v.ficha?.nombre ?? "Ficha pendiente"} · {estados[v.estado]}
          </button></li>)}
      </ul>
      {!datos.versiones.length && <p>No hay versiones maestras registradas.</p>}
      {version && <section className="grid gap-5 rounded border p-5" aria-label="Detalle editorial">
        <h2 className="text-xl font-semibold">{version.codigo} · {version.version} — {estados[version.estado]}</h2>
        <p>Responsable editorial: {version.responsable_id}. Archivo: {version.nombre_archivo ?? "Pendiente"}.</p>
        {version.sha256 && <p className="break-all">Integridad SHA-256: {version.sha256}</p>}
        {lista && tiene("editor") ? <>
          <FichaEditorial key={`${version.id}:${version.generacion}`} version={version} ocupada={ocupada}
            guardar={f => operar(() => guardarFicha(version, f), "Ficha guardada; revisiones anteriores conservadas como historial.")} />
          <form className="grid gap-2" onSubmit={e => { e.preventDefault(); if (archivo) void operar(() => cargarArchivo(version, archivo), "Archivo guardado para revisión."); }}>
            <label>Archivo maestro (máximo 10 MB)<input type="file" required accept={version.formato === "DOCX" ? ".docx" : ".xlsx"}
              onChange={e => setArchivo(e.target.files?.[0] ?? null)} /></label>
            <button disabled={ocupada || !archivo}>Guardar archivo maestro</button>
          </form>
        </> : version.ficha && <dl>{camposFicha.map(([clave, etiqueta]) => <div key={clave}><dt className="font-semibold">{etiqueta}</dt><dd>{version.ficha?.[clave]}</dd></div>)}</dl>}
        <section aria-label="Dictámenes"><h3 className="font-semibold">Revisiones</h3>
          <p>Las revisiones anteriores se conservan; solo cuentan las de la edición actual.</p>
          {revisiones.map((r, i) => <p key={i}>{r.tipo === "tecnica" ? "Técnica" : "Jurídica"}: {r.aprobado ? "Aprobada" : "Rechazada"} · {r.revisor_id} · edición {r.generacion} · {r.comentario}</p>)}
          {lista && independiente && (tiene("revisor_tecnico") || tiene("revisor_juridico")) && <div className="grid gap-2">
            <label>Dictamen<textarea className="block w-full rounded border p-2" value={comentario} maxLength={4000} onChange={e => setComentario(e.target.value)} /></label>
            <label><input type="checkbox" checked={aprobado} onChange={e => setAprobado(e.target.checked)} /> Aprobar revisión</label>
            {([ ["revisor_tecnico", "tecnica", "Registrar revisión técnica"], ["revisor_juridico", "juridica", "Registrar revisión jurídica"] ] as const)
              .map(([cap, tipo, titulo]) => tiene(cap) && <button key={tipo}
                disabled={ocupada || !comentario.trim() || actuales.some(r => r.tipo === tipo)}
                onClick={() => void operar(() => dictaminar(version, tipo, aprobado, comentario), "Dictamen registrado.")}>{titulo}</button>)}
          </div>}
        </section>
        {tiene("publicador") && independiente && (lista || version.estado === "publicada") && <div className="grid gap-2">
          <label>Motivo de la decisión<textarea className="block w-full rounded border p-2" value={motivo} maxLength={2000} onChange={e => setMotivo(e.target.value)} /></label>
          {lista ? <button disabled={ocupada || !completa || !motivo.trim()}
            onClick={() => void operar(() => cambiarEstado(version, "publicar", motivo), "Versión publicada.")}>Publicar versión</button>
            : <button disabled={ocupada || !motivo.trim()}
              onClick={() => void operar(() => cambiarEstado(version, "retirar", motivo), "Versión retirada; se conserva su historial.")}>Retirar versión</button>}
          {lista && !completa && <p>Publicación pendiente: completa archivo, ficha y revisiones técnica y jurídica.</p>}
        </div>}
        {!independiente && <p>No puedes revisar ni publicar una versión en cuya elaboración participaste.</p>}
        {tiene("editor") && version.estado === "publicada" && <button onClick={() => prepararSucesora(version)}>Preparar versión sustituta</button>}
        <button disabled={ocupada} onClick={async () => {
          setOcupada(true); setError("");
          try { setHistorial(await leerHistorial(version)); }
          catch (e) { setError(e instanceof Error ? e.message : "No se pudo cargar el historial."); }
          finally { setOcupada(false); }
        }}>Ver historial editorial</button>
        {historial && <ul aria-label="Historial editorial">{historial.map((h, i) => <li key={i}>
          {h.accion} · {h.actor_id} · {new Date(h.creada_en).toLocaleString()} · {h.motivo}
        </li>)}</ul>}
      </section>}
    </>}
  </main>;
}
