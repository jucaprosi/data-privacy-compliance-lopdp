"""Generador de Informes DIA-10: Informe Ejecutivo y Técnico post-diagnóstico.
Soporta formatos Markdown estructurado y HTML corporativo de alta fidelidad.
Invariantes: Cero dilución de brechas críticas, separación explícita de vectores ortogonales.
"""
from datetime import datetime
from typing import List, Dict, Optional
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    RespuestaDiagnostico,
    ScoringDiagnostico,
    NivelEvidencia,
)
from features.diagnostico.services.engine import (
    generar_banco_preguntas_diagnostico,
)
from features.diagnostico.services.dimensiones_sgpdp import (
    DIMENSIONES_SGPDP,
)

def _obtener_banco_dict(tamano: Optional[str] = None):
    banco_lista = generar_banco_preguntas_diagnostico(tamano=tamano)
    return {
        p.id_pregunta: p for p in banco_lista
    }

def _agrupar_respuestas_por_dimension(
    respuestas: List[RespuestaDiagnostico],
    banco: Dict[str, any],
) -> Dict[str, Dict]:
    dims_dict = {d.id: {"nombre": d.nombre, "total": 0, "afirmativas": 0, "brechas": 0, "evidencias": 0} for d in DIMENSIONES_SGPDP}
    
    for r in respuestas:
        p = banco.get(str(r.id_pregunta))
        if not p:
            continue
        dim_id = p.dominio_id
        dim = dims_dict.get(dim_id)
        if dim:
            dim["total"] += 1
            if r.respuesta_afirmativa:
                dim["afirmativas"] += 1
                if r.nivel_evidencia != NivelEvidencia.E0_VERBAL:
                    dim["evidencias"] += 1
            else:
                dim["brechas"] += 1
    return dims_dict

def _nivel_por_dimension(scoring: ScoringDiagnostico) -> Dict[str, str]:
    """«n · etiqueta» de cada dimensión con controles aplicables; nunca un nivel de la organización."""
    return {
        d.id: (f"{d.nivel} · {d.nivel_etiqueta}" if d.nivel else d.nivel_etiqueta)
        for d in scoring.por_dimension
    }


