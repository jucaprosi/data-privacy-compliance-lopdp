# ¤¤planes-implementacion-privacidad
"""Catálogo de implementación: propuestas operativas, separadas del fundamento legal."""
from features.regulacion_rag.domain.corpus import fundamento

# IDs estables del banco SGPDP; el texto recibido del cliente no crea obligaciones.
# Título, acción concreta, evidencia específica, referencias verificadas.
CONTROLES = {
    1: ("Política de protección de datos", "Redactar alcance, principios, reglas por proceso y responsabilidades; obtener aprobación de gerencia y difundir la versión vigente.", "Política aprobada y registro de difusión", ("L47", "L10")),
    2: ("Roles y responsabilidades", "Designar por escrito dueños de proceso y quien aprueba recursos; definir escalamiento y suplencias.", "Matriz de responsabilidades y designaciones", ("L47",)),
    3: ("Aplicabilidad del DPD", "Documentar el análisis de los supuestos legales de designación y de la normativa SPDP aplicable; si corresponde, designar una persona idónea.", "Informe de aplicabilidad y nombramiento cuando proceda", ("L48", "L49")),
    4: ("Independencia del DPD", "Asignar recursos y acceso a dirección, revisar incompatibilidades y separar ejecución de controles de la supervisión del DPD.", "Carta de independencia, recursos y evaluación de conflictos", ("L50", "R48")),
    5: ("Mapa de obligaciones", "Relacionar cada tratamiento con sus obligaciones y fuentes vigentes, asignando un dueño y una fecha de revisión.", "Matriz de obligaciones con fuentes y responsables", ("L47",)),
    6: ("Gobierno del SGPDP", "Proponer una instancia de coordinación acorde al tamaño; definir integrantes, decisiones y seguimiento. El comité es una medida organizativa propuesta, no una obligación universal.", "Acta de coordinación y compromisos aprobados", ("L47", "L10")),
    7: ("Gestión documental", "Centralizar políticas y registros, identificar versión aprobada y limitar edición por rol.", "Índice documental, versiones y permisos", ("L47", "L10")),
    8: ("Indicadores de cumplimiento", "Definir métricas de solicitudes, incidentes y acciones; asignar metas y presentar resultados a dirección.", "Tablero y acta de revisión con decisiones", ("R36", "L47")),
    9: ("Inventario de tratamientos", "Entrevistar a cada dueño de proceso y listar datos, titulares, finalidad, sistemas, destinatarios y conservación; conciliar el inventario con procesos y activos reales.", "Inventario validado por cada dueño de proceso", ("L47", "R38", "R39")),
    10: ("Registro de actividades de tratamiento", "Evaluar la obligación del RAT conforme a los arts. 38 y 39 del Reglamento; completar cada actividad con los campos exigidos y validar con su dueño.", "RAT versionado y evaluación de aplicabilidad", ("R38", "R39", "L47")),
    11: ("Finalidades declaradas", "Definir finalidades específicas por tratamiento y comprobar que formularios, avisos y usos reales coincidan; evaluar usos secundarios antes de habilitarlos.", "Matriz de finalidades y revisión de usos", ("L10", "L7")),
    12: ("Bases de legitimación", "Seleccionar y justificar una base del art. 7 por finalidad; conservar el respaldo de contrato, obligación legal u otra base aplicable.", "Matriz de bases y sus documentos de respaldo", ("L7", "L8")),
    13: ("Datos sensibles", "Clasificar categorías especiales por tratamiento, justificar la excepción habilitante y restringir el acceso a quienes lo necesitan.", "Clasificación, excepción del art. 26 y matriz de acceso", ("L25", "L26", "L37")),
    14: ("Plazos de conservación", "Definir plazos por finalidad y obligación sectorial, evento de inicio y destino final; programar revisión y depuración.", "Tabla de retención y registro de depuración", ("L10", "R9")),
    15: ("Minimización y calidad", "Justificar cada campo solicitado, retirar los innecesarios y habilitar corrección de datos inexactos.", "Revisión de formularios y prueba de actualización", ("L10", "L14")),
    16: ("Actualización del RAT", "Añadir la revisión del RAT a altas y cambios de sistemas, proveedores y finalidades; guardar aprobación y versiones.", "Historial de cambios del RAT", ("R38", "R39", "L47")),
    17: ("Aviso de privacidad", "Preparar el aviso con todos los contenidos del art. 12 y contrastarlo con los tratamientos reales antes de publicarlo.", "Aviso versionado y lista de comprobación del art. 12", ("L12",)),
    18: ("Información digital", "Situar el aviso donde se recogen datos en web, aplicaciones y formularios, y probar acceso desde cada canal.", "Capturas sin datos personales y prueba de enlaces", ("L12", "L10")),
    19: ("Información presencial", "Entregar o mostrar el aviso antes de recoger datos en oficinas, formularios y atención telefónica cuando corresponda.", "Avisos y procedimiento de atención aprobado", ("L12",)),
    20: ("Lenguaje claro", "Reescribir el aviso con frases comprensibles y formatos accesibles; probar su comprensión con una muestra de usuarios.", "Versión revisada y prueba de comprensión", ("L12", "L10")),
    21: ("Consentimiento", "Separar las finalidades que requieren consentimiento, solicitar una acción afirmativa y guardar fecha, finalidad y versión del aviso aceptado.", "Registro de consentimiento y prueba del formulario", ("L8", "L7")),
    22: ("Revocatoria", "Habilitar un canal gratuito y sencillo para retirar el consentimiento y propagar la retirada a los sistemas que dependen de esa base.", "Prueba de revocatoria y registro de propagación", ("L8",)),
    23: ("Atención de derechos", "Documentar recepción, identidad, clasificación del derecho, localización, respuesta, ejecución y cierre con responsables.", "Procedimiento y expediente de prueba", ("L13", "R12", "R15")),
    24: ("Canales de derechos", "Habilitar un canal accesible y seguro, publicar su ubicación y asignar personal para atender también solicitudes físicas.", "Canales publicados y prueba de recepción", ("R12", "L12")),
    25: ("Registro de solicitudes", "Registrar ingreso, derecho, acreditación, hitos, decisiones y respuesta de cada solicitud con acceso restringido.", "Bitácora de solicitudes y seguimiento", ("R15", "L37")),
    26: ("Plazos de derechos", "Configurar vencimientos según el derecho concreto; para acceso, rectificación, eliminación y oposición usar los plazos de sus artículos y comprobar alertas.", "Matriz de plazos por derecho y pruebas de alertas", ("L13", "L14", "L15", "L16")),
    27: ("Respuesta motivada", "Crear respuestas que expliquen la decisión, las actuaciones y la causa legal concreta si procede una excepción; someter negativas a revisión jurídica.", "Modelo de respuesta y expediente de validación", ("L18", "R16")),
    28: ("Verificación de identidad", "Definir acreditación proporcional de titularidad y representación antes de entregar datos; probar casos válidos e intentos de suplantación.", "Procedimiento de acreditación y pruebas de suplantación", ("R12", "R13", "L37")),
    29: ("Representación de terceros", "Comprobar el alcance y validez de la representación, registrar la comprobación y limitar la entrega al derecho solicitado.", "Expediente de representación validado", ("R13", "L18")),
    30: ("Reclamos ante la autoridad", "Incluir la vía de reclamo ante la autoridad en el procedimiento y conservar respuesta, pruebas y responsables de atender requerimientos.", "Procedimiento de reclamos y expediente trazable", ("R16", "L47")),
    31: ("Portabilidad", "Determinar procedencia y datos comprendidos, generar exportación interoperable y probar entrega segura al destinatario autorizado.", "Archivo de prueba sin datos reales y acta de entrega", ("L17",)),
    32: ("Simulación de derechos", "Ejecutar un caso completo con datos ficticios, medir tiempos y corregir fallos de identificación, búsqueda y entrega.", "Informe del simulacro y correcciones verificadas", ("L47", "R12")),
    33: ("Alta de titulares", "Revisar los formularios de alta, documentar finalidad y base y entregar información antes de la recogida.", "Formulario revisado y expediente de alta de prueba", ("L7", "L12", "L10")),
    34: ("Actualización de datos", "Asignar la fuente maestra, habilitar corrección y propagar cambios a sistemas destinatarios autorizados.", "Procedimiento y trazabilidad de actualización", ("L14", "L10")),
    35: ("Canales digitales", "Mapear datos que recogen formularios, aplicaciones y rastreadores; justificar su base y minimizar los campos.", "Inventario de capturas digitales y validación del aviso", ("L7", "L12", "L39")),
    36: ("Marketing", "Justificar la base de cada campaña y habilitar oposición; excluir de nuevos envíos a quienes se oponen y registrar la ejecución.", "Registro de base, lista de exclusión y prueba de baja", ("L16", "L7", "L8")),
    37: ("Talento humano", "Separar datos laborales y de salud, justificar sus usos y restringir expedientes médicos a personal autorizado.", "Matriz de tratamientos laborales y permisos", ("L7", "L25", "L26", "L37")),
    38: ("Videovigilancia", "Evaluar necesidad y proporcionalidad por cámara, informar a titulares, limitar accesos y definir conservación justificada.", "Mapa de cámaras, aviso y reglas de acceso y retención", ("L10", "L12", "L37")),
    39: ("Eliminación y bloqueo", "Identificar datos cuyo plazo venció, revisar causas de conservación y ejecutar el destino legalmente aplicable con registro verificable.", "Acta de depuración y excepciones justificadas", ("L15", "R9", "L10")),
    40: ("Anonimización y seudonimización", "Elegir técnica según finalidad y riesgo; separar las claves de seudonimización y probar riesgo de reidentificación antes de compartir resultados.", "Diseño de transformación y prueba de reidentificación", ("L37", "R9", "L10")),
    41: ("Inventario de proveedores", "Identificar qué proveedor accede a qué datos, en qué rol, país y servicio, y localizar su contrato.", "Inventario de proveedores y contratos asociados", ("L34", "L47")),
    42: ("Debida diligencia", "Evaluar garantías del proveedor antes de contratar, pedir pruebas proporcionadas y registrar brechas y condiciones de aceptación.", "Evaluación de proveedor con evidencias y decisión", ("L47", "L37")),
    43: ("Contrato de encargado", "Regular instrucciones, finalidades permitidas, confidencialidad, seguridad y destino de datos al terminar; obtener aprobación y firma.", "Contrato o adenda de tratamiento firmada", ("L34", "L47")),
    44: ("Subencargados", "Listar subcontratistas y verificar autorización contractual expresa o escrita antes de habilitar acceso; trasladar obligaciones pertinentes.", "Registro de subencargados y autorizaciones", ("R45", "L34")),
    45: ("Nube y ubicación", "Inventariar regiones de almacenamiento y acceso remoto, destinatarios y subencargados; evaluar contratos y mecanismo internacional antes del uso.", "Mapa de regiones y expediente contractual", ("L55", "L34")),
    46: ("Transferencias internacionales", "Documentar destino, destinatario y finalidad; verificar adecuación o garantías y requisitos de la normativa SPDP vigente antes de transferir.", "Expediente de transferencia y mecanismo acreditado", ("L55", "L56", "L57")),
    47: ("Soporte externo", "Aprobar accesos por tarea y tiempo, autenticar al técnico, registrar su actividad y revocar permisos al finalizar.", "Autorizaciones de soporte, registros y prueba de revocación", ("L34", "L37")),
    48: ("Salida del proveedor", "Planificar devolución o eliminación según contrato, cerrar accesos y obtener evidencia verificable del destino de las copias.", "Acta de salida, devolución o eliminación y bajas de acceso", ("L34",)),
    49: ("Identidades y accesos", "Definir permisos por función, aprobar altas y bajas y revisar privilegios; probar que un usuario sin permiso no accede.", "Matriz de accesos y prueba de denegación", ("L37", "L41")),
    50: ("Autenticación multifactor", "Priorizar accesos remotos y privilegiados según el riesgo; configurar MFA, recuperación segura y probar acceso y revocación.", "Cobertura de MFA y prueba de autenticación", ("L37", "L41")),
    51: ("Cifrado", "Identificar flujos y repositorios que requieren cifrado según el riesgo, gestionar claves separadamente y verificar configuración.", "Inventario de cifrado y prueba de protección de claves", ("L37", "L41")),
    52: ("Registros y monitoreo", "Definir eventos de acceso y cambio necesarios, restringir registros y probar una alerta sin incluir datos excesivos.", "Política de registro y prueba de alerta", ("L37", "L10")),
    53: ("Respaldos", "Definir cobertura y recuperación, proteger copias y ejecutar restauración en entorno aislado con comprobación de integridad.", "Inventario de copias e informe de restauración", ("L37", "L41")),
    54: ("Vulnerabilidades", "Inventariar activos, priorizar hallazgos por riesgo, desplegar parches y verificar correcciones.", "Registro de vulnerabilidades y validación posterior", ("L37", "L41")),
    55: ("Segregación de ambientes", "Separar producción y pruebas, restringir permisos y sustituir datos reales por datos sintéticos cuando sea viable.", "Diagrama de entornos y pruebas de aislamiento", ("L37", "L39")),
    56: ("Seguridad física", "Identificar archivos y equipos con datos, limitar accesos y comprobar custodia y destrucción segura de soportes.", "Control de acceso físico y actas de disposición", ("L37", "L41")),
    57: ("Gestión de incidentes", "Documentar detección, escalamiento, contención, evaluación de riesgos, notificación y recuperación; asignar suplentes.", "Procedimiento de incidentes y cadena de escalamiento", ("L43", "L46", "L37")),
    58: ("Bitácora de incidentes", "Registrar cuándo se conoce el incidente, hechos, datos afectados, riesgo y decisiones; preservar evidencia y controlar acceso.", "Bitácora con cronología y decisiones", ("L43", "L46", "L47")),
    59: ("Severidad de incidentes", "Clasificar por impacto en derechos y libertades, tipo y volumen de datos y personas afectadas; separar riesgo técnico del riesgo al titular.", "Matriz de severidad y caso evaluado", ("L43", "L46", "L40")),
    60: ("Notificación a autoridades", "Preparar un flujo que evalúe el art. 43 y notifique tan pronto sea posible dentro de su término de cinco días; el encargado avisa al responsable en dos días.", "Decisión documentada y prueba del circuito de notificación", ("L43",)),
    61: ("Contención y evidencia", "Definir aislamiento, preservación de registros y acceso a evidencia; probar que la contención conserva integridad y permite recuperación.", "Guía de contención y registro de custodia", ("L37", "L41")),
    62: ("Comunicación a afectados", "Evaluar el riesgo al titular y preparar comunicación sin dilación dentro del término de tres días desde conocer el riesgo, conforme al art. 46 y sus excepciones.", "Evaluación y comunicación de prueba a titulares", ("L46",)),
    63: ("Simulacro de incidentes", "Ejecutar un escenario con datos ficticios y medir detección, escalamiento y decisiones de notificación.", "Informe del simulacro con tiempos y responsables", ("L47", "L43")),
    64: ("Lecciones aprendidas", "Identificar causa del incidente, asignar acciones y comprobar la eficacia de la corrección antes de su cierre.", "Informe causal y pruebas de corrección", ("L47", "L41")),
    65: ("Metodología de riesgos", "Definir escenarios sobre derechos de titulares, probabilidad e impacto, medidas existentes y riesgo residual por tratamiento.", "Metodología aprobada y matriz por tratamiento", ("L40", "L41")),
    66: ("Aplicabilidad de EIPD", "Evaluar cada tratamiento frente a alto riesgo y supuestos del art. 42 antes de iniciarlo; justificar si requiere EIPD.", "Informe de necesidad de EIPD por tratamiento", ("L42",)),
    67: ("Ejecución de EIPD", "Describir operaciones, necesidad, proporcionalidad, riesgos y medidas antes del tratamiento; validar decisiones y revisar obligaciones reglamentarias de presentación.", "EIPD aprobada y plan de mitigación", ("L42", "L40", "L41")),
    68: ("Interés legítimo", "Documentar finalidad legítima, necesidad, expectativas del titular e impacto en derechos; decidir si prevalecen estos y aplicar salvaguardas.", "Evaluación de ponderación y decisión de base legal", ("L7", "L9")),
    69: ("Privacidad desde el diseño", "Añadir revisión de finalidad, base, minimización, derechos y seguridad antes de aprobar nuevos proyectos o cambios.", "Lista de revisión de diseño y aprobación del proyecto", ("L39",)),
    70: ("Privacidad por defecto", "Configurar captura, conservación y accesos al mínimo necesario; probar las opciones de una cuenta nueva sin cambios manuales.", "Configuración base y prueba de cuenta nueva", ("L39", "L10")),
    71: ("Riesgo residual", "Valorar el riesgo que queda tras los controles y asignar medidas adicionales, responsables y decisión documentada del responsable.", "Matriz residual y decisiones justificadas", ("L41", "L47")),
    72: ("Decisiones automatizadas", "Inventariar decisiones y perfiles, evaluar garantías del art. 20 y necesidad de EIPD; habilitar explicación, observaciones e impugnación.", "Inventario de decisiones y prueba de canal de impugnación", ("L20", "L42")),
    73: ("Capacitación", "Preparar formación por rol sobre usos permitidos, derechos, seguridad e incidentes y registrar participación.", "Plan por rol y registro de formación", ("L47", "L37")),
    74: ("Concienciación", "Diseñar mensajes y ejercicios sobre riesgos observados, definir audiencia y medir su recepción.", "Campaña, participación y resultados", ("L47", "R36")),
    75: ("Eficacia de formación", "Comparar conocimientos y errores antes y después de la formación, y reforzar a los equipos que lo necesitan.", "Resultados de evaluación y acciones de refuerzo", ("R36", "L47")),
    76: ("Programa de auditoría", "Planificar revisiones proporcionales al riesgo, con alcance, criterios y revisores que no evalúen su propio trabajo.", "Programa de auditoría aprobado", ("L47",)),
    77: ("Auditoría del SGPDP", "Seleccionar muestras de tratamientos y contrastar prácticas contra normas, procedimientos y evidencias; documentar hallazgos.", "Informe de revisión y muestras verificadas", ("L47",)),
    78: ("Gestión de hallazgos", "Registrar cada hallazgo con causa, riesgo, responsable, acción, fecha y evidencia necesaria para cerrar.", "Registro de hallazgos y plan de acciones", ("L47", "L41")),
    79: ("Acciones correctivas", "Revisar compromisos vencidos, comprobar evidencia de ejecución y repetir el control que originó el hallazgo.", "Prueba de eficacia y validación de cierre", ("L47",)),
    80: ("Revisión y mejora continua", "Presentar indicadores, incidentes, derechos y riesgos a dirección; aprobar recursos y cambios y comprobar su ejecución.", "Acta de revisión y seguimiento de decisiones", ("L47", "R36")),
}

