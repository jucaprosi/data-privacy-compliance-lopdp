/**
 * Interruptor único de la evidencia física (FE-26).
 *
 * El PMV no guarda evidencias: el DPO declara en cada pregunta el nivel de evidencia y la
 * plataforma no la comprueba (DIAG-13). Con el interruptor apagado la pantalla no ofrece adjuntar
 * archivos al diagnóstico ni la custodia de la hoja de ruta. Solo EVYDENTIA lo enciende
 * (`NEXT_PUBLIC_EVIDENCIA_FISICA=true`), y entonces EVI-01 y EVI-02 siguen con esos componentes.
 *
 * Cualquier valor distinto de «true» deja el interruptor apagado: ante la duda, el PMV.
 */

import { useSyncExternalStore } from "react";

/**
 * Ajuste que las pruebas de interfaz fijan desde el navegador (`addInitScript`) para ejercitar el
 * interruptor encendido sin otra compilación. Solo existe fuera de producción: en un build de
 * producción `NODE_ENV` es una constante y esta lectura se elimina.
 */
declare global {
  interface Window {
    __LOPDP_EVIDENCIA_PRUEBAS__?: boolean;
  }
}

function ajusteDePrueba(): boolean | undefined {
  if (process.env.NODE_ENV === "production" || typeof window === "undefined") return undefined;
  const valor = window.__LOPDP_EVIDENCIA_PRUEBAS__;
  return typeof valor === "boolean" ? valor : undefined;
}

function porConfiguracion(): boolean {
  return (process.env.NEXT_PUBLIC_EVIDENCIA_FISICA ?? "").trim().toLowerCase() === "true";
}

export function evidenciaFisicaActiva(): boolean {
  const prueba = ajusteDePrueba();
  if (prueba !== undefined) return prueba;
  return porConfiguracion();
}

const sinSuscripcion = () => () => {};

/**
 * El interruptor dentro de un componente. El servidor renderiza con la configuración y el cliente
 * aplica el ajuste de prueba después de hidratar, sin desajuste de hidratación.
 */
export function useEvidenciaFisica(): boolean {
  return useSyncExternalStore(sinSuscripcion, evidenciaFisicaActiva, porConfiguracion);
}

/** Aviso único del sello cuando la evidencia es declarada (PMV). */
export const AVISO_EVIDENCIA_DECLARADA =
  "La evidencia que indicas en cada pregunta queda registrada como declarada, no verificada";
