"use client";

import { useRef } from "react";
import { ArrowDownRight, ArrowRight, ShieldCheck } from "lucide-react";
import { NIVELES_ASIGNADOS } from "@/lib/diagnostico/escala";
import { NIVELES_MADUREZ } from "@/lib/dimensionesSGPDP";
import type { ResultadoAssessment, ResultadoDimension } from "@/store/useAuditStore";
import styles from "./AssessmentExecutiveSummary.module.css";

interface Props {
  resultado: ResultadoAssessment;
  verificado: ResultadoAssessment;
  onShowTasks: () => void;
}

const SIN_EVALUACION = "Sin evaluación suficiente";

/** Nivel de una dimensión con su nombre; sin cobertura suficiente no se emite nivel. */
function textoNivel(dim: ResultadoDimension | undefined): string {
  if (!dim || dim.nivel === 0) return SIN_EVALUACION;
  return `Nivel ${dim.nivel} · ${dim.nivelEtiqueta}`;
}

/**
 * Portada del informe de madurez (DIAG-09). Muestra el nivel de cada dimensión, con la lectura de
 * las respuestas y la lectura con evidencia vinculada; no combina las dimensiones en un puntaje,
 * nivel ni porcentaje de la organización (INV_LOPDP_MULTIDIMENSIONAL_METRICS).
 */