def generar_informe_markdown(
    ficha: FichaOrganizacion,
    scoring: ScoringDiagnostico,
    respuestas: List[RespuestaDiagnostico],
) -> str:
    """Genera informe exhaustivo en formato Markdown estructurado."""
    banco = _obtener_banco_dict(ficha.tamano)
    resumen_dimensiones = _agrupar_respuestas_por_dimension(respuestas, banco)
    niveles = _nivel_por_dimension(scoring)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md = [
        f"# JUBYS Plataforma LOPDP 360 · Informe Ejecutivo de Diagnóstico",
        f"**Organización / Tenant:** `{ficha.tenant_id}` | **Sector:** {ficha.sector} | **Tamaño:** {ficha.tamano}",
        f"**Fecha de Emisión:** {fecha_actual} | **Tiempo Estimado de Evaluación:** {scoring.duracion_minutos_estimada} min",
        "",
        "---",
        "## 1. Vector de Madurez y Conformidad Normativa (Scoring Multidimensional)",
        "",
        "- **Madurez SPDP:** por dimensión (sección 2); no se emite una cifra global de la organización",
        f"- **Conformidad Jurídica Global:** `{scoring.porcentaje_conformidad_juridica}%`",
        f"- **Cobertura de Evidencia Verificable:** `{scoring.cobertura_evidencia_porcentaje}%`",
        f"- **Brechas Críticas Abiertas:** `{scoring.brechas_criticas_abiertas}` hallazgos no conformes",
        f"- **Preguntas Totales Respondidas:** `{scoring.preguntas_respondidas_total}`",
        "",
        "> [!IMPORTANT]",
        "> Bajo el principio de no-dilución, un alto porcentaje de cumplimiento procedimental no enmascara las brechas críticas abiertas ni la carencia de evidencia verificable (E0 vs E3).",
        "",
        "---",
        "## 2. Estado de Madurez por las 10 Dimensiones del SGPDP",
        "",
        "| ID | Dimensión SGPDP | Nivel | Evaluadas | Conformes | Brechas | Cobertura Evidencias |",
        "|---|---|---|:---:|:---:|:---:|:---:|",
    ]
    
    for dim_id, data in resumen_dimensiones.items():
        if data["total"] > 0:
            pct_ev = round((data["evidencias"] / data["total"]) * 100, 1) if data["total"] > 0 else 0.0
            md.append(f"| `{dim_id}` | {data['nombre']} | {niveles.get(dim_id, 'Sin evaluación suficiente')} | {data['total']} | {data['afirmativas']} | {data['brechas']} | {pct_ev}% |")
            
    md.extend([
        "",
        "---",
        "## 3. Catálogo de Brechas Críticas y Acciones de Mitigación Inmediata",
        "",
    ])
    
    brechas_encontradas = 0
    for r in respuestas:
        if not r.respuesta_afirmativa:
            brechas_encontradas += 1
            p = banco.get(str(r.id_pregunta))
            enunciado = p.enunciado if p else "Control operativo pendiente"
            control_nombre = p.control if (p and p.control) else f"Control {r.id_pregunta}"
            ref = p.referencia_normativa if p else "LOPDP"
            md.append(f"### Brecha #{brechas_encontradas}: Control {r.id_pregunta} · {control_nombre}")
            md.append(f"- **Enunciado:** {enunciado}")
            md.append(f"- **Referencia Normativa:** {ref}")
            md.append(f"- **Estado de Evidencia:** {r.nivel_evidencia.value}")
            if r.rationale:
                md.append(f"- **Observación:** {r.rationale}")
            md.append("")
            
    if brechas_encontradas == 0:
        md.append("✅ **No se identificaron brechas críticas en los controles evaluados.**")
        md.append("")
        
    md.extend([
        "---",
        "## 4. Plan de Acción Recomendado (Hoja de Ruta 30 / 60 / 90 Días)",
        "",
        "### Inmediato (30 Días): Contención y Legalidad Base",
        "- Formalización del Delegado de Protección de Datos (DPD/DPO) e inscripción ante la SPDP (si aplica).",
        "- Regularización de cláusulas contractuales con encargados de tratamiento (DPA / Art. 50 LOPDP).",
        "- Publicación y actualización de políticas de privacidad accesibles para los titulares.",
        "",
        "### Mediano Plazo (60 Días): Registro de Actividades y Seguridad",
        "- Levantamiento completo del Registro de Actividades de Tratamiento (RAT) por cada área de negocio.",
        "- Implementación del protocolo de gestión y notificación de brechas de seguridad (72 horas / Art. 42 LOPDP).",
        "- Ejecución del test paramétrico MTGE para confirmar o descartar tratamiento a gran escala.",
        "",
        "### Largo Plazo (90 Días): Resiliencia y Mejora Continua",
        "- Auditorías periódicas a medidas técnicas y organizativas de seguridad (ISO 27001 / ISO 27701).",
        "- Evaluación de Impacto de Protección de Datos (EIPD) en tratamientos de alto riesgo o IA.",
        "- Cierre y seguimiento formal de acciones correctivas en el módulo CAPA.",
        "",
        "---",
        "_Documento emitido automáticamente por el Motor Determinista de JUBYS Plataforma LOPDP 360._"
    ])
    
    return "\n".join(md)

