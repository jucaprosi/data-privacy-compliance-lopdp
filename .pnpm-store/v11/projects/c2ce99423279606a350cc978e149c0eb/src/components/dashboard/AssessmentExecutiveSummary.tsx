"use client";

import { useRef } from "react";
import { ArrowDownRight, ArrowRight, BadgeCheck, ShieldCheck } from "lucide-react";
import { NIVELES_MADUREZ, NIVELES_MADUREZ_INDEX } from "@/lib/dimensionesSGPDP";
import type { ResultadoAssessment } from "@/store/useAuditStore";
import MaturityPath from "./MaturityPath";
import styles from "./AssessmentExecutiveSummary.module.css";

interface Props {
  resultado: ResultadoAssessment;
  verificado: ResultadoAssessment;
  onShowTasks: () => void;
}

export default function AssessmentExecutiveSummary({ resultado, verificado, onShowTasks }: Props) {
  const nivelesDialog = useRef<HTMLDialogElement>(null);
  const diferencia = Math.max(0, resultado.scorePonderado - verificado.scorePonderado);
  const documentos = verificado.controlesConEvidenciaVinculada;
  const motivos: string[] = [];
  if (resultado.ajustePorBrechaEstructural) {
    const bloqueantes = Math.max(
      resultado.controlesEstructuralesDegradados,
      resultado.controlesBloqueantesDegradados
    );
    motivos.push(`${bloqueantes} control(es) bloqueante(s) por debajo del umbral, que impiden demostrar el resto del sistema (tope: Nivel 2)`);
  }
  if (resultado.ajustePorEvidenciaInsuficiente) {
    motivos.push(`${resultado.controlesSinEvidenciaSuficiente} control(es) de alta criticidad sin evidencia suficiente, sostenidos solo en la declaración (tope: Nivel 3)`);
  }
  if (resultado.coberturaInsuficiente) {
    motivos.push(`cobertura del ${resultado.coberturaPorcentaje.toFixed(1)} %, por debajo del mínimo exigido para emitir un nivel`);
  }
  const sinRespaldo = documentos === 0 && verificado.nivelAjustado === 1;
  const titular = sinRespaldo
    ? "Hagamos verificable el avance declarado."
    : documentos === 0
      ? "El diagnóstico ofrece un punto de partida. Necesitamos consolidar su respaldo documental."
    : diferencia > 0.05
      ? "El avance declarado es visible. Necesitamos fortalecer su respaldo documental."
      : "Las respuestas y la evidencia presentan resultados consistentes.";
  const descripcionNivel = resultado.coberturaInsuficiente
    ? "La cobertura evaluada aún no permite asignar un nivel de madurez."
    : resultado.nivelAjustado === 2
      ? "Prácticas incipientes y repetibles. Su respaldo documental se examina por separado en la lectura con evidencia."
    : NIVELES_MADUREZ_INDEX[resultado.nivelAjustado]?.descripcion
      ?? "El nivel resume la madurez calculada a partir de las respuestas y los límites del diagnóstico.";
  const notaNivel = resultado.coberturaInsuficiente
    ? "Evaluación pendiente"
    : `Con evidencia: nivel ${verificado.nivelAjustado} · ${verificado.nivelAjustadoEtiqueta}`;
  const hitos = [
    ...(verificado.brechas.some((brecha) => brecha.preguntaId === 2) ? ["Designar responsables y aprobar su mandato"] : []),
    ...(verificado.controlesEstructuralesDegradados > 0 ? ["Corregir controles estructurales"] : []),
    ...(documentos < resultado.totalEvaluados ? ["Vincular evidencias a los controles"] : []),
  ];

  return (
    <section className={styles.story} aria-labelledby="assessment-story-title">
      <div className={styles.hero}>
        <div className={styles.level}>
          <span className={styles.levelLabel}>Nivel ajustado por el diagnóstico</span>
          <button type="button" className={styles.levelNumber}
            aria-label={`Nivel ${resultado.nivelAjustado}. Ver escala de madurez de cinco niveles`}
            onClick={() => nivelesDialog.current?.showModal()}>
            Nivel {resultado.nivelAjustado}
          </button>
          <span className={styles.levelName}>{resultado.nivelAjustadoEtiqueta}</span>
          <p className={styles.levelMeaning}>{descripcionNivel}</p>
          <span className={styles.levelNote}>{notaNivel}</span>
          <span className={styles.levelHint}>Seleccione el nivel para consultar la escala</span>
        </div>
        <div className={styles.intro}>
          <div className={styles.eyebrow}>
            <ShieldCheck size={15} aria-hidden="true" />
            <span>Panorama de madurez y evidencia</span>
            <span className={styles.dot} aria-hidden="true" />
            <span>{resultado.dimensiones.length} áreas evaluadas</span>
          </div>
          <h2 id="assessment-story-title" className={`${styles.title} ${sinRespaldo ? styles.titleCompact : ""}`}>{titular}</h2>
          {sinRespaldo && (
            <div className={styles.statusFlow} aria-label={`Nivel ${resultado.nivelTeorico} declarado; nivel ${resultado.nivelAjustado} degradado; nivel ${verificado.nivelAjustado} con evidencia`}>
              <span>Declarado <strong>Nivel {resultado.nivelTeorico}</strong></span>
              <ArrowRight size={16} aria-hidden="true" />
              <span>Degradado <strong>Nivel {resultado.nivelAjustado}</strong></span>
              <ArrowRight size={16} aria-hidden="true" />
              <span>Con evidencia <strong>Nivel {verificado.nivelAjustado}</strong></span>
            </div>
          )}
          <p className={styles.lead}>
            {sinRespaldo
              ? "Las respuestas muestran el punto de partida. Hoy no hay documentos vinculados: comience por la brecha prioritaria y registre su respaldo para recalcular el resultado."
              : `Se evaluaron ${resultado.totalEvaluados} de ${resultado.totalAplicables} controles. La escala de cinco niveles valora la formalización y consistencia de los procesos. Compare el resultado de las respuestas con la lectura que exige evidencia vinculada.`}
          </p>
          <div className={styles.actions} role="group" aria-label="Explorar el informe">
            {sinRespaldo ? (
              <>
                <button type="button" className={styles.primaryAction} onClick={onShowTasks}>
                  Comenzar por la primera acción <ArrowRight size={15} aria-hidden="true" />
                </button>
                <a className={styles.secondaryAction} href="#assessment-areas">
                  Explorar áreas evaluadas <ArrowDownRight size={15} aria-hidden="true" />
                </a>
              </>
            ) : (
              <>
                <a className={styles.primaryAction} href="#assessment-areas">
                  Explorar áreas evaluadas <ArrowRight size={15} aria-hidden="true" />
                </a>
                <a className={styles.secondaryAction} href="#assessment-bases">
                  Consultar prioridades <ArrowDownRight size={15} aria-hidden="true" />
                </a>
              </>
            )}
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
          La escala compara la formalización y consistencia de los procesos. El nivel declarado
          y la lectura con evidencia se calculan por separado.
        </p>
        <ol className={styles.levelList}>
          {NIVELES_MADUREZ.map((nivel, indice) => {
            const maximo = NIVELES_MADUREZ[indice + 1]?.umbralMinimo;
            return (
              <li key={nivel.nivel} className={nivel.nivel === resultado.nivelAjustado ? styles.currentLevel : ""}>
                <span className={styles.listNumber}>N{nivel.nivel}</span>
                <div>
                  <strong>{nivel.etiqueta}</strong>
                  <span className={styles.range}>{nivel.umbralMinimo}%–{maximo === undefined ? 100 : maximo - 1}%</span>
                  <p>{nivel.descripcion}</p>
                </div>
              </li>
            );
          })}
        </ol>
        <p className={styles.dialogFootnote}>Los límites por controles estructurales, evidencia y cobertura pueden ajustar el nivel resultante.</p>
      </dialog>

      <MaturityPath nivelActual={verificado.nivelAjustado} nivelDeclarado={resultado.nivelTeorico}
        nivelDegradado={resultado.nivelAjustado} scoreActual={verificado.scorePonderado}
        soloReferencia={verificado.soloReferencia} pendientes={hitos} />

      <div className={styles.comparison} aria-label="Comparación de resultados">
        <div className={styles.comparisonHeading}>
          <div>
            <span className={styles.sectionLabel}>Tres estados del mismo diagnóstico</span>
            <p>La declaración, los límites metodológicos y la evidencia muestran por qué difieren los niveles.</p>
          </div>
          {diferencia > 0.05 && (
            <div className={styles.gap}>
              <strong>{diferencia.toFixed(1)}</strong>
              <span>puntos de distancia</span>
            </div>
          )}
        </div>
        <div className={`${styles.trackRow} ${styles.reportedReading}`}>
          <div className={styles.trackTop}>
            <span>Estado declarado <small>Nivel {resultado.nivelTeorico}</small></span>
            <strong>{resultado.scorePonderado.toFixed(1)}%</strong>
          </div>
          <div className={styles.track} role="img" aria-label={`Puntaje según respuestas: ${resultado.scorePonderado.toFixed(1)} por ciento`}>
            <span className={styles.reportedFill} style={{ width: `${Math.min(100, Math.max(0, resultado.scorePonderado))}%` }} />
          </div>
        </div>
        <div className={styles.degradedReading}>
          <span>Estado degradado por límites metodológicos <small>Nivel {resultado.nivelAjustado}</small></span>
          <span>{resultado.nivelAjustado < resultado.nivelTeorico ? "El nivel se ajusta; el score declarado se conserva." : "Sin reducción del nivel declarado."}</span>
        </div>
        <div className={`${styles.trackRow} ${styles.verifiedReading}`}>
          <div className={styles.trackTop}>
            <span>Estado actual con evidencia vinculada <BadgeCheck size={14} aria-hidden="true" /> <small>Nivel {verificado.nivelAjustado}</small></span>
            <strong>{verificado.scorePonderado.toFixed(1)}%</strong>
          </div>
          <div className={styles.track} role="img" aria-label={`Puntaje con evidencia vinculada: ${verificado.scorePonderado.toFixed(1)} por ciento`}>
            <span className={styles.verifiedFill} style={{ width: `${Math.min(100, Math.max(0, verificado.scorePonderado))}%` }} />
          </div>
          {sinRespaldo ? (
            <p className={styles.evidenceInsight}>
              <strong>¿Por qué Nivel 1?</strong> No hay documentos vinculados a los {resultado.totalEvaluados} controles evaluados.
              En esta lectura, la evidencia se considera E0 y limita cada control al nivel efectivo 1.
              El puntaje mostrado es un mínimo técnico; no representa madurez demostrada.
              Vincular evidencia permite recalcular el resultado, sin garantizar por sí solo un nivel superior.
            </p>
          ) : (
            <p className={styles.evidenceNote}>
              {documentos} de {resultado.totalEvaluados} controles tienen documentos vinculados.
              {documentos === 0 && " Sin cobertura suficiente no se emite un nivel, y el puntaje técnico no representa madurez demostrada."}
              {" "}Nivel resultante: {verificado.nivelAjustado} · {verificado.nivelAjustadoEtiqueta}.
            </p>
          )}
        </div>
      </div>

      {motivos.length > 0 && (
        <div className={styles.explanation}>
          <strong>Condiciones que limitan el nivel.</strong>{" "}
          Las respuestas corresponden al nivel {resultado.nivelTeorico}; el diagnóstico
          registra el nivel {resultado.nivelAjustado} por las siguientes condiciones:
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
