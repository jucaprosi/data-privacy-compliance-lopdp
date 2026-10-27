# Diseño de la biblioteca documental de EVYDENTIA

> Conversión trazable del documento `data/biblioteca/kit_v1/especificacion/diseno_biblioteca.docx`. El DOCX conserva el original recibido; este Markdown integra su contenido en la gobernanza consultable del repositorio. Corte del documento fuente: 24 de octubre de 2026. Estado: diseño para revisión, no publicación.

Arquitectura catálogo y primer lote de plantillas

EVYDENTIA  |  DISENO-01  |  Corte normativo 2026-10-24

Se propone una biblioteca maestra de 50 entradas con variantes y reglas de aplicabilidad. Esta entrega incluye ocho plantillas editables para revisión y adaptación, el catálogo ampliado y la especificación funcional. Las otras entradas permanecen identificadas como planificadas o como salidas existentes por mapear; no se presentan como archivos ya producidos.

# Alcance y entregables

Se revisaron las tres hojas del catálogo original y se conservaron sus veinte códigos. El primer lote prioriza inventarios, tratamientos, legitimación, selección de EIPD, información, derechos y plan de acciones. No se dispone del código de EVYDENTIA, del cuestionario completo de 80 preguntas ni de sus identificadores; el mapeo de preguntas y la integración ejecutable quedan pendientes. El diseño no implica que la pestaña ya esté programada o publicada.

Archivos: catálogo maestro; INV-01, INV-02, RAT-01, LEG-01 y PLA-01 en Excel; EIPD-00, AVI-01 y PRO-01 en Word. Los Excel incluyen registro en blanco, ejemplo ficticio independiente e instrucciones. No se proporcionaron logotipos ni manual oficial: se utiliza identificación textual neutral sin recrear la marca.

# Diagnóstico del catálogo de origen

El catálogo es una base para centro médico mediano. Su secuencia es aprovechable, pero mezcla instrumentos de gestión, obligaciones jurídicas y estados de ejecución. Faltan el control de las plantillas maestras, reglas de selección verificables y registros operativos separados para derechos, incidentes y terceros. Las referencias a historia clínica se trasladan a la variante de salud.

| Código | Decisión | Cambio y razón |

| --- | --- | --- |

| DIA-01 | Conservar | Exportación o espejo del assessment existente; no reconstruir las 80 preguntas sin su fuente. |

| DIA-02 | Ampliar | Distinguir falta de evidencia de incumplimiento confirmado; añadir requisito y revisión humana. |

| INV-01 | Ampliar | Mantener catálogo de categorías; no recopilar datos de personas en este inventario. |

| INV-02 | Ampliar | Incluir archivo físico nube custodios y accesos desde otros países. |

| RAT-01 | Ampliar | Evaluar art. 38 RGLOPDP y regla de gran escala N09 art. 6; separar adopción voluntaria. |

| LEG-01 | Ampliar | Una base justificada por finalidad y condiciones adicionales para categorías especiales. |

| LIA-01 | Ampliar | Seguir N07 y anexo; no basta una casilla de interés legítimo ni sustituye régimen sensible. |

| RIE-01 | Ampliar | Escenarios de daño al titular y evidencia de controles; sin porcentaje automático de reducción. |

| EIPD-00 | Conservar | Agregar disparadores específicos de biometría y otros que resulten aplicables. |

| EIPD-01 | Ampliar | Separar análisis asesoría del DPD y decisiones del responsable; registrar riesgo residual. |

| SEG-01 | Ampliar | Eficacia probada por control y riesgo; no solo declaración de existencia. |

| POL-01 | Conservar | Documento interno de gobierno; no sustituye aviso al titular. |

| AVI-01 | Ampliar | Versionar por finalidad audiencia y canal con trazabilidad de comunicación. |

| CON-01 | Ampliar | Verificar rol del proveedor antes de asignar contrato de encargo; anexos de N04. |

| PRO-01 | Dividir | Procedimiento más DER-01 solicitud DER-02 registro y DER-03 respuestas; sin formulario obligatorio exclusivo. |

| PRO-02 | Dividir | Procedimiento más INC-01 expediente del evento e INC-02 auxiliar para notificar. |

| PRO-03 | Dividir | Procedimiento más RET-01 tabla y RET-02 acta; plazos sanitarios pasan a variante salud. |

