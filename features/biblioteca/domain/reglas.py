# ¤adpa
# ¤¤developer-architect
"""Modelos de dominio y definición de reglas deterministas de aplicabilidad (BIB-204).

Cada regla evaluada devuelve de forma determinista:
- Aplica
- No aplica
- Información insuficiente

Invariante fundamental (¬R): Un dato desconocido o ausente SIEMPRE mantiene
'Información insuficiente' y NUNCA se infiere o convierte en 'No aplica'.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


# ¤adpa
class ResultadoAplicabilidad(str, Enum):
    APLICA = "Aplica"
    NO_APLICA = "No aplica"
    INFORMACION_INSUFICIENTE = "Información insuficiente"


# ¤adpa
class NaturalezaPlantilla(str, Enum):
    OBLIGACION_LEGAL = "Obligación legal"
    OBLIGACION_CONDICIONAL = "Obligación condicional"
    MEDIDA_DEMOSTRATIVA = "Medida demostrativa"
    BUENA_PRACTICA = "Buena práctica"


# ¤adpa
@dataclass(frozen=True)
class ReglaEvaluada:
    """Resultado determinista de una regla particular."""
    regla_id: str
    nombre: str
    resultado: ResultadoAplicabilidad
    explicacion: str
    fuente_normativa: str
    version_regla: str
    hechos_analizados: dict[str, Any] = field(default_factory=dict)
    hechos_faltantes: list[str] = field(default_factory=list)


# ¤adpa
@dataclass(frozen=True)
class ModificacionHumana:
    """Corrección manual de la aplicabilidad por parte de un usuario autorizado."""
    resultado_original: ResultadoAplicabilidad
    resultado_modificado: ResultadoAplicabilidad
    motivo: str
    evidencia: str
    autor_id: str
    fecha: datetime
    es_obligacion_confirmada: bool = False
    revisor_juridico_id: str | None = None


# ¤adpa
@dataclass(frozen=True)
class EvaluacionPlantilla:
    """Evaluación de aplicabilidad explicable de una plantilla."""
    codigo: str
    nombre: str
    resultado: ResultadoAplicabilidad
    resultado_calculado: ResultadoAplicabilidad
    tipo: str
    familia: str
    formato: str
    naturaleza: str
    es_obligacion: bool
    fuentes_normativas: list[str]
    version_regla: str
    motivo_recomendacion: str
    hechos_relevantes: dict[str, Any] = field(default_factory=dict)
    hechos_faltantes: list[str] = field(default_factory=list)
    reglas_evaluadas: list[ReglaEvaluada] = field(default_factory=list)
    modificacion_humana: ModificacionHumana | None = None


# ¤adpa
@dataclass(frozen=True)
class HechosOrganizacion:
    """Conjunto de hechos capturados de las compuertas de Organización, RAT y MTGE."""
    tenant_id: str
    tamano: str | None = None
    num_trabajadores: int | None = None
    sector: str | None = None
    datos_documentales: Mapping[str, Any] = field(default_factory=dict)
    rat_cargado: bool = False
    actividades_rat: list[Mapping[str, Any]] | None = None
    mtge_cargado: bool = False
    tiene_gran_escala: bool | None = None
    total_gran_escala: int | None = None


def _regla(
    rid: str, nom: str, res: ResultadoAplicabilidad, exp: str,
    fuente: str, hechos: dict[str, Any], faltantes: list[str],
) -> ReglaEvaluada:
    return ReglaEvaluada(
        regla_id=rid, nombre=nom, resultado=res, explicacion=exp,
        fuente_normativa=fuente, version_regla="1.0",
        hechos_analizados=hechos, hechos_faltantes=faltantes,
    )


# ¤adpa
def evaluar_ap01_datos_personales(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-01", "Datos personales presentes", "N01 (LOPDP Arts. 7 a 10)"
    if not hechos.rat_cargado or hechos.actividades_rat is None:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si la organización trata datos personales; inventario pendiente.",
                      fte, {"rat_cargado": hechos.rat_cargado}, ["actividades_rat"])
    if len(hechos.actividades_rat) > 0:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(hechos.actividades_rat)} actividades con datos personales.",
                      fte, {"total_actividades": len(hechos.actividades_rat)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                  "No hay actividades registradas en el RAT; requiere inventario para descartar.",
                  fte, {"total_actividades": 0}, ["inventario_actividades_datos"])


# ¤adpa
def evaluar_ap02_trabajadores_100(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-02", "Responsable y trabajadores >=100", "N02;N12 (RGLOPDP Art. 38, Oficio SPDP-IRD-2026-0064-O)"
    h: dict[str, Any] = {"num_trabajadores": hechos.num_trabajadores, "tamano": hechos.tamano}
    if hechos.num_trabajadores is None and hechos.tamano is None:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce el número de trabajadores o tamaño de la empresa.",
                      fte, h, ["tamano_o_num_trabajadores"])
    if hechos.num_trabajadores is not None:
        if hechos.num_trabajadores >= 100:
            return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                          f"Organización con {hechos.num_trabajadores} trabajadores (>= 100, obligación expresa).",
                          fte, h, [])
        return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                      f"Organización con {hechos.num_trabajadores} trabajadores (< 100).", fte, h, [])
    if hechos.tamano in ("mediana", "corporativo"):
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Tamaño registrado '{hechos.tamano}' supera los 100 trabajadores.", fte, h, [])
    if hechos.tamano in ("micro", "pequena"):
        return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                      f"Tamaño registrado '{hechos.tamano}' no alcanza el umbral de 100 trabajadores.", fte, h, [])
    return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                  f"Tamaño '{hechos.tamano}' no reconocido para evaluar umbral de trabajadores.", fte, h, ["tamano_valido"])


# ¤adpa
def evaluar_ap03_gran_escala(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-03", "Tratamiento a gran escala", "N09 (Res. SPDP-SPD-2026-0005-R Arts. 4 a 6)"
    if not hechos.mtge_cargado or hechos.tiene_gran_escala is None:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce la calificación de gran escala; evaluación MTGE pendiente.",
                      fte, {"mtge_cargado": hechos.mtge_cargado}, ["calificacion_gran_escala_mtge"])
    if hechos.tiene_gran_escala:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Tratamiento calificado a gran escala ({hechos.total_gran_escala or 1} actividad(es)).",
                      fte, {"tiene_gran_escala": True, "total_gran_escala": hechos.total_gran_escala}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "Ningún tratamiento evaluado califica como gran escala bajo la Res. 0005-R.",
                  fte, {"tiene_gran_escala": False, "total_gran_escala": 0}, [])


# ¤adpa
def evaluar_ap04_interes_legitimo(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-04", "Finalidad propone interés legítimo", "N01;N07 (SPDP-SPD-2025-0041-R Arts. 5 a 10)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconocen las bases de legitimación de los tratamientos.", fte, {}, ["actividades_rat"])
    coincidencias = [
        a for a in hechos.actividades_rat
        if str(a.get("base_legal", "")).upper() in ("INTERES_LEGITIMO", "BASELEGITIMACION.INTERES_LEGITIMO")
    ]
    if coincidencias:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se detectaron {len(coincidencias)} tratamiento(s) fundados en interés legítimo.",
                      fte, {"tratamientos_interes_legitimo": len(coincidencias)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "Ningún tratamiento registrado se fundamenta en interés legítimo.",
                  fte, {"tratamientos_interes_legitimo": 0}, [])


# ¤adpa
def evaluar_ap05_datos_sensibles(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-05", "Categorías especiales", "N01 (LOPDP Arts. 25 y 26)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si se tratan categorías especiales o datos sensibles.", fte, {}, ["actividades_rat"])
    sensibles = [a for a in hechos.actividades_rat if bool(a.get("datos_sensibles"))]
    if sensibles:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(sensibles)} tratamiento(s) de categorías especiales de datos.",
                      fte, {"tratamientos_datos_sensibles": len(sensibles)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "No se registraron datos sensibles en las actividades de tratamiento.",
                  fte, {"tratamientos_datos_sensibles": 0}, [])


# ¤adpa
def evaluar_ap06_alto_riesgo_eipd(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-06", "Alto riesgo o supuesto art. 42", "N01;N03 (LOPDP Art. 42, SPDP-SPD-2025-0003-R)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce el nivel de riesgo de los tratamientos.", fte, {}, ["actividades_rat"])
    requieren = [
        a for a in hechos.actividades_rat
        if bool(a.get("requiere_eipd")) or str(a.get("nivel_riesgo", "")).lower() == "alto"
    ]
    if requieren:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(requieren)} tratamiento(s) de alto riesgo que requieren EIPD.",
                      fte, {"tratamientos_alto_riesgo": len(requieren)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "Ningún tratamiento registrado requiere EIPD ni presenta nivel de riesgo alto.",
                  fte, {"tratamientos_alto_riesgo": 0}, [])


# ¤adpa
def evaluar_ap07_biometria(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-07", "Uso de biometría", "N11 (Res. SPDP-SPD-2026-0039-R Arts. 13 a 16)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si los tratamientos procesan datos biométricos.", fte, {}, ["actividades_rat"])
    palabras = ("biometric", "biométric", "huella", "facial", "iris", "voz", "retina")
    biometricos = []
    for a in hechos.actividades_rat:
        cat = " ".join(str(c).lower() for c in a.get("categorias_datos", []))
        nom_a = str(a.get("nombre", "")).lower()
        fin = str(a.get("finalidad", "")).lower()
        med = str(a.get("medio_soporte", "")).lower()
        if any(p in f"{cat} {nom_a} {fin} {med}" for p in palabras):
            biometricos.append(a)
    if biometricos:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(biometricos)} tratamiento(s) con captura de datos biométricos.",
                      fte, {"tratamientos_biometricos": len(biometricos)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "No se identificaron tratamientos que utilicen tecnologías biométricas.",
                  fte, {"tratamientos_biometricos": 0}, [])


# ¤adpa
def evaluar_ap08_encargados(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-08", "Proveedor trata por cuenta de otro", "N01;N04 (LOPDP Art. 48, SPDP-SPD-2025-0006-R)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si existen encargados de tratamiento involucrados.", fte, {}, ["actividades_rat"])
    con_enc = [a for a in hechos.actividades_rat if len(a.get("encargados", [])) > 0]
    if con_enc:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(con_enc)} tratamiento(s) con intervención de encargados.",
                      fte, {"tratamientos_con_encargados": len(con_enc)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "No se registraron encargados externos en los tratamientos.",
                  fte, {"tratamientos_con_encargados": 0}, [])


# ¤adpa
def evaluar_ap09_transferencias(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-09", "Flujo o acceso internacional", "N01;N08 (LOPDP Arts. 49 y 50, SPDP-SPD-2026-0004-R)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si existen transferencias internacionales de datos.", fte, {}, ["actividades_rat"])
    internacionales = [
        a for a in hechos.actividades_rat
        if bool(a.get("transferencia_internacional")) or bool(str(a.get("pais_transferencia", "")).strip())
    ]
    if internacionales:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(internacionales)} tratamiento(s) con transferencias internacionales.",
                      fte, {"transferencias_internacionales": len(internacionales)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "No se registraron transferencias internacionales en las actividades.",
                  fte, {"transferencias_internacionales": 0}, [])


# ¤adpa
def evaluar_ap10_sector_publico(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-10", "Sector público o actividad art. 10 N05", "N01;N05 (LOPDP Art. 47, SPDP-SPD-2025-0028-R Arts. 4 y 10)"
    if not hechos.sector:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si la entidad pertenece al sector público o privado.",
                      fte, {"sector": hechos.sector}, ["sector_organizacion"])
    sec = hechos.sector.strip().lower()
    if sec in ("publico", "público", "estatal"):
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      "Entidad del sector público con deber de nombramiento DPD.",
                      fte, {"sector": hechos.sector}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  f"Organización del sector privado ('{hechos.sector}').",
                  fte, {"sector": hechos.sector}, [])


# ¤adpa
def evaluar_ap11_consentimiento(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-11", "Base válida es consentimiento", "N01 (LOPDP Arts. 7 y 8)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconocen las bases legales de tratamiento.", fte, {}, ["actividades_rat"])
    con_c = [
        a for a in hechos.actividades_rat
        if str(a.get("base_legal", "")).upper() in ("CONSENTIMIENTO", "BASELEGITIMACION.CONSENTIMIENTO")
    ]
    if con_c:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(con_c)} tratamiento(s) basados en consentimiento.",
                      fte, {"tratamientos_consentimiento": len(con_c)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "Ningún tratamiento registrado se basa en el consentimiento del titular.",
                  fte, {"tratamientos_consentimiento": 0}, [])


# ¤adpa
def evaluar_ap13_ia(hechos: HechosOrganizacion) -> ReglaEvaluada:
    rid, nom, fte = "AP-13", "IA con datos personales", "N10 (Res. SPDP-SPD-2026-0009-R y reforma 0037-R)"
    if not hechos.rat_cargado or hechos.actividades_rat is None or len(hechos.actividades_rat) == 0:
        return _regla(rid, nom, ResultadoAplicabilidad.INFORMACION_INSUFICIENTE,
                      "Se desconoce si existen tratamientos con decisiones automatizadas o IA.", fte, {}, ["actividades_rat"])
    ia = [a for a in hechos.actividades_rat if bool(a.get("decisiones_automatizadas"))]
    if ia:
        return _regla(rid, nom, ResultadoAplicabilidad.APLICA,
                      f"Se identificaron {len(ia)} tratamiento(s) con decisiones automatizadas/IA.",
                      fte, {"tratamientos_ia": len(ia)}, [])
    return _regla(rid, nom, ResultadoAplicabilidad.NO_APLICA,
                  "No se identificaron decisiones automatizadas ni sistemas de IA en los tratamientos.",
                  fte, {"tratamientos_ia": 0}, [])
