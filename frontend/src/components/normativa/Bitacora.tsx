"use client";
/** Bitácora de las búsquedas de novedades; el operador las lanza con «Buscar novedades ahora». */
import { useCallback, useEffect, useState } from "react";

import { buscarNovedades, listarBitacora, type Corrida } from "./cliente";
import { ESTADO_CORRIDA, fechaCorta } from "./etiquetas";

export default function Bitacora({ operador }: { operador: boolean }) {
  const [corridas, setCorridas] = useState<Corrida[] | null>(null);
  const [fallo, setFallo] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const [resultado, setResultado] = useState("");

  const cargar = useCallback(async () => {
    setFallo(false);
    try { setCorridas(await listarBitacora()); } catch { setFallo(true); }
  }, []);
  useEffect(() => { void cargar(); }, [cargar]);

  const buscar = async () => {
    setBuscando(true);
    setResultado("");
    const antes = corridas?.length ? corridas[0].id : null;
    try {
      await buscarNovedades();
      // La búsqueda corre en el servidor: se consulta la bitácora hasta que aparece la corrida nueva.
      for (let i = 0; i < 30; i += 1) {
        await new Promise((r) => setTimeout(r, 1000));
        const lista = await listarBitacora();
        if (lista.length && lista[0].id !== antes && lista[0].fin) {
          setCorridas(lista);
          setResultado(`Búsqueda terminada: ${lista[0].nuevos + lista[0].versiones_nuevas} novedades.`);
          return;
        }
      }
      setResultado("La búsqueda sigue en curso. Revisa la bitácora en unos minutos.");
    } catch {
      setResultado("No pudimos iniciar la búsqueda. Inténtalo de nuevo.");
    } finally {
      setBuscando(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      {operador ? (
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => void buscar()} disabled={buscando} aria-busy={buscando}
            className="rounded border border-[var(--ui-borde)] px-3 py-1 text-sm">Buscar novedades ahora</button>
          <p role="status" className="text-sm">{buscando ? "Buscando novedades…" : resultado}</p>
        </div>
      ) : null}
      {fallo ? <p role="alert" className="text-sm">No pudimos cargar la bitácora. <button type="button" className="underline" onClick={() => void cargar()}>Volver a cargar</button></p> : null}
      {corridas && corridas.length === 0 ? <p className="text-sm">Aún no se han hecho búsquedas de novedades.</p> : null}
      {corridas && corridas.length > 0 ? (
        <table aria-label="Bitácora de búsquedas" className="w-full text-left text-sm">
          <caption className="sr-only">Bitácora de búsquedas</caption>
          <thead><tr className="border-b border-[var(--ui-borde)]">
            <th scope="col" className="py-2">Fecha</th><th scope="col">Lanzada</th><th scope="col">Resultado</th><th scope="col">Novedades</th>
          </tr></thead>
          <tbody>
            {corridas.map((c) => (
              <tr key={c.id} className="border-b border-[var(--ui-borde)]">
                <td className="py-2">{fechaCorta(c.inicio)}</td>
                <td>{c.origen === "programado" ? "Programada" : "Manual"}</td>
                <td><span className={`inline-block rounded border border-[var(--ui-borde)] px-2 py-0.5 text-xs ${ESTADO_CORRIDA[c.estado].clase}`}>{ESTADO_CORRIDA[c.estado].texto}</span></td>
                <td>{c.nuevos + c.versiones_nuevas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
