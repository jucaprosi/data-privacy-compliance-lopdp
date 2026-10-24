"use client";

import React from "react";
import { Info, Scale } from "lucide-react";

/**
 * Gran escala de la organización (MTGE-01).
 *
 * Antes esta vista sumaba los titulares de todo el RAT contra un umbral de 10.000 y marcaba la EIPD
 * en un archivo local. La Res. SPDP-SPD-2026-0005-R no califica a la organización en conjunto: el
 * cálculo es por tratamiento (arts. 3.8 y 7). Esta vista explica la regla y remite a la calculadora;
 * la lista de tratamientos a gran escala de la organización llegará con el RAT guardado (RAT-01) y
 * las obligaciones de gran escala (MTGE-02).
 */
export default function MtgeRelacionalModule() {
  return (
    <section aria-label="Gran escala de la organización" className="space-y-6">
      <header className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold flex items-center">
          <Scale className="w-5 h-5 mr-2" aria-hidden="true" /> Gran escala de la organización
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">Resolución SPDP-SPD-2026-0005-R</p>
      </header>

      <div className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5 space-y-3 text-xs leading-relaxed">
        <p className="flex items-start gap-2">
          <Info className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            <strong>La gran escala se califica por tratamiento, no por organización.</strong> Cada actividad del
            RAT se evalúa por separado: el número de titulares es el de ese tratamiento en los últimos 12 meses,
            contando cada persona una sola vez (arts. 3.8 y 7). Sumar todas las actividades no tiene base en la norma.
          </span>
        </p>
        <p>
          Un tratamiento es de gran escala si cae en un supuesto de calificación directa (art. 14: salud y otras
          categorías especiales, perfilamiento con efectos jurídicos, videovigilancia en zonas de acceso público,
          biométricos o geolocalización, crédito, niñas, niños y adolescentes, transferencias sistemáticas o
          mensajería) o si sus seis variables suman 6 puntos o más (arts. 8 a 10).
        </p>
        <p>
          Basta un tratamiento de gran escala para que se apliquen los efectos del art. 12: evaluación de impacto
          previa, delegado de protección de datos obligatorio, inclusión en el RAT y medidas reforzadas.
        </p>
        <p className="text-[var(--ui-texto-suave)]">
          Para calificar un tratamiento, use la calculadora de «Riesgos y MTGE».
        </p>
      </div>
    </section>
  );
}
