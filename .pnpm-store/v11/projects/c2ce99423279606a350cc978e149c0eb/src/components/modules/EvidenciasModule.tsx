"use client";

import React, { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Archive,
  ShieldCheck,
  ShieldX,
  Fingerprint,
  Link2,
  Unlink,
  Layers,
  FileSearch,
  Loader2,
  AlertCircle,
  Settings,
  X,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { resolverNormativa } from "@/lib/normativas";
import { BANCO_PREGUNTAS } from "@/lib/bancoPreguntas";
import {
  calcularSha256,
  formatearFechaRegistro,
  formatearTamano,
} from "@/lib/evidencias/hash";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";

const NOMBRE_CONTROL: ReadonlyMap<number, string> = new Map(
  BANCO_PREGUNTAS.map((p) => [p.id, p.control])
);

type Verificacion =
  | { estado: "inactivo" }
  | { estado: "calculando"; nombre: string }
  | { estado: "integro"; nombre: string; sha256: string; evidencia: EvidenciaDocumental }
  | { estado: "sin-coincidencia"; nombre: string; sha256: string }
  | { estado: "error"; nombre: string; mensaje: string };

interface MetricaProps {
  etiqueta: string;
  valor: number;
  detalle: string;
  tono: string;
  icono: React.ReactNode;
}

function Metrica({ etiqueta, valor, detalle, tono, icono }: MetricaProps) {
  return (
    <div className="p-3.5 rounded-lg bg-[#0a0a0c] border border-[#26262b] space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase font-bold text-zinc-500 tracking-wider">{etiqueta}</span>
        <span className={tono}>{icono}</span>
      </div>
      <div className={`text-2xl font-bold font-mono ${tono}`}>{valor}</div>
      <div className="text-[10px] text-zinc-500">{detalle}</div>
    </div>
  );
}

function VerificadorIntegridad({ evidencias }: { evidencias: EvidenciaDocumental[] }) {
  const [verificacion, setVerificacion] = useState<Verificacion>({ estado: "inactivo" });

  const verificar = async (file: File) => {
    setVerificacion({ estado: "calculando", nombre: file.name });
    try {
      const sha256 = await calcularSha256(file);
      const coincidencia = useAuditStore.getState().evidencias.find((e) => e.sha256 === sha256);
      setVerificacion(
        coincidencia
          ? { estado: "integro", nombre: file.name, sha256, evidencia: coincidencia }
          : { estado: "sin-coincidencia", nombre: file.name, sha256 }
      );
    } catch (error) {
      setVerificacion({
        estado: "error",
        nombre: file.name,
        mensaje: error instanceof Error ? error.message : "Error desconocido.",
      });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: false,
    disabled: verificacion.estado === "calculando",
    onDrop: (archivos) => {
      if (archivos[0]) void verificar(archivos[0]);
    },
  });

  return (
    <div className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3">
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-white flex items-center">
          <FileSearch className="w-4 h-4 mr-1.5 text-[#3892f3]" />
          Verificar integridad
        </h3>
        <p className="text-[11px] text-zinc-400 mt-0.5">
          Presenta un documento y se comparará su huella con las {evidencias.length} registradas. El archivo se procesa en tu
          navegador y no se envía a ningún servidor.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-2 ${
          isDragActive
            ? "border-[#3892f3] bg-[#3892f3]/10"
            : "border-[#26262b] hover:border-[#3892f3]/60 bg-[#0a0a0c]"
        }`}
      >
        <input {...getInputProps()} />
        {verificacion.estado === "calculando" ? (
          <>
            <Loader2 className="w-5 h-5 text-[#3892f3] animate-spin" />
            <span className="text-xs text-zinc-300">Calculando huella de {verificacion.nombre}…</span>
          </>
        ) : (
          <>
            <Fingerprint className="w-5 h-5 text-[#3892f3]" />
            <span className="text-xs font-semibold text-white">Suelta aquí el documento a verificar o haz clic para elegirlo</span>
          </>
        )}
      </div>

      {verificacion.estado === "integro" && (
        <div className="flex items-start gap-2.5 p-3 rounded-lg bg-[#00c853]/10 border border-[#00c853]/40 text-xs">
          <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5 text-[#00c853]" />
          <div className="flex-1 min-w-0 space-y-1">
            <div className="font-bold text-[#00c853]">
              Íntegro: coincide con {verificacion.evidencia.codigo} · {verificacion.evidencia.nombreArchivo}
            </div>
            <div className="text-zinc-400">
              Registrado el {formatearFechaRegistro(verificacion.evidencia.registradaEn)}.
              {verificacion.nombre !== verificacion.evidencia.nombreArchivo &&
                ` El archivo presentado se llama "${verificacion.nombre}", pero su contenido es idéntico.`}
            </div>
            <div className="font-mono text-[10px] text-zinc-500 break-all">{verificacion.sha256}</div>
          </div>
          <BotonCerrar onClick={() => setVerificacion({ estado: "inactivo" })} />
        </div>
      )}

      {verificacion.estado === "sin-coincidencia" && (
        <div className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs">
          <ShieldX className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" />
          <div className="flex-1 min-w-0 space-y-1">
            <div className="font-bold text-[#ff1744]">
              No coincide con ninguna evidencia registrada: el documento difiere del registrado o no fue registrado
            </div>
            <div className="text-zinc-400">Archivo presentado: {verificacion.nombre}</div>
            <div className="font-mono text-[10px] text-zinc-500 break-all">{verificacion.sha256}</div>
          </div>
          <BotonCerrar onClick={() => setVerificacion({ estado: "inactivo" })} />
        </div>
      )}

      {verificacion.estado === "error" && (
        <div className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/40 text-xs text-[#ffab00]">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="flex-1">
            No se pudo verificar &quot;{verificacion.nombre}&quot;. {verificacion.mensaje}
          </span>
          <BotonCerrar onClick={() => setVerificacion({ estado: "inactivo" })} />
        </div>
      )}
    </div>
  );
}

function BotonCerrar({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-zinc-500 hover:text-zinc-200 cursor-pointer"
      aria-label="Cerrar resultado"
    >
      <X className="w-3.5 h-3.5" />
    </button>
  );
}

export default function EvidenciasModule() {
  const evidencias = useAuditStore((s) => s.evidencias);
  const normativaSeleccionada = useAuditStore((s) => s.normativaSeleccionada);
  const setActiveView = useAuditStore((s) => s.setActiveView);
  const normativa = resolverNormativa(normativaSeleccionada);

  const metricas = useMemo(() => {
    const vinculadas = evidencias.filter((e) => e.controlesVinculados.length > 0).length;
    const controles = new Set(evidencias.flatMap((e) => e.controlesVinculados));
    return {
      total: evidencias.length,
      vinculadas,
      sinVincular: evidencias.length - vinculadas,
      controlesRespaldados: controles.size,
    };
  }, [evidencias]);

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[#26262b]">
        <h2 className="text-xl font-bold text-white flex items-center">
          <Archive className="w-5 h-5 mr-2 text-[#9a3bf1]" /> Bóveda de Evidencias
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Registro de huellas SHA-256 de los documentos que respaldan los controles del assessment {normativa.etiquetaCorta}.
        </p>
      </div>

      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-[#3892f3]/5 border border-[#3892f3]/25 text-xs text-zinc-300 leading-relaxed">
        <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-[#3892f3]" />
        <span>
          La plataforma guarda la huella del documento, no el archivo. La huella identifica el contenido exacto: cualquier cambio,
          por mínimo que sea, produce una huella distinta. Custodia los originales en tu repositorio documental y verifica aquí
          que siguen siendo los registrados.
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Metrica
          etiqueta="Evidencias"
          valor={metricas.total}
          detalle="huellas registradas"
          tono="text-zinc-200"
          icono={<Fingerprint className="w-4 h-4" />}
        />
        <Metrica
          etiqueta="Vinculadas"
          valor={metricas.vinculadas}
          detalle="respaldan al menos un control"
          tono="text-[#00c853]"
          icono={<Link2 className="w-4 h-4" />}
        />
        <Metrica
          etiqueta="Sin vincular"
          valor={metricas.sinVincular}
          detalle="aún no respaldan nada"
          tono={metricas.sinVincular > 0 ? "text-[#ffab00]" : "text-zinc-400"}
          icono={<Unlink className="w-4 h-4" />}
        />
        <Metrica
          etiqueta="Controles respaldados"
          valor={metricas.controlesRespaldados}
          detalle="con evidencia verificable"
          tono="text-[#9a3bf1]"
          icono={<Layers className="w-4 h-4" />}
        />
      </div>

      {evidencias.length === 0 ? (
        <div className="bg-[#141417] border border-[#26262b] rounded-xl p-10 flex flex-col items-center text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#1e1e24] flex items-center justify-center">
            <Archive className="w-6 h-6 text-zinc-500" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Aún no hay evidencias registradas</div>
            <p className="text-xs text-zinc-400 mt-1 max-w-md">
              Registra los documentos de cumplimiento desde Configuración: se calculará su huella y podrás vincularlos a los
              controles que respaldan.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setActiveView("configuracion")}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#9a3bf1] hover:bg-[#8a2be1] text-white text-xs font-semibold transition cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5" />
            Ir a Configuración
          </button>
        </div>
      ) : (
        <>
          <VerificadorIntegridad evidencias={evidencias} />

          <div className="bg-[#141417] border border-[#26262b] rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-zinc-300">
                <thead className="bg-[#0a0a0c] text-zinc-500 border-b border-[#26262b] text-[10px] uppercase tracking-wider font-mono">
                  <tr>
                    <th className="p-3 font-bold">Código</th>
                    <th className="p-3 font-bold">Documento</th>
                    <th className="p-3 font-bold">Tamaño</th>
                    <th className="p-3 font-bold">Controles vinculados</th>
                    <th className="p-3 font-bold">Huella SHA-256</th>
                    <th className="p-3 font-bold">Registrada</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#26262b]">
                  {evidencias.map((e) => (
                    <tr key={e.id} className="hover:bg-[#1e1e24]/60 transition align-top">
                      <td className="p-3 font-mono font-bold text-[#9a3bf1] whitespace-nowrap">{e.codigo}</td>
                      <td className="p-3 max-w-[14rem]">
                        <div className="font-semibold text-zinc-100 truncate" title={e.nombreArchivo}>
                          {e.nombreArchivo}
                        </div>
                        <div className="text-[10px] text-zinc-500 font-mono truncate">{e.tipoMime}</div>
                      </td>
                      <td className="p-3 font-mono text-zinc-400 whitespace-nowrap">{formatearTamano(e.tamanoBytes)}</td>
                      <td className="p-3 max-w-[18rem]">
                        {e.controlesVinculados.length === 0 ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ffab00]/10 text-[#ffab00] border border-[#ffab00]/30">
                            Sin vincular
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {e.controlesVinculados.map((id) => (
                              <span
                                key={id}
                                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#9a3bf1]/10 text-[#c89bf7] border border-[#9a3bf1]/30"
                              >
                                P{id}
                                {NOMBRE_CONTROL.has(id) ? ` · ${NOMBRE_CONTROL.get(id)}` : ""}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="p-3 font-mono text-[10px] text-[#00c853] break-all min-w-[16rem] max-w-xs">
                        {e.sha256}
                      </td>
                      <td className="p-3 font-mono text-[10px] text-zinc-400 whitespace-nowrap">
                        {formatearFechaRegistro(e.registradaEn)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