def generar_informe_html(
    ficha: FichaOrganizacion,
    scoring: ScoringDiagnostico,
    respuestas: List[RespuestaDiagnostico],
) -> str:
    """Genera informe en formato HTML corporativo listo para visualización e impresión a PDF."""
    banco = _obtener_banco_dict(ficha.tamano)
    resumen_dimensiones = _agrupar_respuestas_por_dimension(respuestas, banco)
    niveles = _nivel_por_dimension(scoring)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    filas_tabla = ""
    for dim_id, data in resumen_dimensiones.items():
        if data["total"] > 0:
            pct_ev = round((data["evidencias"] / data["total"]) * 100, 1)
            filas_tabla += f"""
            <tr>
                <td style="font-weight:600; color:#1e293b;">{dim_id}</td>
                <td>{data['nombre']}</td>
                <td>{niveles.get(dim_id, 'Sin evaluación suficiente')}</td>
                <td style="text-align:center;">{data['total']}</td>
                <td style="text-align:center; color:#16a34a; font-weight:600;">{data['afirmativas']}</td>
                <td style="text-align:center; color:#dc2626; font-weight:600;">{data['brechas']}</td>
                <td style="text-align:center;">{pct_ev}%</td>
            </tr>
            """
            
    lista_brechas = ""
    num_b = 0
    for r in respuestas:
        if not r.respuesta_afirmativa:
            num_b += 1
            p = banco.get(str(r.id_pregunta))
            enunciado = p.enunciado if p else "Control operativo pendiente"
            control_nombre = p.control if (p and p.control) else f"Control {r.id_pregunta}"
            ref = p.referencia_normativa if p else "LOPDP"
            lista_brechas += f"""
            <div style="background:#fff1f2; border-left:4px solid #e11d48; padding:12px 16px; margin-bottom:12px; border-radius:4px;">
                <div style="font-weight:700; color:#9f1239;">Brecha #{num_b} · Control {r.id_pregunta}: {control_nombre}</div>
                <div style="color:#334155; margin-top:4px;">{enunciado}</div>
                <div style="font-size:12px; color:#64748b; margin-top:4px;"><strong>Referencia:</strong> {ref} | <strong>Nivel Evidencia:</strong> {r.nivel_evidencia.value}</div>
            </div>
            """
            
    if not lista_brechas:
        lista_brechas = "<p style='color:#16a34a; font-weight:600;'>✅ No se identificaron brechas críticas en la evaluación realizada.</p>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Informe de Diagnóstico LOPDP 360 - {ficha.tenant_id}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px auto; max-width: 900px; color: #1e293b; line-height: 1.5; }}
    .header {{ border-bottom: 2px solid #0284c7; padding-bottom: 16px; margin-bottom: 24px; }}
    .brand {{ font-size: 20px; font-weight: 800; color: #0369a1; letter-spacing: -0.5px; }}
    .title {{ font-size: 26px; font-weight: 700; color: #0f172a; margin: 6px 0; }}
    .meta {{ font-size: 14px; color: #64748b; }}
    .grid-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; }}
    .card-val {{ font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 4px; }}
    .card-lbl {{ font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
    th {{ background: #f1f5f9; text-align: left; padding: 10px 12px; border-bottom: 2px solid #cbd5e1; color: #475569; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
    .section-title {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 32px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }}
    .plan-box {{ background: #f0fdf4; border-left: 4px solid #16a34a; padding: 14px 18px; margin: 12px 0; border-radius: 4px; }}
    .footer {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
    <div class="header">
        <div class="brand">JUBYS · PLATAFORMA LOPDP 360</div>
        <div class="title">Informe Ejecutivo y Técnico de Diagnóstico de Privacidad</div>
        <div class="meta">Organización: <strong>{ficha.tenant_id}</strong> | Sector: {ficha.sector} | Fecha: {fecha_actual}</div>
    </div>

    <div class="grid-metrics">
        <div class="card">
            <div class="card-lbl">Madurez SPDP</div>
            <div class="card-val" style="color:#0284c7; font-size:16px;">Por dimensión</div>
            <div style="font-size:11px; font-weight:600; color:#0369a1; margin-top:2px;">Sin cifra global de la organización</div>
        </div>
        <div class="card">
            <div class="card-lbl">Conformidad Jurídica</div>
            <div class="card-val" style="color:#16a34a;">{scoring.porcentaje_conformidad_juridica}%</div>
            <div style="font-size:11px; color:#64748b; margin-top:2px;">Controles conformes</div>
        </div>
        <div class="card">
            <div class="card-lbl">Cobertura Evidencia</div>
            <div class="card-val" style="color:#8b5cf6;">{scoring.cobertura_evidencia_porcentaje}%</div>
            <div style="font-size:11px; color:#64748b; margin-top:2px;">Evidencia informal o superior</div>
        </div>
        <div class="card">
            <div class="card-lbl">Brechas Críticas</div>
            <div class="card-val" style="color:#dc2626;">{scoring.brechas_criticas_abiertas}</div>
            <div style="font-size:11px; color:#dc2626; margin-top:2px; font-weight:600;">Acción inmediata</div>
        </div>
    </div>

    <div class="section-title">2. Estado de Cumplimiento por las 10 Dimensiones del SGPDP</div>
    <table>
        <thead>
            <tr>
                <th style="width:8%;">ID</th>
                <th style="width:30%;">Dimensión SGPDP</th>
                <th style="width:16%;">Nivel</th>
                <th style="width:12%; text-align:center;">Evaluadas</th>
                <th style="width:12%; text-align:center;">Conformes</th>
                <th style="width:12%; text-align:center;">Brechas</th>
                <th style="width:14%; text-align:center;">Cobertura</th>
            </tr>
        </thead>
        <tbody>
            {filas_tabla}
        </tbody>
    </table>

    <div class="section-title">3. Catálogo de Brechas Identificadas</div>
    {lista_brechas}

    <div class="section-title">4. Plan de Acción de Mitigación Inmediata</div>
    <div class="plan-box">
        <strong>Prioridades Inmediatas (30 Días):</strong> Formalización de DPD/DPO, adecuación de contratos con terceros encargados y publicación de avisos de privacidad transparentes.
    </div>
    <div class="plan-box" style="background:#eff6ff; border-left-color:#2563eb;">
        <strong>Hitos a Mediano Plazo (60 Días):</strong> Registro y consolidación del RAT, implementación del canal de derechos y protocolo de notificación de brechas en 72h.
    </div>

    <div class="footer">
        JUBYS Plataforma LOPDP 360 - Motor Determinista de Conformidad Regulatoria - Ecuador
    </div>
</body>
</html>
"""
    return html
