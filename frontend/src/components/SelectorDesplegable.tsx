"use client";

import React, { useEffect, useId, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

interface SelectorDesplegableProps {
  /** Id del botón, para asociarlo a su etiqueta con htmlFor. */
  id: string;
  value: string;
  opciones: readonly string[];
  onChange: (valor: string) => void;
  /** Si el valor guardado no está en la lista (dato anterior), se muestra como opción adicional. */
  conservarValorExterno?: boolean;
}

/**
 * Selector cuya lista de opciones siempre se despliega hacia abajo.
 *
 * El `<select>` nativo decide por su cuenta si abre hacia arriba o hacia abajo
 * según el espacio de la ventana, y no admite forzarlo. Este selector fija la
 * lista bajo el campo, con altura máxima y desplazamiento interno, y conserva
 * el uso con teclado (flechas, Enter, Escape, Inicio y Fin).
 */
export default function SelectorDesplegable({
  id,
  value,
  opciones,
  onChange,
  conservarValorExterno = true,
}: SelectorDesplegableProps) {
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(0);
  const contenedor = useRef<HTMLDivElement>(null);
  const lista = useRef<HTMLUListElement>(null);
  const idLista = useId();

  const todas =
    conservarValorExterno && value && !opciones.includes(value) ? [value, ...opciones] : [...opciones];

  useEffect(() => {
    if (!abierto) return;
    const alPulsarFuera = (e: MouseEvent) => {
      if (contenedor.current && !contenedor.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", alPulsarFuera);
    return () => document.removeEventListener("mousedown", alPulsarFuera);
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    lista.current?.querySelector<HTMLElement>(`[data-indice="${activo}"]`)?.scrollIntoView({ block: "nearest" });
  }, [abierto, activo]);

  const abrir = () => {
    setActivo(Math.max(0, todas.indexOf(value)));
    setAbierto(true);
  };

  const elegir = (valor: string) => {
    onChange(valor);
    setAbierto(false);
  };

  const alPulsarTecla = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (!abierto) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        abrir();
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActivo((i) => Math.min(todas.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActivo((i) => Math.max(0, i - 1));
    } else if (e.key === "Home") {
      e.preventDefault();
      setActivo(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setActivo(todas.length - 1);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      elegir(todas[activo]);
    } else if (e.key === "Escape" || e.key === "Tab") {
      setAbierto(false);
    }
  };

  return (
    <div ref={contenedor} className="relative">
      <button
        id={id}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={abierto}
        aria-controls={idLista}
        onClick={() => (abierto ? setAbierto(false) : abrir())}
        onKeyDown={alPulsarTecla}
        className="w-full flex items-center justify-between gap-2 text-left bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 text-xs focus:outline-none focus:border-[#9a3bf1] transition cursor-pointer"
      >
        <span className="truncate">{value}</span>
        <ChevronDown className={`w-3.5 h-3.5 shrink-0 text-zinc-500 transition-transform ${abierto ? "rotate-180" : ""}`} />
      </button>
      {abierto && (
        <ul
          id={idLista}
          ref={lista}
          role="listbox"
          aria-labelledby={id}
          className="absolute left-0 right-0 top-full mt-1 z-30 max-h-56 overflow-y-auto rounded-lg border border-zinc-300 dark:border-[#26262b] bg-white dark:bg-[#141417] shadow-lg py-1 text-xs"
        >
          {todas.map((opcion, i) => (
            <li
              key={opcion}
              data-indice={i}
              role="option"
              aria-selected={opcion === value}
              onMouseEnter={() => setActivo(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => elegir(opcion)}
              className={`px-3 py-1.5 cursor-pointer text-zinc-800 dark:text-zinc-200 ${
                i === activo ? "bg-[#9a3bf1]/15" : ""
              } ${opcion === value ? "font-semibold text-[#9a3bf1]" : ""}`}
            >
              {opcion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