DIMENSIONES = {
    "D01": (1, 8, "Gerencia y responsables de proceso", "Confirmar aprobación y difusión con las áreas afectadas."),
    "D02": (9, 16, "Dueños de proceso y asesoría jurídica", "Validar cobertura con los procesos, sistemas y flujos reales."),
    "D03": (17, 22, "Responsables de canales y asesoría jurídica", "Probar la experiencia del titular en los canales afectados."),
    "D04": (23, 32, "Equipo de atención de derechos y dueños de sistemas", "Ejecutar una solicitud ficticia de extremo a extremo y medir su atención."),
    "D05": (33, 40, "Dueño del proceso y equipo de sistemas", "Comprobar el tratamiento desde la recogida hasta su destino final."),
    "D06": (41, 48, "Compras, asesoría jurídica y dueño del servicio", "Contrastar contrato, operación del proveedor y evidencias recibidas."),
    "D07": (49, 56, "Seguridad de la información y equipo de TI", "Probar efectividad del control y documentar el riesgo residual."),
    "D08": (57, 64, "Equipo de respuesta a incidentes y responsable del tratamiento", "Ejecutar un escenario de prueba y registrar tiempos y decisiones."),
    "D09": (65, 72, "Dueño del tratamiento, riesgos y asesoría jurídica", "Validar medidas antes del tratamiento y registrar la decisión del responsable."),
    "D10": (73, 80, "Talento humano, calidad y dirección", "Comprobar eficacia mediante una muestra y acordar mejoras con dirección."),
}