export default function AssessmentExecutiveSummary({ resultado, verificado, onShowTasks }: Props) {
  const nivelesDialog = useRef<HTMLDialogElement>(null);
  const documentos = verificado.controlesConEvidenciaVinculada;
  const sinRespaldo = documentos === 0;
  const motivos: string[] = [];
  if (resultado.ajustePorBrechaEstructural) {
    const bloqueantes = Math.max(
      resultado.controlesEstructuralesDegradados,
      resultado.controlesBloqueantesDegradados
    );
    motivos.push(`${bloqueantes} control(es) bloqueante(s) por debajo del umbral, que impiden demostrar el resto del sistema (tope: Nivel 2 en su dimensión)`);
  }
  if (resultado.ajustePorEvidenciaInsuficiente) {
    motivos.push(`${resultado.controlesSinEvidenciaSuficiente} control(es) de alta criticidad sin evidencia suficiente, sostenidos solo en la declaración (tope: Nivel 3 en su dimensión)`);
  }
  if (resultado.coberturaInsuficiente) {
    motivos.push(`cobertura del ${resultado.coberturaPorcentaje.toFixed(1)} %, por debajo del mínimo exigido para emitir un nivel`);
  }
  const titular = sinRespaldo
    ? "El diagnóstico ofrece un punto de partida. Necesitamos consolidar su respaldo documental."
    : "Compare el nivel que muestran las respuestas con el que sostiene la evidencia vinculada.";

  return (
    <section className={styles.story} aria-labelledby="assessment-story-title">
      <div className={styles.hero}>
        <div className={styles.intro}>
          <div className={styles.eyebrow}>
            <ShieldCheck size={15} aria-hidden="true" />
            <span>Nivel de madurez por dimensión</span>
            <span className={styles.dot} aria-hidden="true" />
            <span>{resultado.dimensiones.length} áreas evaluadas</span>
          </div>
          <h2 id="assessment-story-title" className={styles.title}>{titular}</h2>
          <p className={styles.lead}>
            {`Se evaluaron ${resultado.totalEvaluados} de ${resultado.totalAplicables} controles. Cada dimensión tiene su propio nivel de la escala de cinco niveles; la organización no recibe un nivel único. `}
            {sinRespaldo && "Hoy no hay documentos vinculados: registre el respaldo de la brecha prioritaria para recalcular la lectura con evidencia."}
          </p>
          <div className={styles.actions} role="group" aria-label="Explorar el informe">
            {sinRespaldo ? (
              <button type="button" className={styles.primaryAction} onClick={onShowTasks}>
                Comenzar por la primera acción <ArrowRight size={15} aria-hidden="true" />
              </button>
            ) : (
              <a className={styles.primaryAction} href="#assessment-areas">
                Explorar áreas evaluadas <ArrowRight size={15} aria-hidden="true" />
              </a>
            )}
            <a className={styles.secondaryAction} href="#assessment-bases">
              Consultar prioridades <ArrowDownRight size={15} aria-hidden="true" />
            </a>
            <button type="button" className={styles.secondaryAction} onClick={() => nivelesDialog.current?.showModal()}>
              Ver la escala de cinco niveles
            </button>
          </div>
        </div>
      </div>

      <dialog ref={nivelesDialog} className={styles.levelDialog} aria-labelledby="level-dialog-title"
        aria-describedby="level-dialog-description">
        <div className={styles.dialogHeading}>
          <div>
            <span className={styles.levelLabel}>Escala de madurez del diagnóstico</span>
            <h3 id="level-dialog-title">¿Qué significa cada nivel?</h3>
          </div>
          <button type="button" className={styles.dialogClose} onClick={() => nivelesDialog.current?.close()}
            aria-label="Cerrar escala de madurez">×</button>
        </div>
        <p id="level-dialog-description" className={styles.dialogIntro}>
          El nivel asignado a cada control y el nivel de cada dimensión usan la misma escala.
        </p>
        <ol className={styles.levelList}>
          {NIVELES_ASIGNADOS.map((nivel, indice) => {
            const maximo = NIVELES_MADUREZ[indice + 1]?.umbralMinimo;
            return (
              <li key={nivel.nivel}>
                <span className={styles.listNumber}>N{nivel.nivel}</span>
                <div>
                  <strong>{nivel.nombre}</strong>
                  <span className={styles.range}>{NIVELES_MADUREZ[indice].umbralMinimo}%–{maximo === undefined ? 100 : maximo - 1}%</span>
                  <p>{nivel.criterio}</p>
                </div>
              </li>
            );
          })}
        </ol>
        <p className={styles.dialogFootnote}>Los límites por controles estructurales, evidencia y cobertura pueden ajustar el nivel de una dimensión.</p>
      </dialog>

      <div className={styles.comparison} aria-label="Nivel por dimensión">
        <div className={styles.comparisonHeading}>
          <div>
            <span className={styles.sectionLabel}>Nivel por dimensión</span>
            <p>La lectura de las respuestas y la que exige evidencia vinculada, dimensión por dimensión.</p>
          </div>
        </div>
        <table className="w-full border-collapse text-[11px]">
          <caption className="sr-only">Nivel de madurez de cada dimensión</caption>
          <thead>
            <tr className="text-left text-[var(--ui-texto-suave)]">
              <th scope="col" className="py-1.5 pr-3 font-semibold">Dimensión</th>
              <th scope="col" className="py-1.5 pr-3 font-semibold">Según las respuestas</th>
              <th scope="col" className="py-1.5 font-semibold">Con evidencia vinculada</th>
            </tr>
          </thead>
          <tbody>
            {resultado.dimensiones.map((dim) => (
              <tr key={dim.id} data-dimension={dim.id} className="border-t border-[var(--ui-borde)]">
                <th scope="row" className="py-1.5 pr-3 text-left font-normal">{dim.id} · {dim.nombre}</th>
                <td className="py-1.5 pr-3 font-semibold">{textoNivel(dim)}</td>
                <td className="py-1.5 font-semibold">{textoNivel(verificado.dimensiones.find((d) => d.id === dim.id))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className={styles.evidenceNote}>
          {documentos} de {resultado.totalEvaluados} controles tienen documentos vinculados. Sin documento, la evidencia
          de un control cuenta como verbal (0) y limita su nivel efectivo a 1.
        </p>
      </div>

      {motivos.length > 0 && (
        <div className={styles.explanation}>
          <strong>Condiciones que limitan el nivel.</strong>{" "}
          El diagnóstico topa el nivel de las dimensiones afectadas por las siguientes condiciones:
          <ul>{motivos.map((motivo) => <li key={motivo}>{motivo}</li>)}</ul>
        </div>
      )}

      <div className={styles.footer}>
        <span>En el resto del informe</span>
        <span><strong>{resultado.brechasCriticas}</strong> prioridades urgentes</span>
        <span><strong>{resultado.brechasAltas}</strong> importantes</span>
        <span><strong>{resultado.controlesEstructuralesDegradados}/4</strong> bases por fortalecer</span>
        <span role="group" aria-label="Cobertura">
          Cobertura <strong>{resultado.coberturaPorcentaje.toFixed(1)}%</strong>
          <small>{resultado.totalEvaluados} de {resultado.totalAplicables} controles aplicables</small>
        </span>
      </div>
    </section>
  );
}
