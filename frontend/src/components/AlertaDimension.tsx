"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, ArrowRight, CheckCircle2, ChevronDown, Compass, Scale, X } from "lucide-react";
import { DIMENSION_POR_ID, type DimensionId } from "@/lib/dimensionesSGPDP";
import { ALERTAS_DIMENSION } from "@/lib/alertasDimension";
import dimensionStyles from "./DimensionIdentity.module.css";
import styles from "./AlertaDimension.module.css";

interface Props {
  dimensionId?: DimensionId;
  esPrimeraPregunta: boolean;
  activo: boolean;
}

export default function AlertaDimension({ dimensionId, esPrimeraPregunta, activo }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const vistas = useRef(new Set<DimensionId>());
  const [abierta, setAbierta] = useState(false);

  useEffect(() => {
    if (!activo || !dimensionId || !esPrimeraPregunta || vistas.current.has(dimensionId)) return;
    vistas.current.add(dimensionId);
    setAbierta(true);
  }, [activo, dimensionId, esPrimeraPregunta]);

  useEffect(() => {
    if (!activo && abierta) setAbierta(false);
  }, [activo, abierta]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (abierta && !dialog.open) dialog.showModal();
    if (!abierta && dialog.open) dialog.close();
  }, [abierta]);

  if (!dimensionId) return null;
  const contenido = ALERTAS_DIMENSION[dimensionId];
  const dimension = DIMENSION_POR_ID[dimensionId];

  return (
    <dialog
      ref={dialogRef}
      className={`${dimensionStyles.identity} ${styles.dialog}`}
      data-dimension={dimensionId}
      aria-labelledby="alerta-dimension-titulo"
      aria-describedby="alerta-dimension-resumen"
      onClose={() => setAbierta(false)}
      onClick={(event) => { if (event.target === dialogRef.current) setAbierta(false); }}
    >
      <div className={styles.content}>
        <div className={styles.hero}>
          <div className={styles.header}>
            <span className={styles.eyebrow}><Compass size={15} /> Perspectiva ejecutiva · {dimension.id} de 10</span>
            <button type="button" className={styles.close} aria-label="Cerrar alerta" onClick={() => setAbierta(false)}><X size={19} /></button>
          </div>
          <p className={styles.dimensionName}>{dimension.nombre}</p>
          <h2 id="alerta-dimension-titulo" className={styles.title}>{contenido.titular}</h2>
          <div className={styles.executiveRisk}>
            <AlertTriangle size={18} aria-hidden="true" />
            <p><strong>El riesgo de aplazarlo:</strong> una infracción verificada puede dar lugar a multas de entre el 0,1 % y el 1 % del volumen de negocio anterior. La falta de controles también puede dificultar contratos que exigen garantías de privacidad y dar pie a reclamaciones, según los hechos.</p>
          </div>
          <p id="alerta-dimension-resumen" className={styles.lead}>Aquí comprobará {contenido.enfoque}.</p>
        </div>
        <div className={styles.body}>
          <div className={styles.path} aria-label="Riesgo, decisión y resultado">
            <section className={styles.impact}>
              <div className={styles.step}><AlertTriangle size={16} /><span>01 · Riesgo para el negocio</span></div>
            <p>{contenido.impacto}</p>
            </section>
            <div className={styles.connector} aria-hidden="true"><ArrowRight size={17} /></div>
            <section className={styles.action}>
              <div className={styles.step}><Compass size={16} /><span>02 · Decisión inmediata</span></div>
            <p>{contenido.accion}</p>
            </section>
          </div>
          <div className={styles.benefit}><CheckCircle2 size={20} /><p><strong>Lo que gana al actuar:</strong> {contenido.beneficio}</p></div>
          <details className={styles.legal}>
            <summary><span><Scale size={17} /> Marco legal y posibles consecuencias</span><ChevronDown size={17} className={styles.chevron} /></summary>
            <div className={styles.legalContent}>
              <p>Si la autoridad verifica una infracción, puede ordenar medidas correctivas y sancionar. Para entidades privadas o empresas públicas, las multas previstas por la LOPDP son del <strong>0,1 % al 0,7 %</strong> del volumen de negocio anterior para infracciones leves y del <strong>0,7 % al 1 %</strong> para graves. La clasificación y el importe dependen de la conducta y las circunstancias; una respuesta negativa no genera una multa automática.</p>
              <p>Según los hechos, los titulares podrían reclamar reparación por daños. Si existe una conducta independiente tipificada en el COIP, también podría haber una investigación penal. La falta de garantías puede dificultar acuerdos con clientes internacionales; no genera por sí sola una inhabilitación para negociar con Europa. El RGPD europeo solo se aplica cuando concurren sus criterios territoriales y materiales.</p>
              <div className={styles.sources}>
                <a href="https://www.registroficial.gob.ec/quinto-suplemento-al-registro-oficial-no-459/" target="_blank" rel="noopener noreferrer">LOPDP, arts. 67–72 ↗</a>
                <a href="https://spdp.gob.ec/wp-content/uploads/2025/07/22.02-Modelo-calculo-sanciones-administrativas.pdf" target="_blank" rel="noopener noreferrer">Modelo de cálculo SPDP ↗</a>
                <a href="https://www.asambleanacional.gob.ec/sites/default/files/coip.pdf" target="_blank" rel="noopener noreferrer">COIP ↗</a>
                <a href="https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/" target="_blank" rel="noopener noreferrer">RGPD, art. 3 ↗</a>
              </div>
            </div>
          </details>
          <div className={styles.footer}>
            <span className={styles.note}>Evaluación orientativa · la respuesta no determina una sanción</span>
            <button type="button" className={styles.primary} onClick={() => setAbierta(false)}>Evaluar esta dimensión <ArrowRight size={16} /></button>
          </div>
        </div>
      </div>
    </dialog>
  );
}