# ¤resolver-guia-implementacion
def obtener_guia_brecha(pregunta_id: int, control: str = "", dimension_id: str = "") -> dict | None:
    """Resuelve únicamente IDs del catálogo; no inventa fundamento para controles desconocidos."""
    registro = CONTROLES.get(pregunta_id)
    if registro is None:
        return None
    dimension = next(d for d, valores in DIMENSIONES.items() if valores[0] <= pregunta_id <= valores[1])
    titulo, accion, evidencia, referencias = registro
    _, _, responsable, validacion = DIMENSIONES[dimension]
    return {
        "fundamento": [fundamento(clave) for clave in referencias],
        "pasos": [
            accion,
            "Asignar responsable de ejecución y fecha objetivo, identificar sistemas y personas afectadas y aprobar recursos.",
            validacion,
            "Adjuntar evidencia sin datos personales innecesarios y someter el cierre a revisión humana; actualizar el assessment.",
        ],
        "responsable_sugerido": responsable,
        "evidencias": [evidencia, "Resultado de verificación y aprobación del dueño del proceso"],
        "criterio_cierre": f"Para {titulo}: evidencia vigente aprobada y una ejecución o prueba satisfactoria del control; registrar excepciones y riesgo residual. La tarea completada no acredita por sí sola cumplimiento legal.",
        "seguimiento": "Revisar al cambiar el tratamiento, proveedor o normativa; acordar una periodicidad proporcional al riesgo. El asistente ayuda a preparar y revisar, y el DPD conserva su función independiente cuando corresponda.",
        "tipo_guia": "Recomendaciones operativas para implementar las obligaciones citadas; no son texto de la ley.",
        "dimension_id": dimension,
        "control": titulo,
    }
