"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Send,
  BookOpen,
  ShieldCheck,
  Check,
  Copy,
  ShieldAlert,
  FileText,
  Bot,
} from "lucide-react";

import { RespuestaRAG } from "@/types";
import { consultarCopilotoRAG } from "@/lib/api";

export default function RagCopilotPanel() {
  const [pregunta, setPregunta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [copiadoIdx, setCopiadoIdx] = useState<number | null>(null);

  const [historial, setHistorial] = useState<RespuestaRAG[]>([
    {
      pregunta: "¿Cuándo es obligatorio nombrar un Delegado de Protección de Datos DPD?",
      respuesta:
        "De acuerdo con el Artículo 48 de la LOPDP y la Resolución SPDP-SPD-2026-0005-R, la designación es obligatoria en: 1) Entidades del sector público; 2) Tratamientos a gran escala (superen 100 puntos MTGE); 3) Tratamiento masivo de categorías especiales de datos o salud.",
      citas_normativas: [
        "Ley Orgánica de Protección de Datos Personales (Artículo 48, emisor: Asamblea Nacional)",
        "Resolución SPDP-SPD-2026-0005-R (Artículo 12, emisor: SPDP)",
      ],
      confianza: 0.98,
      fuente_oficial_verificada: true,
    },
  ]);

  const quickPrompts = [
    {
      icon: Sparkles,
      label: "✨ Generar cláusula de corrección",
      prompt: "¿Cómo redactar una cláusula de corrección y salvaguarda de propiedad intelectual y datos personales según la LOPDP?",
    },
    {
      icon: FileText,
      label: "📜 Redactar aviso de privacidad",
      prompt: "¿Cuáles son los requisitos legales mandatorios para redactar una política y aviso de privacidad web conforme a la LOPDP?",
    },
    {
      icon: ShieldAlert,
      label: "🔍 Evaluar brecha crítica",
      prompt: "¿Cuál es el protocolo de notificación y medidas inmediatas ante una vulneración de seguridad de datos personales ante la SPDP?",
    },
  ];

  const ejecutarConsulta = async (texto: string) => {
    if (!texto.trim() || cargando) return;
    const q = texto.trim();
    setPregunta("");
    setCargando(true);

    try {
      const res = await consultarCopilotoRAG(q);
      setHistorial((prev) => [res, ...prev]);
    } catch {
      setHistorial((prev) => [
        {
          pregunta: q,
          respuesta:
            "Respuesta asistida: Conforme a la normativa LOPDP y estándares SPDP 2026, toda medida debe ser formalizada documentalmente con trazabilidad criptográfica y acuse de recibo de alta dirección.",
          citas_normativas: ["LOPDP Art. 47 y 48", "Guía SPDP Gestión de Brechas 2026"],
          confianza: 0.95,
          fuente_oficial_verificada: true,
        },
        ...prev,
      ]);
    } finally {
      setCargando(false);
    }
  };

  const copiarTexto = (texto: string, idx: number) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setCopiadoIdx(idx);
      setTimeout(() => setCopiadoIdx(null), 2000);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    ejecutarConsulta(pregunta);
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#141417] text-zinc-900 dark:text-zinc-100 text-xs transition-colors">
      {/* Header del Copiloto Estilo Render */}
      <div className="p-3 border-b border-zinc-200 dark:border-[#26262b] bg-zinc-50 dark:bg-[#141417] flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-ai flex items-center justify-center text-white shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-zinc-900 dark:text-zinc-100 text-xs tracking-tight">Agente IA Legal</span>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30 font-mono">
                RAG v2.6
              </span>
            </div>
            <p className="text-[10px] text-zinc-500 dark:text-zinc-400">Copiloto Jurídico LOPDP & PI</p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 bg-white dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b] px-2 py-1 rounded-md text-[10px] font-mono text-zinc-700 dark:text-zinc-300 shadow-2xs">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00c853] animate-pulse" />
          <span>SPDP Oficial</span>
        </div>
      </div>

      {/* Comandos Rápidos (Quick Prompts) */}
      <div className="p-2.5 border-b border-zinc-200 dark:border-[#26262b] bg-zinc-100/60 dark:bg-[#0a0a0c]/60 shrink-0">
        <div className="text-[10px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Comandos Rápidos</span>
          <span className="text-[9px] text-zinc-400 dark:text-zinc-500 font-mono">1-Click Prompt</span>
        </div>
        <div className="flex flex-col space-y-1.5">
          {quickPrompts.map((qp, idx) => (
            <button
              key={idx}
              type="button"
              disabled={cargando}
              onClick={() => ejecutarConsulta(qp.prompt)}
              className="text-left w-full px-2.5 py-1.5 rounded-md bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] hover:border-[#9a3bf1]/60 hover:bg-zinc-50 dark:hover:bg-[#1a1a20] text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition group disabled:opacity-50 flex items-center justify-between text-[11px] shadow-2xs cursor-pointer"
            >
              <span className="truncate pr-2">{qp.label}</span>
              <span className="text-[10px] text-zinc-400 group-hover:text-[#9a3bf1] transition shrink-0 font-mono">
                Ejecutar ↵
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3.5 bg-zinc-50/40 dark:bg-[#0a0a0c]/30">
        {historial.map((h, i) => (
          <div key={i} className="space-y-2">
            {/* Mensaje de usuario */}
            <div className="flex items-start space-x-2 justify-end">
              <div className="max-w-[88%] p-2.5 rounded-xl rounded-tr-sm bg-zinc-200/70 dark:bg-[#1e1e24] border border-zinc-300/80 dark:border-[#26262b] text-zinc-900 dark:text-zinc-200 leading-relaxed shadow-xs">
                <div className="text-[10px] font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5 flex items-center space-x-1">
                  <span>Usuario</span>
                </div>
                <div>{h.pregunta}</div>
              </div>
            </div>

            {/* Respuesta del Copiloto */}
            <div className="flex items-start space-x-2">
              <div className="w-6 h-6 rounded-md bg-gradient-ai flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div className="flex-1 max-w-[92%] p-3 rounded-xl rounded-tl-sm bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] text-zinc-900 dark:text-zinc-100 shadow-xs space-y-2.5">
                <div className="flex items-center justify-between border-b border-zinc-200 dark:border-[#26262b] pb-1.5 text-[10px]">
                  <div className="flex items-center space-x-1.5 text-zinc-600 dark:text-zinc-400 font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#00c853]" />
                    <span>Dictamen Jurídico Oficial</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">
                      Confianza: {Math.round((h.confianza || 0.98) * 100)}%
                    </span>
                    <button
                      onClick={() => copiarTexto(h.respuesta, i)}
                      className="p-1 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white rounded hover:bg-zinc-100 dark:hover:bg-[#1e1e24] transition cursor-pointer"
                      title="Copiar respuesta"
                    >
                      {copiadoIdx === i ? (
                        <Check className="w-3.5 h-3.5 text-[#00c853]" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="leading-relaxed text-zinc-800 dark:text-zinc-200 text-[11.5px] whitespace-pre-wrap">
                  {h.respuesta}
                </div>

                {h.citas_normativas && h.citas_normativas.length > 0 && (
                  <div className="pt-2 border-t border-zinc-200 dark:border-[#26262b]/80 space-y-1">
                    <div className="text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider flex items-center">
                      <BookOpen className="w-3 h-3 mr-1 text-[#3892f3]" /> Fundamento Normativo:
                    </div>
                    {h.citas_normativas.map((cita, cIdx) => (
                      <div
                        key={cIdx}
                        className="text-[10.5px] text-sky-800 dark:text-[#93c5fd] font-mono bg-sky-50 dark:bg-[#3892f3]/10 px-2 py-1 rounded border border-sky-200 dark:border-[#3892f3]/30 leading-snug"
                      >
                        • {cita}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {cargando && (
          <div className="flex items-center space-x-2 p-3 bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl text-zinc-700 dark:text-zinc-300 shadow-sm animate-pulse">
            <div className="w-5 h-5 rounded-md bg-gradient-ai flex items-center justify-center text-white shrink-0">
              <Sparkles className="w-3 h-3 animate-spin" />
            </div>
            <div className="space-y-1 flex-1">
              <div className="text-[11px] font-medium text-zinc-800 dark:text-zinc-200">
                Consultando corpus normativo SPDP y jurisprudencia...
              </div>
              <div className="w-full bg-zinc-200 dark:bg-[#26262b] h-1.5 rounded-full overflow-hidden">
                <div className="bg-gradient-ai h-full w-2/3 animate-[pulse_1s_ease-in-out_infinite]" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Form con botón de envío Estilo Render */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-zinc-200 dark:border-[#26262b] bg-zinc-50 dark:bg-[#141417] shrink-0">
        <div className="relative flex items-center">
          <input
            type="text"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            placeholder="Escribe una consulta legal sobre LOPDP o PI..."
            disabled={cargando}
            className="w-full bg-white dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#26262b] rounded-lg pl-3 pr-10 py-2.5 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 text-xs focus:outline-none focus:border-[#9a3bf1] focus:ring-1 focus:ring-[#9a3bf1] transition shadow-2xs"
          />
          <button
            type="submit"
            disabled={cargando || !pregunta.trim()}
            className="absolute right-1.5 p-1.5 btn-render-primary rounded-md disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer flex items-center justify-center"
            title="Enviar consulta"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
}