| CAP-01 | Conservar | Plan y registro integrados por función con evaluación de aprendizaje. |

| PLA-01 | Ampliar | Exportación del módulo de acciones con control de cierre por evidencia y eficacia. |

| AUD-01 | Ampliar | Aclarar alcance interno; separar auditoría regulatoria y acciones correctivas AUD-02. |

# Arquitectura y entidades

Biblioteca maestra: una definición de plantilla con su versión y archivos. Variantes: bloques o anexos vinculados a un maestro, habilitados por contexto. Instancias: documentos de una organización, creados desde una versión determinada y con aprobación propia. Ejemplos e instrucciones quedan separados de la versión para uso.

| Entidad | Identidad y relaciones esenciales |

| --- | --- |

| Organización | organization_id; perfil; sector; tamaño; roles por actividad; sin compartir datos de clientes |

| Plantilla y versión | template_id; código; template_version_id; archivo; estado editorial; fuentes; variables; checksum |

| Regla de aplicabilidad | rule_id; versión; hechos requeridos; resultado; fundamento; revisor; fecha; evidencia |

| Documento del cliente | document_id; organization_id; template_version_id; versión propia; estado; aprobaciones |

| Actividad y requisito | treatment_id; requirement_id; norma y versión; responsables; relaciones con hallazgos |

| Hallazgo y acción | gap_id; action_id; prioridad; fechas; dueño; aceptación; enlaces muchos a muchos |

| Evidencia y revisión | evidence_id; versión; hash; acceso; retención; review_id; criterio; resultado |

| Evento de auditoría | actor; organization_id; entidad; acción; versión anterior y nueva; fecha; motivo |

# Estados y aprobación

Plantilla maestra: Planificada, En elaboración, Revisión jurídica, Revisión técnica, Publicada, Sustituida o Retirada. El estado Creada para revisión de este lote equivale a borrador editorial, no a Publicada. Solo versiones publicadas se ofrecen como vigentes por defecto.

Documento de cliente: Borrador, En revisión, Aprobado, Implementado, Verificado eficaz, Sustituido o Archivado. Aprobar congela la versión; una corrección crea una nueva. La revisión del DPD puede quedar registrada como opinión y discrepancias, sin convertirlo en ejecutor ni aprobador automático de la decisión empresarial.

Aplicabilidad tiene tres resultados: Aplica, No aplica, Información insuficiente. El sistema guarda por separado si hay obligación expresa, una medida demostrativa o una buena práctica. Un documento puede servir para cumplir una obligación sin que su nombre o formato concreto esté impuesto por ley.

# Experiencia de la pestaña

Al ingresar a una organización, mostrar Documentos recomendados, Todos los documentos y Mis documentos. Encabezado con organización activa y estado de perfil. Buscador por código nombre finalidad y contenido autorizado; filtros por familia etapa formato naturaleza aplicabilidad variante y estado.

Cada fila muestra código, título, propósito breve, formato, motivo de recomendación, versión y estado. Una ficha lateral contiene cuándo se usa, insumos, fuentes, pendientes, campos requeridos, vista previa y documentos relacionados. No mostrar al cliente una plantilla planificada como descargable.

Acciones: ver ficha; crear documento para esta organización; completar datos; guardar borrador; descargar editable; vincular a acción; enviar a revisión; aprobar según permiso; registrar implementación; adjuntar evidencia; consultar historial. Si faltan campos obligatorios, señalar cada campo y bloquear aprobación, manteniendo guardado y descarga de borrador identificada.

La vista previa y los ejemplos deben indicarse como demostrativos. La descarga necesita permisos de lectura y genera evento de auditoría. La búsqueda de contenido respeta el aislamiento de cada organización y nunca utiliza documentos de otros clientes como ejemplos de IA.

# Reglas de selección y trazabilidad

La selección usa hechos por tratamiento. Los valores desconocidos no se convierten en No. Las reglas AP-01 a AP-16 del catálogo conservan pregunta, lógica, documentos y responsable de validación. Su automatización requiere prueba contra la norma completa y control de versión. Los resultados son sugerencias revisables, no dictámenes automáticos.

RAT: separar el supuesto general del art. 38 RGLOPDP de los supuestos específicos de gran escala. El oficio N12 diferencia RAT y DPD pero es no vinculante y no elimina la revisión de N09. No configurar la regla simplista Todo centro médico tiene RAT obligatorio ni la regla Solo 100 trabajadores en todos los casos.

