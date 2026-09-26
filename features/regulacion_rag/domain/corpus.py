# ¤¤corpus-normativo-versionado
"""Corpus cerrado: resúmenes editoriales trazables, no transcripciones legales."""
from features.regulacion_rag.domain.models import TipoNorma, UnidadNormativa

CORPUS_VERSION = "lopdp-rg-2026-09-20.1"
FECHA_REVISION = "2026-09-20"
LEY_URL = "https://www.gob.ec/sites/default/files/regulations/2025-01/01%20Ley%20Org%C3%A1nica%20de%20Protecci%C3%B3n%20de%20Datos%20Personales.pdf"
REGLAMENTO_URL = "https://www.gob.ec/sites/default/files/regulations/2025-01/02%20Reglamento%20General%20a%20la%20Ley%20Org%C3%A1nica%20de%20Protecci%C3%B3n%20de%20Datos%20Personales_0.pdf"

# Clave, artículo, título, resumen editorial y términos de recuperación.
LEY = [
    ("L7", "7", "Tratamiento legítimo", "Cada tratamiento debe apoyarse en una condición de licitud aplicable: consentimiento, obligación legal, orden judicial, misión de interés público, contrato, intereses vitales, fuente pública o interés legítimo, con los requisitos propios de cada caso.", ("base de legitimacion", "bases de legitimacion", "licitud", "contrato", "obligacion legal")),
    ("L8", "8", "Consentimiento", "Cuando se use esta base, la autorización debe ser libre, específica, informada e inequívoca. Debe comprender las finalidades correspondientes y poder revocarse mediante un procedimiento sencillo, eficaz y gratuito, sin efectos retroactivos.", ("consentimiento", "revocacion", "revocatoria", "autorizacion")),
    ("L9", "9", "Interés legítimo", "El interés legítimo exige necesidad y transparencia y no puede prevalecer sobre los derechos del titular. La autoridad puede requerir un informe de riesgo sobre su impacto en las expectativas legítimas y derechos fundamentales.", ("interes legitimo", "lia", "ponderacion")),
    ("L10", "10", "Principios", "Los tratamientos deben respetar, entre otros, finalidad, minimización, proporcionalidad, confidencialidad, calidad, conservación, seguridad y responsabilidad proactiva. El responsable debe poder demostrar las medidas implantadas. Este artículo no impone una regla específica de citas para asistentes de IA.", ("minimizacion", "conservacion", "finalidad", "calidad", "responsabilidad proactiva", "principios")),
    ("L12", "12", "Derecho a la información", "Debe informarse al titular de forma clara sobre el tratamiento: finalidades, base legal, conservación, responsable, derechos, transferencias y demás contenidos exigidos por el artículo. La información debe proporcionarse en los momentos y condiciones previstos para la obtención de datos.", ("aviso de privacidad", "transparencia", "informacion al titular", "lenguaje claro")),
    ("L13", "13", "Derecho de acceso", "El titular puede conocer y obtener gratuitamente sus datos y la información del tratamiento sin justificar su solicitud. El responsable debe facilitar métodos razonables y atender el acceso dentro de quince días.", ("derecho de acceso", "solicitud de acceso")),
    ("L14", "14", "Rectificación y actualización", "El titular puede obtener la corrección y actualización de datos inexactos o incompletos. La solicitud debe atenderse en quince días y la corrección debe comunicarse a los destinatarios cuando corresponda.", ("rectificacion", "actualizacion de datos")),
    ("L15", "15", "Eliminación", "El titular puede pedir eliminación en los supuestos legales, incluidos datos innecesarios, finalidad cumplida o conservación vencida. La eliminación debe ser segura y gratuita, en quince días desde la solicitud, considerando las excepciones legales.", ("eliminacion", "supresion", "borrado")),
    ("L16", "16", "Oposición", "La oposición procede bajo las condiciones legales. Para mercadotecnia directa comprende también los perfiles y obliga a dejar de tratar los datos para ese fin. La solicitud debe atenderse en quince días.", ("oposicion", "marketing", "mercadotecnia", "comunicaciones comerciales")),
    ("L17", "17", "Portabilidad", "El titular puede recibir sus datos en formato estructurado e interoperable o transmitirlos a otro responsable cuando se cumplan las condiciones del artículo. Existen límites, entre ellos la información inferida o generada mediante análisis.", ("portabilidad", "exportacion")),
    ("L18", "18", "Excepciones al ejercicio de derechos", "Las excepciones requieren una causa legal concreta, como falta de acreditación de titularidad o representación, obligaciones legales o contractuales y defensa de reclamaciones. Deben analizarse para el derecho y caso específicos.", ("excepciones", "representacion", "respuesta motivada")),
    ("L19", "19", "Suspensión del tratamiento", "La suspensión puede proceder ante impugnación de exactitud y otras situaciones legales. Debe limitarse el uso mientras se resuelve el supuesto correspondiente y conservarse la trazabilidad de la decisión.", ("suspension", "bloqueo")),
    ("L20", "20", "Decisiones automatizadas", "El titular dispone de garantías frente a decisiones basadas única o parcialmente en valoraciones automatizadas con efectos jurídicos o afectación de derechos. Puede solicitar explicación y criterios, presentar observaciones e impugnar, sin perjuicio de las excepciones del artículo.", ("decisiones automatizadas", "perfilado", "inteligencia artificial", "algoritmos")),
    ("L25", "25", "Categorías especiales", "Son categorías especiales los datos sensibles, de niños y adolescentes, de salud y de personas con discapacidad y sus sustitutos relativos a la discapacidad. Su clasificación exige considerar las reglas específicas aplicables.", ("categorias especiales", "datos sensibles", "salud", "menores")),
    ("L26", "26", "Tratamiento de datos sensibles", "El tratamiento de datos sensibles está prohibido salvo que concurra una excepción del artículo. Debe documentarse la excepción aplicable, como el consentimiento explícito en los casos legalmente permitidos, además de las restantes garantías.", ("datos sensibles", "biometricos", "biometria")),
    ("L34", "34", "Acceso del encargado", "El servicio que implica acceso del encargado debe regularse por contrato con instrucciones del responsable, límites de finalidad y condiciones sobre devolución o destrucción al terminar. El encargado responde por incumplir esas condiciones.", ("encargado", "proveedores", "contratos", "terceros")),
    ("L37", "37", "Seguridad de datos personales", "Las medidas de seguridad deben considerar categorías y volumen de datos, estado de la técnica, costes, contexto, fines y riesgos. Debe verificarse y evaluarse continuamente su eficacia. Las técnicas concretas se seleccionan conforme al riesgo.", ("seguridad", "cifrado", "autenticacion", "multifactor", "accesos", "respaldos", "vulnerabilidades")),
    ("L39", "39", "Protección desde el diseño y por defecto", "La protección debe incorporarse desde las primeras fases del proyecto mediante medidas técnicas y organizativas. Por defecto deben tratarse únicamente los datos necesarios para cada finalidad.", ("desde el diseno", "por defecto", "privacy by design", "proyectos")),
    ("L40", "40", "Análisis de riesgos", "La metodología de riesgos debe considerar las particularidades del tratamiento, de las partes y las categorías y volumen de datos personales.", ("riesgos", "amenazas", "metodologia")),
    ("L41", "41", "Medidas según el riesgo", "Las medidas se determinan a partir del análisis de riesgos, naturaleza de los datos, partes y antecedentes de incidentes. Deben evaluarse y mantenerse para prevenir y reducir amenazas y vulnerabilidades.", ("riesgo residual", "mitigacion", "medidas de seguridad")),
    ("L42", "42", "Evaluación de impacto", "La EIPD debe realizarse antes del tratamiento cuando sea probable un alto riesgo, la autoridad la requiera o concurra un supuesto obligatorio, como ciertos perfiles automatizados o tratamientos a gran escala de categorías especiales.", ("eipd", "evaluacion de impacto", "alto riesgo", "gran escala")),
    ("L43", "43", "Notificación de vulneraciones", "El responsable notifica a la autoridad de protección de datos y ARCOTEL tan pronto sea posible, a más tardar en el término de cinco días desde que conoce la vulneración, salvo la excepción de riesgo improbable. El encargado avisa al responsable en un máximo de dos días.", ("incidentes", "vulneracion", "notificacion a la autoridad", "brecha de seguridad")),
    ("L46", "46", "Notificación al titular", "Cuando la vulneración conlleve riesgo para derechos y libertades, se notifica al titular sin dilación, dentro del término de tres días desde conocer el riesgo. Deben analizarse las excepciones del artículo y la intervención de la autoridad que este exige.", ("titulares afectados", "notificacion al titular", "comunicacion de incidentes")),
    ("L47", "47", "Obligaciones de responsables y encargados", "El responsable debe implantar y demostrar medidas apropiadas, políticas, gestión de riesgos, evaluación periódica, privacidad desde el diseño y garantías de los encargados. El encargado tiene las mismas obligaciones en cuanto le sean aplicables.", ("gobierno", "politica", "responsable", "capacitacion", "auditoria", "mejora continua", "evidencia")),
    ("L48", "48", "Designación del delegado", "Debe designarse DPD en los casos previstos legalmente, incluidos sector público, control permanente y sistematizado y categorías especiales a gran escala. La aplicación exige revisar el reglamento y condiciones que establezca la autoridad.", ("designacion", "delegado", "dpd", "dpo")),
    ("L49", "49", "Funciones del delegado", "El DPD asesora, supervisa el cumplimiento y la gestión de riesgos, y coopera con la autoridad. La responsabilidad de implementar las medidas permanece en el responsable y encargado; el asistente es apoyo y no constituye una designación de DPD.", ("funciones", "delegado", "dpd", "dpo", "asesoria")),
    ("L50", "50", "Garantías del delegado", "El responsable y encargado deben facilitar recursos, participación oportuna y relación directa con la máxima dirección, respetando el desempeño del DPD. Otras funciones no deben generar conflicto con sus responsabilidades.", ("independencia", "conflictos de interes", "recursos del dpd")),
    ("L55", "55", "Transferencias internacionales", "Una transferencia internacional debe ajustarse al régimen legal y a la normativa especializada. Es necesario determinar el mecanismo aplicable antes de realizarla; usar un proveedor extranjero no acredita por sí mismo su licitud.", ("transferencias internacionales", "nube", "pais", "internacional")),
    ("L56", "56", "Nivel adecuado de protección", "Las transferencias a destinos con nivel adecuado se sujetan a la determinación de la autoridad y a los criterios legales de protección. No debe darse por existente una declaración de adecuación sin verificarla.", ("adecuacion", "transferencias internacionales")),
    ("L57", "57", "Garantías adecuadas", "Sin nivel adecuado de protección, la transferencia debe analizar las garantías adecuadas admitidas por la ley y la normativa de la autoridad, para proteger los derechos del titular.", ("garantias", "transferencias internacionales")),
]
REGLAMENTO = [
    ("R9", "9", "Eliminación, bloqueo o anonimización", "Cumplida la finalidad, debe determinarse si subsiste una causa legítima o legal de conservación; de lo contrario procede eliminación, bloqueo o anonimización. Deben existir procedimientos y revisiones periódicas.", ("anonimizacion", "bloqueo", "eliminacion")),
    ("R12", "12", "Medios para ejercer derechos", "El responsable habilita canales sencillos y seguros para recibir y atender solicitudes, incluidos medios físicos. Quien solicita debe acreditar la titularidad o representación.", ("identidad", "representacion", "canales", "derechos")),
    ("R13", "13", "Contenido de la solicitud", "La solicitud identifica al titular y el derecho, precisa lo solicitado y acompaña acreditación de identidad o representación. El tratamiento de esa acreditación debe ser proporcional y seguro.", ("identidad", "solicitud", "representacion")),
    ("R15", "15", "Registro de solicitudes", "Deben registrarse todas las solicitudes de ejercicio de derechos y el detalle de la atención prestada.", ("registro de solicitudes", "trazabilidad", "derechos")),
    ("R16", "16", "Reclamo ante la autoridad", "El titular puede reclamar ante la autoridad si considera vulnerados sus derechos por la respuesta o falta de respuesta en el plazo establecido, conforme al procedimiento aplicable.", ("reclamo", "autoridad")),
    ("R36", "36", "Prueba de medidas", "El responsable debe demostrar las medidas aplicadas y puede usar indicadores cuantitativos o cualitativos apropiados para evidenciar su eficacia.", ("indicadores", "metricas", "eficacia", "formacion")),
    ("R38", "38", "Registro de actividades de tratamiento", "El responsable con cien o más trabajadores lleva RAT con responsables, fines, categorías, destinatarios, perfiles, transferencias, bases legales, retención y medidas. Se conserva por escrito o electrónicamente y se facilita a la autoridad cuando lo solicite.", ("rat", "inventario", "registro de actividades")),
    ("R39", "39", "Extensión de la obligación de RAT", "También deben llevar RAT los responsables con menos de cien trabajadores si el tratamiento puede implicar riesgo, no es ocasional o incluye categorías especiales. El tamaño por sí solo no decide la obligación.", ("rat", "inventario", "menos de cien")),
    ("R45", "45", "Subcontratación del encargado", "La subcontratación debe constar expresamente en el contrato con el responsable o contar con su autorización escrita. El tercero asume las obligaciones pertinentes del encargado.", ("subencargados", "subcontratacion")),
    ("R48", "48", "Independencia del delegado", "El DPD es una persona natural que asesora y supervisa con independencia profesional. El responsable y encargado deben facilitar asistencia y recursos; las tareas adicionales no deben crear conflictos.", ("independencia", "delegado", "dpd", "dpo")),
]


