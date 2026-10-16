"use client";

import React, { useCallback, useEffect, useId, useState } from "react";
import { Loader2 } from "lucide-react";

import { TAMANOS, configuracionApi } from "./configuracion";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export function ConfiguracionTab() {
  const id = useId();
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<ErrorDescrito | null>(null);
  const [errorGuardado, setErrorGuardado] = useState<ErrorDescrito | null>(null);
  const [tamano, setTamano] = useState("");
  const [sector, setSector] = useState("");
  const [guardado, setGuardado] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const actual = await configuracionApi.obtener();
      setTamano(actual.tamano ?? "");
      setSector(actual.sector ?? "");
    } catch (err: unknown) {
      setErrorCarga(describirError(err));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    setGuardado(false);
    setErrorGuardado(null);
    if (tamano === "") {
      setAviso("Elige el tamaño de la organización.");
      return;
    }
    setAviso(null);
    setOcupado(true);
    try {
      const nueva = await configuracionApi.guardar({ tamano, sector: sector.trim() || null });
      setTamano(nueva.tamano ?? "");
      setSector(nueva.sector ?? "");
      setGuardado(true);
    } catch (err: unknown) {
      setErrorGuardado(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  if (cargando) {
    return (
      <p role="status" className="flex items-center gap-2 text-xs text-zinc-300">
        <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" aria-hidden="true" />
        Cargando la configuración…
      </p>
    );
  }

  if (errorCarga) {
    return (
      <div className="space-y-2">
        <BloqueError error={errorCarga} testId="error-configuracion" />
        <button type="button" className={BOTON} onClick={() => void cargar()}>
          Reintentar la carga
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={guardar} noValidate aria-label="Configuración de la organización" className="space-y-4 max-w-xl">
      {tamano === "" && (
        <p role="note" data-testid="aviso-tamano" className="p-3 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs">
          El tamaño de la organización aún no está configurado. Sin él no se puede comprobar si una misma persona puede ser
          encargado y responsable de área.
        </p>
      )}
      <div>
        <label htmlFor={`${id}-tamano`} className={ETIQUETA}>
          Tamaño de la organización
        </label>
        <select id={`${id}-tamano`} className={CAMPO} value={tamano} onChange={(e) => setTamano(e.target.value)}>
          <option value="">Sin configurar</option>
          {TAMANOS.map((t) => (
            <option key={t.clave} value={t.clave}>
              {t.etiqueta}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor={`${id}-sector`} className={ETIQUETA}>
          Sector
        </label>
        <input id={`${id}-sector`} className={CAMPO} value={sector} onChange={(e) => setSector(e.target.value)} />
      </div>
      {aviso && (
        <p role="alert" className="text-[11px] text-[#ff6b86]">
          {aviso}
        </p>
      )}
      {errorGuardado && <BloqueError error={errorGuardado} testId="error-guardado" />}
      {guardado && (
        <p role="status" data-testid="configuracion-guardada" className="text-xs text-[#5fe39a]">
          La configuración se guardó correctamente.
        </p>
      )}
      <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
        {ocupado ? "Guardando…" : "Guardar configuración"}
      </button>
    </form>
  );
}