Cada pregunta del assessment se vincula a uno o varios requisitos; cada requisito a hallazgos; hallazgos a acciones; acciones a documentos y evidencias. Definir tablas de enlace para relaciones muchos a muchos. No utilizar el nombre del archivo como clave de relación.

Las 80 preguntas no fueron suministradas. Crear una tabla de mapeo con question_id real, versión de cuestionario, requirement_id, tipo de evidencia y regla; mantener Sin mapear hasta recibir la fuente. No inventar números de preguntas.

# Automatización y actualización de documentos

1. Capturar perfil y actividad. 2. Evaluar reglas con evidencia. 3. Recomendar plantillas. 4. Instanciar la versión seleccionada. 5. Insertar únicamente variables verificadas. 6. Marcar campos faltantes. 7. Revisión y aprobación. 8. Implementación y comprobación. Cualquier IA debe mostrar origen de los datos, versión del modelo y cambios propuestos.

Para generación determinista de DOCX, el futuro motor sustituirá variables y bloques condicionales. En Excel mantendrá fórmulas y validaciones. Esta entrega proporciona archivos y diccionario; no incluye un servicio de generación conectado a la plataforma.

Cuando cambia una norma, crear evento normativo, identificar requisitos y versiones afectadas y asignar revisión. Publicar una nueva versión tras aprobarla, emitir aviso a organizaciones afectadas y ofrecer comparación. Nunca sobrescribir documentos aprobados ni afirmar que el aviso equivale a su actualización efectiva.

# Permisos y protección de la información

| Rol | Permisos propuestos |

| --- | --- |

| Administrador editorial | Gestiona maestros reglas y fuentes; publicación exige revisiones registradas |

| Consultor asignado | Accede solo a organizaciones autorizadas; elabora instancias y solicita revisión |

| Dueño de proceso | Completa datos y aporta evidencias de sus actividades |

| Revisor jurídico | Revisa fundamento aplicabilidad y restricciones; deja observaciones |

| DPD | Asesora y supervisa; acceso necesario sin asumir decisiones de implementación |

| Responsable o delegado autorizado | Aprueba documentos decisiones de riesgo y recursos según facultades |

| Auditor | Lectura de alcance autorizado y evidencias; registra comprobaciones sin alterar aprobaciones |

Aplicar autorización por organización en cada petición y descarga; denegar acceso por defecto; usar enlaces temporales; registrar lectura y descarga de evidencias sensibles; cifrar tránsito y almacenamiento; autenticar roles privilegiados y disponer de respaldo y recuperación verificados. Los registros de auditoría deben resistir alteraciones y tener retención definida. Son requisitos de diseño que deben comprobarse en la implementación.

# Cierre de acciones e indicadores

Una acción se cierra al cumplir sus criterios de aceptación, con evidencia accesible y verificable, revisión por persona autorizada y comprobación de eficacia cuando corresponda. Cargar o descargar un archivo no acredita implementación. Las exclusiones necesitan decisión motivada e historial, no borrado del hallazgo.

PLA-01 utiliza fecha de corte explícita, fechas Excel reales y una puerta de cierre verificable. La alerta detecta evidencia, revisor, resultado y fecha de verificación faltantes. Es una ayuda operacional que requiere comprobar el contenido de la evidencia. En producción impedir que un estado Cerrada se acepte si falta un requisito.

Indicadores propuestos: acciones verificadas sobre acciones aplicables; acciones vencidas con fecha validada; documentos desactualizados; decisiones pendientes de información. Mostrar denominador, exclusiones, fecha de corte y resultados sin mapear. Ningún porcentaje debe denominarse garantía de cumplimiento legal.

# Pruebas de aplicabilidad con perfiles ficticios

## Microempresa privada de servicios

8 trabajadores; clientes adultos; sin biometría; nube con soporte extranjero; encargados de nómina

Selección propuesta: INV-01;INV-02;LEG-01;AVI-01;PRO-01;PLA-01;PRV-01;TRA-01;GOB-01;EIPD-00

Decisiones: RAT: adopción recomendada si no concurre supuesto específico; escala pendiente de datos. DPD: evaluar actividad, no presumir exención.