# ¤crear-unidad-normativa
def _crear(clave, articulo, titulo, resumen, terminos, reglamento=False):
    return UnidadNormativa(
        id=clave,
        tipo=TipoNorma.REGLAMENTO_GENERAL if reglamento else TipoNorma.LEY_ORGANICA,
        emisor="Presidencia de la República" if reglamento else "Asamblea Nacional",
        numero_o_titulo="Reglamento General a la LOPDP" if reglamento else "LOPDP",
        articulo_o_seccion=f"Art. {articulo}",
        texto_oficial=resumen,
        fecha_vigencia="2023-11-13" if reglamento else "2021-05-26",
        fuente_url=REGLAMENTO_URL if reglamento else LEY_URL,
        version=CORPUS_VERSION,
        es_resumen=True,
        palabras_clave=terminos,
        titulo=titulo,
    )


CORPUS_NORMATIVO_OFICIAL = [_crear(*fila) for fila in LEY] + [
    _crear(*fila, reglamento=True) for fila in REGLAMENTO
]
POR_ID = {norma.id: norma for norma in CORPUS_NORMATIVO_OFICIAL}


# ¤proyectar-fundamento
def fundamento(clave: str) -> dict:
    norma = POR_ID[clave]
    return {
        "articulo": f"{norma.numero_o_titulo}, {norma.articulo_o_seccion}",
        "titulo": norma.titulo,
        "url": norma.fuente_url,
        "version": norma.version,
        "resumen": norma.texto_oficial,
    }
