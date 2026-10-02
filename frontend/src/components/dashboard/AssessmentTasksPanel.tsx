"use client";

import { ArrowUpRight, BadgeCheck, ClipboardList } from "lucide-react";
import { BANCO_PREGUNTAS, normalizarTamano, podarBancoPorTamano } from "@/lib/bancoPreguntas";
import { CONTROLES_ESTRUCTURALES } from "@/lib/dimensionesSGPDP";
import { brechaPrioritaria } from "@/lib/assessmentPriorities";
import { useAuditStore } from "@/store/useAuditStore";
import dimensionStyles from "@/components/DimensionIdentity.module.css";
import styles from "./AssessmentTasksPanel.module.css";

export default function AssessmentTasksPanel() {
  const {
    calcularResultadoAssessment, respuestas, evidencias, companyData,
    setPreguntaActualIndex, setActiveView,
  } = useAuditStore();
  const resultado = calcularResultadoAssessment("verificado");
  const vinculados = new Set(evidencias.flatMap((e) => e.controlesVinculados));
  const preguntas = podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(companyData.tamano), companyData.perfil);
  const indiceDe = (id: number) => preguntas.findIndex((pregunta) => pregunta.id === id);
  const abrirControl = (id: number) => {
    const indice = indiceDe(id);
    if (indice >= 0) setPreguntaActualIndex(indice);
    setActiveView("diagnostico");
  };

  const responsable = respuestas.find((r) => r.preguntaId === 2);
  const responsableAsignado = responsable?.cumple === "Conforme" && vinculados.has(2);
  const brecha = brechaPrioritaria(resultado.brechas.filter((item) => item.preguntaId !== 2));
  const control = brecha && preguntas.find((pregunta) => pregunta.id === brecha.preguntaId);
  const estructural = brecha && CONTROLES_ESTRUCTURALES.find((item) => item.preguntaId === brecha.preguntaId);
  const respuestaControl = respuestas.find((item) => item.preguntaId === brecha?.preguntaId);

  return (
    <section id="assessment-tasks" className={styles.panel} aria-labelledby="tasks-title">
      <div className={styles.header}>
        <div className={styles.heading}>
          <ClipboardList size={20} aria-hidden="true" />
          <div>
            <span className={styles.eyebrow}>Plan de acción vinculado al diagnóstico</span>
            <h3 id="tasks-title">Tasks · siguiente brecha prioritaria</h3>
          </div>
        </div>
        <span className={styles.count}>{resultado.brechas.length} brechas en la lectura con evidencia</span>
      </div>
      <p className={styles.intro}>
        El score se recalcula con las respuestas y evidencias del diagnóstico. Completar una gestión fuera de la plataforma
        no modifica el resultado hasta registrar el control y vincular su respaldo.
      </p>

      <div className={styles.steps}>
        <article data-dimension="D01" className={`${dimensionStyles.identity} ${styles.step}`}>
          <span className={styles.stepNumber}>01</span>
          <div className={styles.stepBody}>
            <div className={styles.stepHeading}>
              <div className={styles.stepTitle}>
                <span className={`${dimensionStyles.dimensionBadge} ${styles.dimensionTag}`}>D01</span>
                <h4>Establecer la responsabilidad de protección de datos</h4>
              </div>
              <span className={responsableAsignado ? styles.done : styles.pending}>
                {responsableAsignado ? "Registrado con respaldo" : "Prioridad habilitadora"}
              </span>
            </div>
            <p>Designar por escrito a la persona responsable, definir sus funciones y comunicar el mandato a los equipos.</p>
            <p className={styles.evidence}>Evidencia esperada: {preguntas.find((item) => item.id === 2)?.evidenciaVigente ?? "designación escrita del responsable"}.</p>
            <button type="button" onClick={() => abrirControl(2)}>Abrir control P2 <ArrowUpRight size={14} /></button>
          </div>
        </article>

        {brecha && control ? (
          <article data-dimension={control.dimensionId} className={`${dimensionStyles.identity} ${styles.step}`}>
            <span className={styles.stepNumber}>02</span>
            <div className={styles.stepBody}>
              <div className={styles.stepHeading}>
                <div className={styles.stepTitle}>
                  <span className={`${dimensionStyles.dimensionBadge} ${styles.dimensionTag}`}>{control.dimensionId}</span>
                  <h4>Corregir P{brecha.preguntaId}: {brecha.control}</h4>
                </div>
                <span className={styles.pending}>{brecha.esEstructural ? "Estructural" : brecha.severidad}</span>
              </div>
              <p>{estructural?.accionPrioritaria ?? `Definir y ejecutar el procedimiento para ${brecha.control.toLowerCase()}.`}</p>
              <p className={styles.evidence}>Evidencia esperada: {control.evidenciaVigente}.</p>
              <div className={styles.status}>
                <span>{respuestaControl?.cumple === "Conforme" ? "Respuesta implementada" : "Respuesta por corregir"}</span>
                <span><BadgeCheck size={13} /> {vinculados.has(brecha.preguntaId) ? "Documento vinculado" : "Documento pendiente"}</span>
              </div>
              <button type="button" onClick={() => abrirControl(brecha.preguntaId)}>
                Revisar respuesta y vincular evidencia <ArrowUpRight size={14} />
              </button>
            </div>
          </article>
        ) : (
          <article className={styles.step}>
            <span className={styles.stepNumber}>02</span>
            <div className={styles.stepBody}>
              <h4>Continuar con la verificación periódica</h4>
              <p>No hay una brecha evaluada pendiente. Revise la cobertura y mantenga las evidencias actualizadas.</p>
            </div>
          </article>
        )}
      </div>
    </section>
  );
}