No activar VAR-BIO; CON-01 solo al confirmar encargado; LIA solo si base elegida lo requiere.

## Centro médico privado mediano

60 trabajadores; historias clínicas; sin biometría; prestador institucional no consultorio individual; escala por verificar

Selección propuesta: Base general;VAR-SAL;GOB-01;GOB-02 si confirma art.10.7;ESC-01;EIPD-00;RET-01;PRV-01

Decisiones: DPD: supuesto sectorial N05 art.10.7 a contrastar. RAT: no inferir obligatoriedad solo por salud; valorar N09 art.6. EIPD: si escala especial o alto riesgo.

Plazo historia clínica pendiente de normativa sanitaria; consentimiento asistencial separado.

## Entidad pública municipal

180 trabajadores; competencias públicas; plataforma de trámites; proyecto de acceso biométrico

Selección propuesta: Base general;RAT-01;GOB-01;GOB-02;VAR-PUB;VAR-BIO;EIPD-01;DIS-01

Decisiones: RAT por art.38; DPD por sector público. Biometría exige revisión de necesidad y EIPD; no autoriza por sí sola su uso.

Competencias públicas por finalidad; transparencia no habilita divulgar indiscriminadamente datos personales.

# Producción por lotes

| Lote | Contenido | Salida y criterio de cierre |

| --- | --- | --- |

| 0 | DIA-01 y DIA-02 | Mapear salidas existentes; requiere cuestionario y esquema reales |

| 1 | 8 plantillas iniciales | Entregadas v0.1 para revisión; archivos abren y controles revisados |

| 2 | Riesgos gobierno controles e incidentes | Producir 10 archivos tras consolidar N03 N05 N09 N13 |

| 3 | Legitimación derechos consentimiento y terceros | Producir 10 archivos; cotejar anexos y reglas de N04 N07 |

| 4 | Transferencias diseño y conservación | Producir 6 archivos; verificar N06 y normativa sectorial |

| 5 | Formación monitoreo auditoría y documentación | Producir 5 archivos; definir métricas y evidencias |

| 6 | 9 variantes sectoriales y tecnológicas | Producir anexos condicionales; fuentes sectoriales e IA consolidadas |

Orden propuesto dentro del lote 2: PRO-02, INC-01, INC-02, GOB-01, GOB-03, ESC-01, RIE-01, SEG-01, EIPD-01 y POL-01. Ajustar prioridad ante incidentes o tratamientos de alto riesgo. Los lotes siguientes están planificados, no generados en este primer paquete.

# Fuentes y límites de verificación

Fecha de consulta y corte de esta entrega: 24 de octubre de 2026, Ecuador. La revisión es específica de las disposiciones señaladas; no representa una certificación de vigencia consolidada de todo el ordenamiento. El catálogo Fuentes distingue texto localizado, disposición revisada, publicación corroborada y pendientes.

N01 — LOPDP. Arts. 7 a 10, 12 a 24, 25 a 30, 37 a 43, 46 a 50 y 55 a 61. Publicación original 26 mayo 2021. Texto consultado; verificar reformas al aplicar.
https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf

N02 — Reglamento General Decreto 904. Art. 38 y capítulos sobre derechos, EIPD y DPD. RO tercer suplemento 435 de 13 noviembre 2023. Verificación de publicación; cotejo específico pendiente salvo art. 38 reproducido por SPDP.
https://www.spdp.gob.ec/wp-content/uploads/2026/09/03-Reglamento-General-de-la-Ley-Organica-de-Proteccion-de-Datos-Personales-2023.pdf

N03 — SPDP-SPD-2025-0003-R y guía de riesgos. Guía y anexo de evaluación de impacto. Instrumento localizado en portal oficial; cotejo metodológico íntegro pendiente.
https://spdp.gob.ec/wp-content/uploads/2025/05/GUIA-DE-GESTION-DE-RIESGOS-E-IMPACTO-VERSION-1.pdf

N04 — SPDP-SPD-2025-0006-R. Cláusulas contractuales y anexos por relación. Texto oficial localizado. Publicación y control de reformas pendientes de cotejo antes del lote contractual.
https://www.spdp.gob.ec/wp-content/uploads/2025/12/06.01.01-SPDP-SPD-2025-0006-R-clausulas-para-contratos-en-Ecuador-signed_compressed.pdf

