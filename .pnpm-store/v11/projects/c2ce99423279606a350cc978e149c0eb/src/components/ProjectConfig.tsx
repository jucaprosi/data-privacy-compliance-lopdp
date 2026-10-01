"use client";

import React, { useId, useState } from "react";
import { Building2, SlidersHorizontal, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuditStore, useHasHydrated } from "@/store/useAuditStore";
import {
  PERFIL_VACIO,
  SELECTORES_PERFIL,
  etiquetaTamanoPorPersonas,
  respuestasPendientes,
  type ClavePerfil,
  type RespuestaPerfil,
} from "@/lib/bancoPreguntas";

/** Ficha organizacional de la empresa. */
export default function ProjectConfig() {
  const hasHydrated = useHasHydrated();
  const { companyData, isConfigured, setCompanyData, setIsConfigured } = useAuditStore();
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  // Los campos de la ficha se asocian a su etiqueta por id, de modo que el
  // lector de pantalla anuncie de qué dato se trata al recibir el foco.
  const idRazonSocial = useId();
  const idSector = useId();
  const idTamano = useId();
  const idIess = useId();
  const idServicios = useId();

  const perfil = companyData.perfil ?? PERFIL_VACIO;
  const pendientes = respuestasPendientes(companyData.perfil);
  const hayConteo =
    (companyData.empleadosIess ?? null) !== null || (companyData.contratadosServicios ?? null) !== null;
  const totalPersonas = (companyData.empleadosIess ?? 0) + (companyData.contratadosServicios ?? 0);

  // El tamaño se deriva de lo verificable: empleados directos afiliados al IESS
  // más personas bajo contrato de servicios (cuentas contables de servicios).
  const actualizarConteo = (cambio: { empleadosIess?: number | null; contratadosServicios?: number | null }) => {
    const iess = cambio.empleadosIess !== undefined ? cambio.empleadosIess : companyData.empleadosIess ?? null;
    const servicios =
      cambio.contratadosServicios !== undefined ? cambio.contratadosServicios : companyData.contratadosServicios ?? null;
    const total = (iess ?? 0) + (servicios ?? 0);
    setCompanyData({
      ...cambio,
      ...(iess !== null || servicios !== null ? { tamano: etiquetaTamanoPorPersonas(total) } : {}),
    });
  };
  const aNumero = (valor: string): number | null => {
    if (valor.trim() === "") return null;
    const n = Math.floor(Number(valor));
    return Number.isFinite(n) && n >= 0 ? n : null;
  };
  const responderPerfil = (clave: ClavePerfil, valor: RespuestaPerfil) =>
    setCompanyData({ perfil: { ...perfil, [clave]: valor } });

  const handleGuardar = async () => {
    if (!companyData.razonSocial.trim()) {
      alert("Por favor ingresa la Razón Social de la empresa antes de continuar.");
      return;
    }
    setGuardando(true);
    let texto: string;
    try {
      await fetch("/api/project/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyData,
          isConfigured: true,
          timestamp: new Date().toISOString(),
        }),
      });
      texto = "Ficha organizacional guardada.";
    } catch {
      texto = "Ficha organizacional guardada localmente.";
    }
    setMensaje(texto);
    // Este componente se desmonta en cuanto isConfigured pasa a true: la
    // navegación no la dispara esta función, sino un efecto en
    // dashboard/page.tsx que reacciona al propio isConfigured y saca al
    // usuario de "configuracion" apenas deja de ser una vista válida. Por
    // eso hay que retrasar isConfigured, no la navegación: si solo se
    // retrasara un setActiveView propio, ese efecto ajeno igual desmontaría
    // el componente de inmediato y el aviso nunca llegaría a pintarse.
    await new Promise((resolver) => setTimeout(resolver, 700));
    setIsConfigured(true);
  };

  if (!hasHydrated) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto pb-10 animate-pulse">
        <div className="h-14 bg-zinc-100 dark:bg-[#141417] rounded-xl border border-zinc-200 dark:border-[#26262b]" />
        <div className="max-w-3xl h-64 bg-zinc-100 dark:bg-[#141417] rounded-xl border border-zinc-200 dark:border-[#26262b]" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-200 dark:border-[#26262b] gap-3">
        <div>
          <h2 className="text-xl font-bold text-zinc-900 dark:text-white flex items-center tracking-tight">
            <SlidersHorizontal className="w-5 h-5 mr-2 text-[#9a3bf1]" />
            Ficha Organizacional
          </h2>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1">
            Registra los parámetros de la empresa que la plataforma utilizará automáticamente.
          </p>
        </div>

        <span
          className={`text-[11px] font-mono px-2.5 py-1 rounded-md border flex items-center space-x-1.5 shrink-0 ${
            isConfigured
              ? "bg-[#00c853]/15 text-[#00c853] border-[#00c853]/30"
              : "bg-zinc-100 dark:bg-[#0a0a0c] text-zinc-500 border-zinc-200 dark:border-[#26262b]"
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isConfigured ? "bg-[#00c853]" : "bg-zinc-400"}`} />
          <span>{isConfigured ? "Perfil Empresarial Guardado" : "Pendiente de Completar"}</span>
        </span>
      </div>

      <div className="max-w-3xl">
        {/* Ficha organizacional */}
        <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-200 dark:border-[#26262b] pb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white flex items-center">
              <Building2 className="w-4 h-4 mr-1.5 text-[#3892f3]" />
              Ficha Organizacional (Datos de la Empresa)
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div className="sm:col-span-2">
              <label
                htmlFor={idRazonSocial}
                className="block text-zinc-700 dark:text-zinc-400 mb-1 font-medium"
              >
                Razón Social de la Empresa <span className="text-[#ff1744]">*</span>
              </label>
              <input
                id={idRazonSocial}
                type="text"
                required
                value={companyData.razonSocial}
                onChange={(e) => setCompanyData({ razonSocial: e.target.value })}
                placeholder="Ej. Jubys Cloud Solutions S.A.S."
                className="w-full bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-xs focus:outline-none focus:border-[#9a3bf1] transition"
              />
            </div>

            <div>
              <label
                htmlFor={idSector}
                className="block text-zinc-700 dark:text-zinc-400 mb-1 font-medium"
              >
                Sector de la Empresa
              </label>
              <select
                id={idSector}
                value={companyData.sector}
                onChange={(e) => setCompanyData({ sector: e.target.value })}
                className="w-full bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 text-xs focus:outline-none focus:border-[#9a3bf1] transition"
              >
                <option>Telecomunicaciones y Tecnología</option>
                <option>Fintech y Servicios Financieros</option>
                <option>Salud y Farmacéutica</option>
                <option>Comercio Electrónico y Retail</option>
                <option>Manufactura y Logística</option>
                <option>Sector Público y Academia</option>
              </select>
            </div>

            <div>
              <label
                htmlFor={idIess}
                className="block text-zinc-700 dark:text-zinc-400 mb-1 font-medium"
              >
                Empleados directos afiliados al IESS
              </label>
              <input
                id={idIess}
                type="number"
                min={0}
                inputMode="numeric"
                value={companyData.empleadosIess ?? ""}
                onChange={(e) => actualizarConteo({ empleadosIess: aNumero(e.target.value) })}
                placeholder="Según la planilla de aportes del IESS"
                className="w-full bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-xs focus:outline-none focus:border-[#9a3bf1] transition"
              />
              <p className="mt-1 text-[10px] text-zinc-500 dark:text-zinc-400">
                El IESS es la fuente que corrobora el número de empleados directos.
              </p>
            </div>

            <div>
              <label
                htmlFor={idServicios}
                className="block text-zinc-700 dark:text-zinc-400 mb-1 font-medium"
              >
                Personas bajo contrato de servicios
              </label>
              <input
                id={idServicios}
                type="number"
                min={0}
                inputMode="numeric"
                value={companyData.contratadosServicios ?? ""}
                onChange={(e) => actualizarConteo({ contratadosServicios: aNumero(e.target.value) })}
                placeholder="Según las cuentas contables de servicios"
                className="w-full bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 text-xs focus:outline-none focus:border-[#9a3bf1] transition"
              />
              <p className="mt-1 text-[10px] text-zinc-500 dark:text-zinc-400">
                Se cuentan con las cuentas contables de servicios (honorarios y servicios contratados).
              </p>
            </div>

            <div>
              <label
                htmlFor={idTamano}
                className="block text-zinc-700 dark:text-zinc-400 mb-1 font-medium"
              >
                Tamaño / Número de Empleados
                {hayConteo && (
                  <span className="ml-1 font-normal text-zinc-500 dark:text-zinc-400">
                    (calculado: {totalPersonas} personas)
                  </span>
                )}
              </label>
              <select
                id={idTamano}
                value={companyData.tamano}
                disabled={hayConteo}
                onChange={(e) => setCompanyData({ tamano: e.target.value })}
                className="w-full bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 text-xs focus:outline-none focus:border-[#9a3bf1] transition"
              >
                <option>Microempresa (1-9)</option>
                <option>Pequeña Empresa (10-49)</option>
                <option>Mediana Empresa (50-199)</option>
                <option>Corporativo (&gt; 200)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Perfil de operación */}
        <div className="mt-4 bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-5 shadow-sm space-y-3">
          <div className="border-b border-zinc-200 dark:border-[#26262b] pb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white flex items-center">
              <SlidersHorizontal className="w-4 h-4 mr-1.5 text-[#9a3bf1]" />
              Perfil de Operación
            </h3>
            <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
              Responda Sí o No a cada pregunta. Si no está seguro, consulte con el área correspondiente antes de
              contestar: sus respuestas definen qué controles se evaluarán.
            </p>
          </div>

          <div className="border border-zinc-200 dark:border-[#26262b] rounded-lg overflow-hidden text-xs">
            {SELECTORES_PERFIL.map((sel, i) => (
              <div
                key={sel.clave}
                className={`flex flex-col sm:flex-row sm:items-center gap-2 px-3.5 py-2.5 ${
                  i % 2 === 0 ? "bg-zinc-50 dark:bg-[#0a0a0c]" : "bg-white dark:bg-[#141417]"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-zinc-800 dark:text-zinc-200" id={`perfil-${sel.clave}`}>
                    {sel.pregunta}
                  </p>
                  <p className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5">{sel.ayuda}</p>
                </div>
                <div
                  role="radiogroup"
                  aria-labelledby={`perfil-${sel.clave}`}
                  className="flex items-center gap-5 shrink-0"
                >
                  {(["si", "no"] as const).map((valor) => (
                    <label key={valor} className="flex items-center gap-1.5 cursor-pointer text-zinc-700 dark:text-zinc-300">
                      <input
                        type="radio"
                        name={`perfil-${sel.clave}`}
                        checked={perfil[sel.clave] === valor}
                        onChange={() => responderPerfil(sel.clave, valor)}
                        className="accent-[#9a3bf1]"
                      />
                      {valor === "si" ? "Sí" : "No"}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
            {pendientes === 0
              ? "Perfil completo."
              : `Faltan ${pendientes} respuesta(s). Mientras no responda, no se descartará ni se agregará ningún control.`}
          </p>
        </div>
      </div>

      {/* Acción principal */}
      <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-zinc-200 dark:border-[#26262b] gap-3">
        <div className="flex items-center space-x-2 text-xs text-zinc-500 dark:text-zinc-400">
          <ShieldCheck className="w-4 h-4 text-[#9a3bf1]" />
          <span>{mensaje ?? "La ficha organizacional alimenta automáticamente la evaluación y el tablero."}</span>
        </div>

        <button
          type="button"
          onClick={handleGuardar}
          disabled={guardando}
          style={{ background: "linear-gradient(135deg, #9a3bf1, #3892f3)" }}
          className="w-full sm:w-auto text-white px-5 py-2.5 text-xs font-semibold rounded-lg flex items-center justify-center cursor-pointer shadow-md hover:opacity-95 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span>{guardando ? "Guardando…" : "Guardar Ficha y Continuar"}</span>
          <ArrowRight className="w-3.5 h-3.5 ml-2" />
        </button>
      </div>
    </div>
  );
}




