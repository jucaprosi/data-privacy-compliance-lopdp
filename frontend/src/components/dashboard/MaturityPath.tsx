"use client";

import { useAuditStore } from "@/store/useAuditStore";
import { useMaturityProjection } from "./useMaturityProjection";
import styles from "./MaturityPath.module.css";

interface Props {
  nivelActual: number;
  nivelDeclarado: number;
  nivelDegradado: number;
  scoreActual: number;
  soloReferencia: boolean;
  pendientes: string[];
}

const y = (nivel: number) => 172 - (nivel - 1) * 34;
const x = (mes: number) => 46 + (mes * 507) / 6;
const etiquetaNivel = (nivel: number) => nivel >= 1 ? `N${nivel}` : "Pendiente";

export default function MaturityPath({ nivelActual, nivelDeclarado, nivelDegradado, scoreActual, soloReferencia, pendientes }: Props) {
  const proyectoActivo = useAuditStore((state) => state.proyectoActivo);
  const razonSocial = useAuditStore((state) => state.companyData.razonSocial);
  const projectKey = proyectoActivo?.id ?? razonSocial;
  const { projectedAt, trendAvailable, monthsToLevel3 } = useMaturityProjection(
    projectKey, nivelActual, scoreActual, soloReferencia
  );
  const hayNivel = nivelActual >= 1;
  const nivelMes6 = projectedAt(6);
  // Una separación visual mínima permite distinguir lecturas que coinciden en el mismo nivel.
  const yDeclarado = y(nivelDeclarado) - (nivelDeclarado === nivelDegradado || nivelDeclarado === nivelActual ? 3 : 0);
  const yDegradado = y(nivelDegradado) + (nivelDegradado === nivelDeclarado || nivelDegradado === nivelActual ? 3 : 0);
  const desfaseEvidencia = nivelActual === nivelDeclarado && nivelActual !== nivelDegradado ? 3 : 0;
  const ruta = [0, 2, 4, 6].map((mes) => `${x(mes)},${y(projectedAt(mes)) + desfaseEvidencia}`).join(" ");
  const hitos = pendientes.slice(0, 3);
  const horizonteNivel3 = monthsToLevel3 === null
    ? null
    : monthsToLevel3 < 1 ? "menos de un mes" : `aproximadamente ${Math.ceil(monthsToLevel3)} meses`;

  return (
    <section className={styles.path} aria-labelledby="maturity-path-title">
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>Ruta de madurez · horizonte de 6 meses</span>
          <h3 id="maturity-path-title">Primera fase: alcanzar y sostener el Nivel 3</h3>
        </div>
        <span className={styles.goal}>Meta final · Nivel 5</span>
      </div>
      <p className={styles.description}>
        <strong>Nivel 3 · Definido:</strong> primer umbral de control demostrable en esta escala.
        La organización cuenta con un Sistema de Gestión (SGPDP), políticas escritas,
        inventario de tratamientos (RAT), acuerdos de confidencialidad y protocolos de
        respuesta a incidentes. El personal conoce sus responsabilidades y conserva
        evidencias para demostrar su gestión ante la SPDP.
      </p>
      <div className={styles.legend} aria-label="Lecturas del diagnóstico">
        <span className={styles.declaredKey}>Declarado · {etiquetaNivel(nivelDeclarado)}</span>
        <span className={styles.degradedKey}>Degradado · {etiquetaNivel(nivelDegradado)}</span>
        <span className={styles.verifiedKey}>Actual con evidencia · {etiquetaNivel(nivelActual)}</span>
      </div>
      <svg className={styles.chart} viewBox="0 0 600 212" role="img"
        aria-label={hayNivel
          ? `Declarado: nivel ${nivelDeclarado}. Degradado por límites: nivel ${nivelDegradado}. Actual con evidencia: nivel ${nivelActual}. Proyección de la lectura con evidencia al mes 6: ${nivelMes6.toFixed(1)}. Referencia de primera fase en nivel 3; meta final en nivel 5.`
          : "Sin nivel emitido por cobertura insuficiente. Referencia de primera fase en nivel 3 y meta final en nivel 5."}>
        {[1, 2, 3, 4, 5].map((nivel) => (
          <g key={nivel}>
            <line x1="46" x2="568" y1={y(nivel)} y2={y(nivel)}
              className={nivel === 3 ? styles.targetLine : styles.gridLine} />
            <text x="8" y={y(nivel) + 4} className={styles.tick}>N{nivel}</text>
          </g>
        ))}
        <text x="432" y={y(5) - 7} className={styles.finalText}>META FINAL · N5</text>
        <text x="405" y={y(3) - 7} className={styles.targetText}>PRIMERA FASE · N3</text>
        {[0, 2, 4, 6].map((mes) => (
          <text key={mes} x={x(mes)} y="199" textAnchor={mes === 0 ? "start" : "middle"}
            className={styles.tick}>Mes {mes}</text>
        ))}
        {nivelDeclarado >= 1 && <line x1={x(0)} x2={x(6)} y1={yDeclarado} y2={yDeclarado} className={styles.declaredLine} />}
        {nivelDegradado >= 1 && <line x1={x(0)} x2={x(6)} y1={yDegradado} y2={yDegradado} className={styles.degradedLine} />}
        {hayNivel && (
          <>
            <polyline points={ruta} className={styles.routeLine} />
            <circle cx={x(0)} cy={y(nivelActual) + desfaseEvidencia} r="6" className={styles.currentPoint} />
            <circle cx={x(6)} cy={y(nivelMes6) + desfaseEvidencia} r="5" className={styles.projectedPoint} />
          </>
        )}
      </svg>
      <p className={styles.chartCaption}>Declarado y degradado son lecturas del corte actual; solo la línea con evidencia muestra una proyección según el historial observado.</p>
      <p className={styles.projectionNote}>
        {!hayNivel
          ? "Complete la cobertura mínima para obtener una lectura verificable y activar la proyección."
          : trendAvailable
            ? `Proyección al mes 6: Nivel ${nivelMes6.toFixed(1)} según el ritmo observado en los niveles verificados.${horizonteNivel3 ? ` Si ese ritmo continúa, el Nivel 3 podría alcanzarse en ${horizonteNivel3}.` : " Aún no hay una tendencia ascendente hacia el Nivel 3."}`
            : `Base al mes 6: Nivel ${nivelActual} si no se registran cambios. Aún no hay historial suficiente para estimar cuándo se alcanzará el Nivel 3.`}
      </p>
      <div className={styles.milestones}>
        {(hitos.length > 0 ? hitos : ["Mantener controles y evidencias al día"]).map((hito, indice) => (
          <span key={hito}><strong>{indice + 1}.</strong> {hito}</span>
        ))}
      </div>
      <p className={styles.disclaimer}>
        La proyección se actualiza con cambios observados en el nivel verificado; no anticipa acciones futuras ni certifica cumplimiento legal.
      </p>
    </section>
  );
}