N05 — SPDP-SPD-2025-0028-R. Arts. 4 y 10 y reglas de independencia. RO 105 de 19 agosto 2025 corroborado por oficio oficial N12. Verificar reformas antes de nombramiento.
https://www.spdp.gob.ec/wp-content/uploads/2025/12/028-R_compressed.pdf

N06 — SPDP-SPD-2025-0030-R. Reglamento de seudonimización anonimización bloqueo y eliminación. Existencia y título comprobados; PDF no accesible. Articulado pendiente de verificación normativa.
https://www.spdp.gob.ec/resoluciones/

N07 — SPDP-SPD-2025-0041-R. Arts. 5 a 10 y anexo 1; supuestos y prohibiciones. Texto oficial revisado en disposiciones indicadas; publicación y reformas por corroborar antes de aprobar LIA.
https://www.spdp.gob.ec/wp-content/uploads/2025/12/41.01.01-SPSP-SPD-2025-0041-R-Normativa-general-para-la-aplicacion-del-interes-legitimo-y-su-anexo_compressed.pdf

N08 — SPDP-SPD-2026-0004-R. Arts. 49 y 50 y régimen de transferencias. Texto oficial revisado parcialmente; publicación y relación con norma 2025-0024-R pendientes. No afirmar derogatoria no comprobada.
https://www.spdp.gob.ec/wp-content/uploads/2026/08/04.01.01-SPSP-SPD-2026-0004-R-Norma-general-de-transferencias-signed.pdf

N09 — SPDP-SPD-2026-0005-R. Arts. 4 a 6; MTGE y anexos. Art. 6 revisado. Publicación y validación íntegra del MTGE pendientes antes de automatizar la clasificación.
https://www.spdp.gob.ec/wp-content/uploads/2026/08/Resolucion0005.pdf

N10 — SPDP-SPD-2026-0009-R y reforma 0037-R. Norma de IA y reforma de septiembre 2026. Textos oficiales localizados; consolidación y publicación pendientes antes de producir variante IA.
https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0037-R.pdf

N11 — SPDP-SPD-2026-0039-R. Arts. 13 a 16 y disposición transitoria. Publicación confirmada RO 376 de 24 septiembre 2026. Revisar transición de sistemas preexistentes.
https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0039-R-Norma-General-para-el-Tratamiento-de-Datos-Biometricos-signed.pdf

N12 — Oficio SPDP-IRD-2026-0064-O. Reproduce art. 38 RGLOPDP y diferencia RAT y DPD. Texto oficial revisado. Es opinión para la consulta; no norma general ni exención frente a otras normas posteriores.
https://www.spdp.gob.ec/docs/consultas-absueltas/2026-2/oficio-n-spdp-ird-2026-0064-o/

N13 — SPDP-SPD-2026-0040-R. Arts. 8, 11 a 13 y disposición final. Publicación confirmada suplemento RO 376 de 24 septiembre 2026. Canal SISPDP; auxiliar no sustituye envío.
https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0040-r.pdf

N14 — Registro Oficial 376. Sumario biometría 0039-R. 24 septiembre 2026; comprobado.
https://www.registroficial.gob.ec/registro-oficial-no-376-16/

N15 — Suplemento Registro Oficial 376. Sumario notificaciones 0040-R. 24 septiembre 2026; comprobado.
https://www.registroficial.gob.ec/suplemento-no-376/

Pendientes materiales: articulado íntegro de N06; consolidación de IA N10; plazos por cada derecho del Reglamento; formalidades de transferencias y su régimen vigente; conservación sanitaria educativa laboral y archivo público. Las variantes sectoriales permanecen planificadas hasta completar esa revisión. Las fuentes oficiales publicadas después de la fecha de corte quedan fuera.

# Validación y condiciones para publicar la biblioteca

Este paquete se verifica por apertura, estructura y revisión visual de Word y hojas de Excel; los controles de fórmulas se prueban con datos ficticios. El informe de validación incluido en el paquete recoge los resultados efectivos y sus límites. No se ha probado integración web ni operación en una cuenta real de EVYDENTIA.

Antes de publicar: revisión jurídica y sectorial; completar configuración de plazos; validar motor de reglas; aprobar versiones maestras; probar separación de organizaciones, permisos y generación; ejecutar pruebas de aceptación con consultores. Mantener una política de revisión normativa con responsable y evidencias.
