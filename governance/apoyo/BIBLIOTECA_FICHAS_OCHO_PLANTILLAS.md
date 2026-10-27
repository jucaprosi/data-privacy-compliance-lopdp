# Fichas funcionales de las ocho plantillas iniciales

> Conversión trazable del documento `data/biblioteca/kit_v1/especificacion/fichas_ocho_plantillas.docx`. La sección EIPD-00 está actualizada a la plantilla v0.2 (2026-10-26); las diferencias con el DOCX original constan en `BIBLIOTECA_ESTADO.md` §10. El DOCX conserva el original recibido; este Markdown permite revisar los campos y reglas desde Git. Las ocho plantillas v0.1 permanecen en revisión editorial y jurídica.

EVYDENTIA    ANEXO BIB 01    Versión 1.0 para revisión de producto

Fecha de diseño 24 de octubre de 2026

Este anexo especifica qué capturar, de dónde obtenerlo, cómo validarlo y cómo generar cada documento. Debe utilizarse junto con el PRD y los archivos originales del lote 1; no sustituye la revisión jurídica del contenido.

# 1 Convenciones comunes

O significa obligatorio para generar una versión para revisión. C significa condicional. D significa derivado y no editable. Un borrador puede guardarse incompleto; sus faltantes permanecen visibles. La aprobación de entrega 3 exige validación adicional según el flujo y la aplicabilidad. Cada campo conserva origen, responsable de validación y revisión de la fuente.

Los datos de empresa, actores, tratamiento, relaciones, versiones y auditoría se guardan en objetos estructurados. La pantalla muestra etiquetas comprensibles; las claves estables sirven al desarrollador. Los nombres técnicos y enlaces de salida se consultan en Backlog_y_Esquemas_Biblioteca_EVYDENTIA.json. El estado de una fila del inventario o RAT indica validación del registro; no equivale a aprobación del documento ni a cierre de una acción.

Los campos de texto aceptan Unicode y se guardan como texto seguro; fechas usan YYYY-MM-DD y horas ISO con zona; correos y URLs se validan por sintaxis y uso. Los IDs se resuelven en el servidor y requieren pertenencia a la organización. Los catálogos tienen claves estables y etiquetas versionadas. Un dato desconocido se representa expresamente, no como falso ni texto vacío equivalente a No.

Las ocho fichas se desarrollan en entrega 2. La descarga del maestro se habilita en entrega 1 al publicarse su versión; revisión, aprobación e integración completas se añaden en entrega 3. El sistema no necesita IA para generar estas ocho salidas.

## Lista de comprobación del desarrollador

Para cada ficha: validar mapa de campos con consultor; comprobar norma y regla aplicable; preparar plantilla de producción; publicar esquema compatible; implementar captura y precarga; comparar vista previa con archivo; probar datos incompletos y condicionales; comprobar permisos; registrar evidencia de aceptación. Una ficha especificada no equivale a una pantalla implementada.

# INV-01 Inventario de datos personales

Interfaz: Tabla de categorías de datos por actividad. Origen principal: Dueño de proceso; formularios y repositorios; referencias del tratamiento.

Unidad de captura: Una fila por categoría de datos y actividad; varias filas pueden compartir tratamiento_id.

## Campos y mapa de salida Excel

| Columna y campo | Req | Tipo | Regla |

| --- | --- | --- | --- |

| A Inventario ID | D | ID generado | ID estable generado por servidor; no solicitar digitación manual. |

| B Tratamiento ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| C Proceso y área | O | Texto | Completar y validar antes de generar para revisión. |

| D Finalidad | O | Texto | Completar y validar antes de generar para revisión. |

| E Categoría de titulares | O | Texto | Completar y validar antes de generar para revisión. |

| F Categoría de datos | O | Texto | Completar y validar antes de generar para revisión. |

| G Ejemplos de campos sin valores | C | Texto | Completar si corresponde al contexto; registrar No aplica con motivo. |

| H Origen y canal | O | Texto | Completar y validar antes de generar para revisión. |

| I Operaciones | O | Texto | Completar y validar antes de generar para revisión. |

| J Repositorio o activo ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| K Custodio por rol | O | Texto | Completar y validar antes de generar para revisión. |

| L Categoría especial | O | Lista | Completar y validar antes de generar para revisión. Opciones: Sí, No, Por evaluar. |

| M Volumen estimado y unidad | C | Texto | Si se conoce volumen; si falta, registrar unidad y acción para determinarlo. |

| N Países de acceso | C | Texto | Si hay almacenamiento o acceso fuera; desconocido mantiene pendiente. |

| O Destinatarios por rol | C | Texto | Si existen destinatarios. |

| P Retención y evento inicial | C | Texto | Debe definirse antes de validar; puede quedar pendiente solo en borrador. |

| Q Fundamento de retención | C | Texto | Debe justificar retención antes de validar. |

| R Evidencia de levantamiento | O | Texto | Completar y validar antes de generar para revisión. |

| S Fecha de revisión | O | Fecha | Completar y validar antes de generar para revisión. Validar fecha real; no admitir texto ni cero. |

| T Estado | O | Lista | Completar y validar antes de generar para revisión. Opciones: Borrador, Revisado, Validado. |

## Validaciones y generación

No admitir IDs repetidos por fila dentro de la misma empresa.

Una categoría especial obliga a completar su evaluación en LEG-01.

No guardar valores de personas; registrar nombre de campo, no números o historias clínicas.

Generar XLSX con guía y fuentes identificadas, sin incluir la hoja Ejemplo en la salida de cliente. Registro recibe solo filas de esta empresa. Conservar encabezados, tipos, filtros y validaciones; extender fórmulas autorizadas hasta la última fila real. Añadir metadatos de corte y versión sin modificar los datos fuente.

## Casos mínimos por ficha

INV-01 CA 1. Crear dos categorías de la misma actividad conserva un único tratamiento vinculado.

INV-01 CA 2. Registrar país desconocido no genera una afirmación de ausencia de transferencia.

INV-01 CA 3. Validar sin finalidad o evidencia bloquea envío a revisión.

# INV-02 Inventario de activos y sistemas

Interfaz: Tabla de activos físicos y digitales. Origen principal: TI, custodios, proveedores y contratos.

Unidad de captura: Una fila por activo; colección de relaciones a tratamientos, no texto sin validar.

## Campos y mapa de salida Excel

| Columna y campo | Req | Tipo | Regla |

| --- | --- | --- | --- |

| A Activo ID | D | ID generado | ID estable generado por servidor; no solicitar digitación manual. |

| B Nombre del activo | O | Texto | Completar y validar antes de generar para revisión. |

| C Tipo | O | Lista | Completar y validar antes de generar para revisión. Opciones: Físico, Servidor, Nube, Aplicación, Equipo, Respaldo, Otro. |

| D Tratamiento IDs | O | Lista de IDs | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| E Dueño por rol | O | Texto | Completar y validar antes de generar para revisión. |

| F Custodio por rol | O | Texto | Completar y validar antes de generar para revisión. |

| G Ubicación o proveedor | O | Texto | Completar y validar antes de generar para revisión. |

| H País almacenamiento | C | Texto | País confirmado o estado Pendiente con tarea; no inferirlo del domicilio del proveedor. |

| I País acceso remoto | C | Texto | Si hay soporte remoto; estado desconocido obliga revisión. |

| J Encargado o rol por validar | O | Texto | Completar y validar antes de generar para revisión. |

| K Acceso autorizado por rol | O | Texto | Completar y validar antes de generar para revisión. |

| L Medidas declaradas | O | Texto | Completar y validar antes de generar para revisión. |

| M Evidencia del control | C | Texto | Declaración de control sin evidencia no permite estado Validado. |

| N Respaldo y recuperación | C | Texto | Si existe respaldo; documentar prueba y responsable. |

| O Disposición al fin del servicio | C | Texto | Si activo o servicio tiene disposición al finalizar. |

| P Contrato o evaluación ID | C | Referencia | Si interviene proveedor o contrato. Validar referencia y empresa. |

| Q Última revisión | O | Fecha | Completar y validar antes de generar para revisión. Validar fecha real; no admitir texto ni cero. |

| R Estado | O | Lista | Completar y validar antes de generar para revisión. Opciones: Borrador, Revisado, Validado. |

## Validaciones y generación

Cada tratamiento relacionado debe pertenecer a la empresa activa.

Excluir contraseñas y secretos; restringir el acceso al inventario.

Registrar control declarado y evidencia de comprobación por separado.

Generar XLSX con guía y fuentes identificadas, sin incluir la hoja Ejemplo en la salida de cliente. Registro recibe solo filas de esta empresa. Conservar encabezados, tipos, filtros y validaciones; extender fórmulas autorizadas hasta la última fila real. Añadir metadatos de corte y versión sin modificar los datos fuente.

## Casos mínimos por ficha

INV-02 CA 1. Relacionar un activo con dos tratamientos genera dos enlaces válidos.

INV-02 CA 2. Elegir un tratamiento de otra empresa es rechazado por servidor.

INV-02 CA 3. Un archivo físico permite ubicación sin forzar un proveedor de nube.

# RAT-01 Registro de actividades de tratamiento

Interfaz: Tabla o asistente por actividad de tratamiento. Origen principal: INV-01, INV-02, perfil, LEG-01 y decisiones revisadas.

Unidad de captura: Una actividad puede tener varias finalidades; conservar bases y retención por finalidad.

## Campos y mapa de salida Excel

| Columna y campo | Req | Tipo | Regla |

| --- | --- | --- | --- |

| A Tratamiento ID | D | ID generado | Recuperar ID de tratamiento existente; generar solo al crear una actividad nueva. |

| B Nombre de actividad | O | Texto | Completar y validar antes de generar para revisión. |

| C Rol de organización | O | Lista | Completar y validar antes de generar para revisión. Opciones: Responsable, Encargado, Por evaluar. |

| D Responsable y contacto | O | Texto | Completar y validar antes de generar para revisión. |

| E Corresponsable si aplica | C | Texto | Si existe corresponsable confirmado. |

| F DPD y contacto si existe | C | Texto | Si existe DPD; recuperar contacto completo validado. |

| G Finalidades | O | Texto | Completar y validar antes de generar para revisión. |

| H Titulares | O | Texto | Completar y validar antes de generar para revisión. |

| I Categorías de datos | O | Texto | Completar y validar antes de generar para revisión. |

| J Operaciones y origen | O | Texto | Completar y validar antes de generar para revisión. |

| K Destinatarios y rol | O | Texto | Completar y validar antes de generar para revisión. |

| L Perfiles y decisiones automatizadas | O | Texto | Completar y validar antes de generar para revisión. |

| M Transferencias países y garantías | O | Texto | Completar y validar antes de generar para revisión. |

| N Bases legitimadoras motivadas | O | Texto | Completar y validar antes de generar para revisión. |

| O Condición para categorías especiales | C | Texto | Si hay categorías especiales; necesita condición adicional. |

| P Retención evento y fundamento | O | Texto | Completar y validar antes de generar para revisión. |

| Q Medidas generales | O | Texto | Completar y validar antes de generar para revisión. |

| R Activo IDs | O | Lista de IDs | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| S Dueño de proceso | O | Texto | Completar y validar antes de generar para revisión. |

| T Supuesto RAT o adopción voluntaria | C | Texto | Decisión motivada específica; sin información conservar borrador. |

| U Evidencia de aplicabilidad | O | Texto | Completar y validar antes de generar para revisión. |

| V Última revisión | O | Fecha | Completar y validar antes de generar para revisión. Validar fecha real; no admitir texto ni cero. |

| W Revisado por | O | Texto | Completar y validar antes de generar para revisión. |

| X Estado | O | Lista | Completar y validar antes de generar para revisión. Opciones: Borrador, Revisado, Validado. |

## Validaciones y generación

No crear otro tratamiento al exportar una actividad ya existente.

Aplicabilidad distingue supuesto normativo de adopción voluntaria; requiere regla publicada y versión.

Los contactos se gestionan como objetos estructurados; la salida puede mostrarlos en una celda.

Generar XLSX con guía y fuentes identificadas, sin incluir la hoja Ejemplo en la salida de cliente. Registro recibe solo filas de esta empresa. Conservar encabezados, tipos, filtros y validaciones; extender fórmulas autorizadas hasta la última fila real. Añadir metadatos de corte y versión sin modificar los datos fuente.

## Casos mínimos por ficha

RAT-01 CA 1. Actividad con tres finalidades exporta todas sin truncar a dos.

RAT-01 CA 2. Perfil sin DPD no genera contacto ficticio ni casilla sin resolver.

RAT-01 CA 3. Cambiar una base revisada marca instancias afectadas sin cambiar un archivo aprobado.

# LEG-01 Matriz de bases legitimadoras por finalidad

Interfaz: Tabla de evaluación por finalidad. Origen principal: RAT, jurídico, norma o hecho habilitante y evidencias.

Unidad de captura: Una evaluación por finalidad y rol; IDs relacionados con la misma empresa.

## Campos y mapa de salida Excel

| Columna y campo | Req | Tipo | Regla |

| --- | --- | --- | --- |

| A Evaluación ID | D | ID generado | ID estable generado por servidor; no solicitar digitación manual. |

| B Tratamiento ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| C Finalidad específica | O | Texto | Completar y validar antes de generar para revisión. |

| D Rol | O | Lista | Completar y validar antes de generar para revisión. Opciones: Responsable, Encargado, Por evaluar. |

| E Base propuesta art 7 | O | Texto | Completar y validar antes de generar para revisión. |

| F Norma contrato o hecho habilitante | O | Texto | Completar y validar antes de generar para revisión. |

| G Necesidad de datos | O | Texto | Completar y validar antes de generar para revisión. |

| H Datos sensibles o especiales | O | Texto | Completar y validar antes de generar para revisión. |

| I Condición especial y sustento | C | Texto | Obligatoria si hay categoría especial. |

| J Requiere consentimiento | O | Texto | Completar y validar antes de generar para revisión. |

| K LIA ID si procede | C | Referencia | Obligatoria si la base propuesta es interés legítimo y su uso resulta admisible. Validar referencia y empresa. |

| L Evidencia de la base | O | Texto | Completar y validar antes de generar para revisión. |

| M Aviso y versión ID | C | Referencia | Antes de poner el aviso a disposición del titular. Validar referencia y empresa. |

| N Restricciones y salvaguardas | O | Texto | Completar y validar antes de generar para revisión. |

| O Decisión jurídica | O | Lista | Completar y validar antes de generar para revisión. Opciones: Admisible, No admisible, Información insuficiente, Pendiente de revisión. |

| P Acción ante faltantes | C | Texto | Si la decisión es información insuficiente o no admisible. |

| Q Elabora por rol | O | Texto | Completar y validar antes de generar para revisión. |

| R Revisa y fecha | O | Texto | Completar y validar antes de generar para revisión. |

| S Estado | O | Lista | Completar y validar antes de generar para revisión. Opciones: Borrador, Revisado, Validado. |

## Validaciones y generación

Una base propuesta no se convierte automáticamente en Admisible.

La decisión jurídica requiere revisor y evidencia.

Interés legítimo no se asigna por defecto y no reemplaza el régimen de datos especiales.

Generar XLSX con guía y fuentes identificadas, sin incluir la hoja Ejemplo en la salida de cliente. Registro recibe solo filas de esta empresa. Conservar encabezados, tipos, filtros y validaciones; extender fórmulas autorizadas hasta la última fila real. Añadir metadatos de corte y versión sin modificar los datos fuente.

## Casos mínimos por ficha

LEG-01 CA 1. Seleccionar interés legítimo activa la referencia LIA sin declararla aprobada.

LEG-01 CA 2. Categoría especial sin sustento impide validar.

LEG-01 CA 3. Cambio de finalidad requiere nueva evaluación o revisión, conservando historial.

# PLA-01 Plan de acción de implementación

Interfaz: Vista y exportación del plan de acción existente. Origen principal: Módulo canónico de acciones, brechas, revisiones y evidencias.

Unidad de captura: Una fila por acción existente; Biblioteca no crea un plan paralelo.

## Campos y mapa de salida Excel

| Columna y campo | Req | Tipo | Regla |

| --- | --- | --- | --- |

| A Acción ID | D | ID generado | Recuperar ID de acción del plan existente; nunca generar otra acción al exportar. |

| B Brecha ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| C Tratamiento ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| D Requisito ID | O | Referencia | Completar y validar antes de generar para revisión. Validar referencia y empresa. |

| E Acción concreta | O | Texto | Completar y validar antes de generar para revisión. |

| F Prioridad | O | Lista | Completar y validar antes de generar para revisión. Opciones: Alta, Media, Baja. |

| G Responsable por rol | O | Texto | Completar y validar antes de generar para revisión. |

| H Fecha objetivo | O | Fecha | Completar y validar antes de generar para revisión. Validar fecha real; no admitir texto ni cero. |

| I Estado declarado | O | Lista | Completar y validar antes de generar para revisión. Opciones: Pendiente, En curso, En revisión, Cerrada. |

| J Criterio de aceptación | O | Texto | Completar y validar antes de generar para revisión. |

| K Documento IDs | C | Lista de IDs | Si hay documentos vinculados. Validar referencia y empresa. |

| L Evidencia IDs | C | Lista de IDs | Obligatorio para cerrar. Validar referencia y empresa. |

| M Revisor | C | Texto | Obligatorio para cerrar. |

| N Resultado verificación | C | Lista | Conforme obligatorio para cierre verificable. Opciones: Conforme, No conforme, Pendiente. |

| O Fecha verificación | C | Fecha | Fecha real y no futura al corte para cerrar. Validar fecha real; no admitir texto ni cero. |

| P Requiere eficacia | O | Lista | Completar y validar antes de generar para revisión. Opciones: Sí, No. |

| Q Resultado eficacia | C | Lista | Conforme si se requiere eficacia. Opciones: Conforme, No conforme, Pendiente. |

| R Control de cierre | D | Cálculo | Solo lectura; calcular desde la instantánea. |

| S Alerta temporal | D | Cálculo | Solo lectura; calcular desde la instantánea. |

## Validaciones y generación

R y S son derivados y de solo lectura; fechas almacenadas con tipo.

Fecha de corte visible y editable por permiso; el archivo exporta una instantánea identificada.

La fórmula del Excel ayuda a verificar integridad; el cierre real se autoriza en servidor con evidencias revisadas.

Generar XLSX con guía y fuentes identificadas, sin incluir la hoja Ejemplo en la salida de cliente. Registro recibe solo filas de esta empresa. Conservar encabezados, tipos, filtros y validaciones; extender fórmulas autorizadas hasta la última fila real. Añadir metadatos de corte y versión sin modificar los datos fuente.

Vínculos particulares: columnas A a D recuperan IDs canónicos; H y O son fechas; R controla elegibilidad del cierre y S compara vencimiento con fecha de corte. La condición final se verifica en servidor. Reglas de fórmula y prueba inicial están en PLA-01.xlsx; el equipo debe reproducirlas sin evaluar fórmulas no autorizadas.

## Casos mínimos por ficha

PLA-01 CA 1. Cerrar sin evidencia deja Cierre bloqueado y no cambia la acción en servidor.

PLA-01 CA 2. Fecha texto o cero devuelve error; no aparece En plazo.

PLA-01 CA 3. Reexportar tras cambiar el plan crea otra revisión y conserva el archivo anterior.

# EIPD-00 Análisis de necesidad de EIPD

Interfaz: Asistente con contexto, criterios, evidencias y conclusión. Salida principal: DOCX editable. Las secciones se muestran con condiciones y datos de origen visibles.

## Contexto

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| FINALIDAD | O | Obligatorio para esta sección antes de generar para revisión. |

| OPERACIONES_DATOS_TITULARES | O | Obligatorio para esta sección antes de generar para revisión. |

| ROL_FLUJOS | O | Obligatorio para esta sección antes de generar para revisión. |

| CONTEXTO_ESCALA | O | Obligatorio para esta sección antes de generar para revisión. |

| NUEVO_EXISTENTE_CAMBIO | O | Obligatorio para esta sección antes de generar para revisión. |

| FECHA_INICIO | O | Obligatorio para esta sección antes de generar para revisión. |

## Criterios y evidencia

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| SI_NO_DESCONOCIDO | O | Alto riesgo (LOPDP art. 42, primer inciso). Obligatorio para esta sección antes de generar para revisión. |

| ESCENARIOS_Y_SOPORTE | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUADOR_ALTO_RIESGO | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUACION_PERFILES_EFECTOS_JURIDICOS | O | LOPDP art. 42 a). Obligatorio para esta sección antes de generar para revisión. |

| EVIDENCIA_PERFILES | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUADOR_PERFILES | O | Obligatorio para esta sección antes de generar para revisión. |

| GRAN_ESCALA | O | Resultado del MTGE (N09 arts. 4 a 6 y 12.1). Obligatorio para esta sección antes de generar para revisión. |

| CAT_ESPECIAL | O | LOPDP art. 42 b). Obligatorio para esta sección antes de generar para revisión. |

| PENAL | O | Datos relativos a condenas e infracciones penales, LOPDP art. 42 b). Obligatorio para esta sección antes de generar para revisión. |

| EVIDENCIA_GRAN_ESCALA | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUADOR_GRAN_ESCALA | O | Obligatorio para esta sección antes de generar para revisión. |

| OBSERVACION_PUBLICA_GRAN_ESCALA | O | LOPDP art. 42 c). Obligatorio para esta sección antes de generar para revisión. |

| EVIDENCIA_OBSERVACION_PUBLICA | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUADOR_OBSERVACION_PUBLICA | O | Obligatorio para esta sección antes de generar para revisión. |

| REQUERIMIENTO_AUTORIDAD | O | Requerimiento de la Autoridad (LOPDP art. 42, primer inciso). Obligatorio para esta sección antes de generar para revisión. |

| REQUERIMIENTO_REFERENCIA | C | Si existe requerimiento de la Autoridad. |

| EVALUADOR_REQUERIMIENTO | O | Obligatorio para esta sección antes de generar para revisión. |

| BIOMETRIA_SI_NO | O | N11 arts. 5, 13 y 15. Obligatorio para esta sección antes de generar para revisión. |

| BIOMETRIA_NUEVO_O_EXISTENTE | C | Si hay sistema biométrico; distingue sistema nuevo y sistema en uso antes de la vigencia de N11 (disposición transitoria). |

| EVIDENCIA_BIOMETRIA | O | Obligatorio para esta sección antes de generar para revisión. |

| EVALUADOR_BIOMETRIA | O | Obligatorio para esta sección antes de generar para revisión. |

| OTRO_SUPUESTO_RESPUESTA | O | Otros supuestos establecidos por la Autoridad (LOPDP art. 42, penúltimo inciso). Obligatorio para esta sección antes de generar para revisión. |

| NORMA_ARTICULO_SUPUESTO | C | Si existe disparador adicional confirmado. |

| EVALUADOR_OTRO_SUPUESTO | C | Si existe disparador adicional confirmado. |

## Conclusión y pendientes

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| RESULTADO_EIPD | O | Obligatorio para esta sección antes de generar para revisión. |

| NORMA_Y_ARTICULO | O | Obligatorio para esta sección antes de generar para revisión. |

| EVIDENCIA_ID | O | Obligatorio para esta sección antes de generar para revisión. |

| MOTIVACION | O | Obligatorio para esta sección antes de generar para revisión. |

| DATOS_FALTANTES | C | Si hay información insuficiente. |

| RESPONSABLE_OBTENERLOS | C | Si hay información insuficiente. |

| FECHA_LIMITE_DATOS | C | Si hay información insuficiente. |

| CONSULTA_AUTORIDAD_REFERENCIA | C | Si se consulta a la Autoridad (RGLOPDP art. 31, tercer inciso). |

| EVENTO_REVISION | C | Si no se identifica obligación o hay condición de revisión. |

| ACCION_ID | C | Si hay acción creada o vinculada; enlace real en entrega 3. |

## Metadatos y variables de control

| Variable | Tratamiento |

| --- | --- |

| ALCANCE | Alcance de empresa o actividad; no exigir una única actividad si el procedimiento abarca varios procesos. |

| APRUEBA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| DESCRIPCION_CAMBIO | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| ELABORA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| ESTADO_DOCUMENTO | Estado del documento de empresa; sustituye el texto fijo «Borrador» de v0.1. |

| FECHA | Fecha de elaboración. Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| FECHA_VERSION | Fecha de la fila del control de versiones. |

| ORGANIZACION_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| RAZON_SOCIAL | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| REVISA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| TRATAMIENTO_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| VERSION_CLIENTE | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

## Reglas de contenido y migración del maestro

Cada criterio se captura como respuesta Sí No o Desconocido más evidencia, fundamento y evaluador; el mapa expande la respuesta a los textos del maestro.

Desde v0.2, la respuesta biométrica se vincula a BIOMETRIA_SI_NO y la probabilidad de alto riesgo a SI_NO_DESCONOCIDO; cada criterio tiene sus propias claves de respuesta, evidencia y evaluador. El literal b) del art. 42 se evalúa como GRAN_ESCALA ∧ (CAT_ESPECIAL ∨ PENAL).

Un disparador confirmado mantiene recomendación Requiere EIPD aunque otros criterios sean negativos. Información insuficiente requiere resolver hechos antes de concluir No se identifica obligación.

El motor propone y explica; la decisión final y los supuestos de transición requieren revisión de reglas jurídicas publicadas. No se aplica una suma de casillas.

Retirar instrucciones y ejemplo de la salida de uso. Conservar fuentes pertinentes y control de versión según perfil de exportación. La vista previa y el DOCX deben proceder de la misma instantánea. Los aprobadores se registran al aprobar, no como una firma ficticia al generar.

## Casos mínimos por ficha

EIPD-00 CA 1. Confirmar un disparador y negar otros conserva recomendación de EIPD.

EIPD-00 CA 2. Escala desconocida genera pendientes y permite guardar borrador sin una conclusión negativa automática.

EIPD-00 CA 3. Cambiar el contexto crea revisión; el resultado emitido previo conserva sus hechos y fundamento.

# AVI-01 Aviso de privacidad por tratamiento

Interfaz: Asistente con responsable, actividad, finalidades, conservación, flujos y derechos. Salida principal: DOCX editable. Las secciones se muestran con condiciones y datos de origen visibles.

## Identificación

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| IDENTIFICACION_RESPONSABLE | O | Obligatorio para esta sección antes de generar para revisión. |

| DIRECCION_RESPONSABLE | O | Obligatorio para esta sección antes de generar para revisión. |

| TELEFONO_RESPONSABLE | O | Obligatorio para esta sección antes de generar para revisión. |

| CORREO_RESPONSABLE | O | Obligatorio para esta sección antes de generar para revisión. |

| NOMBRE_DPD | C | Si la organización tiene DPD; el bloque se omite íntegro cuando no corresponde. |

| DIRECCION_DPD | C | Si la organización tiene DPD; el bloque se omite íntegro cuando no corresponde. |

| TELEFONO_DPD | C | Si la organización tiene DPD; el bloque se omite íntegro cuando no corresponde. |

| CORREO_DPD | C | Si la organización tiene DPD; el bloque se omite íntegro cuando no corresponde. |

## Datos y actividad

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| CATEGORIAS_DATOS | O | Obligatorio para esta sección antes de generar para revisión. |

| CATEGORIAS_TITULARES | O | Obligatorio para esta sección antes de generar para revisión. |

| ORIGEN_DATOS | O | Obligatorio para esta sección antes de generar para revisión. |

| FUENTE_Y_CONTEXTO | C | Si hay recolección indirecta. |

| BASE_O_REPOSITORIO | O | Obligatorio para esta sección antes de generar para revisión. |

| OPERACIONES_TRATAMIENTO | O | Obligatorio para esta sección antes de generar para revisión. |

## Finalidades repetibles

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| FINALIDAD_1 | O | Obligatorio para esta sección antes de generar para revisión. |

| BASE_1_Y_SUSTENTO | O | Obligatorio para esta sección antes de generar para revisión. |

| OBLIGATORIEDAD_Y_CONSECUENCIAS_1 | O | Obligatorio para esta sección antes de generar para revisión. |

| FINALIDAD_2_SI_APLICA | C | Cada finalidad adicional en colección repetible. |

| BASE_2_Y_SUSTENTO | C | Para cada finalidad adicional. |

| OPCIONALIDAD_Y_CONSECUENCIAS_2 | C | Según entrega obligatoria u opcional por finalidad. |

| FINALIDADES_POSTERIORES_O_NO_PREVISTAS | O | Obligatorio para esta sección antes de generar para revisión. |

| EFECTO_DATOS_INEXACTOS | O | Obligatorio para esta sección antes de generar para revisión. |

| EFECTOS_NEGATIVA_OPCIONAL | O | Obligatorio para esta sección antes de generar para revisión. |

## Conservación y flujos

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| CATEGORIA_O_SERIE | O | Obligatorio para esta sección antes de generar para revisión. |

| DURACION_O_CRITERIO_CONCRETO | O | Obligatorio para esta sección antes de generar para revisión. |

| EVENTO_INICIO_RETENCION | O | Obligatorio para esta sección antes de generar para revisión. |

| FUNDAMENTO_RETENCION | O | Obligatorio para esta sección antes de generar para revisión. |

| EXCEPCIONES_Y_LIMITE | O | Obligatorio para esta sección antes de generar para revisión. |

| DISPOSICION_FINAL | O | Obligatorio para esta sección antes de generar para revisión. |

| DESTINATARIOS | O | Obligatorio para esta sección antes de generar para revisión. |

| FINALIDADES_COMUNICACION | O | Obligatorio para esta sección antes de generar para revisión. |

| FLUJOS_Y_PAISES | O | Obligatorio para esta sección antes de generar para revisión. |

| MECANISMO_Y_GARANTIAS | O | Obligatorio para esta sección antes de generar para revisión. |

## Derechos y automatización

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| CANAL_DERECHOS | O | Obligatorio para esta sección antes de generar para revisión. |

| CANAL_RETIRO | C | Si una finalidad se basa en consentimiento. |

| EFECTOS_RETIRO | C | Si una finalidad se basa en consentimiento. |

| CANAL_RECLAMOS | O | Obligatorio para esta sección antes de generar para revisión. |

| EXISTENCIA_O_AUSENCIA_VERIFICADA | O | Obligatorio para esta sección antes de generar para revisión. |

| LOGICA_COMPRENSIBLE | C | Si existen perfiles o decisiones automatizadas. |

| DATOS_UTILIZADOS | C | Si existen perfiles o decisiones automatizadas. |

| EFECTOS_PREVISTOS | C | Si existen perfiles o decisiones automatizadas. |

| CANAL_REVISION_HUMANA | C | Si corresponde revisión de decisión automatizada. |

## Publicación

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| AUDIENCIA | O | Obligatorio para esta sección antes de generar para revisión. |

| CANAL_ENTREGA | O | Obligatorio para esta sección antes de generar para revisión. |

| VERSION_AVISO | O | Obligatorio para esta sección antes de generar para revisión. |

| FECHA_PUBLICACION | C | Al programar o registrar publicación, sin confundir fecha de generación. |

| EVIDENCIA_ID | C | Al registrar entrega o publicación efectiva; no se inventa al generar. |

## Metadatos y variables de control

| Variable | Tratamiento |

| --- | --- |

| ALCANCE | Alcance de empresa o actividad; no exigir una única actividad si el procedimiento abarca varios procesos. |

| APRUEBA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| DESCRIPCION_CAMBIO | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| ELABORA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| FECHA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| ORGANIZACION_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| RAZON_SOCIAL | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| REVISA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| TRATAMIENTO_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| VERSION_CLIENTE | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

## Reglas de contenido y migración del maestro

Usar LEG-01 revisada para las bases y RAT para datos y flujos; la ausencia de una base validada bloquea generar para revisión.

Finalidades es una colección sin límite fijo de dos; adaptar el Word a filas repetibles y mantener correspondencia base finalidad consecuencias.

Mantener versiones por tratamiento audiencia y canal. Generar un aviso no prueba su entrega al titular.

Los párrafos condicionales incluyen etiquetas de control que el generador elimina; ni instrucciones al consultor ni comentarios sobre campos pendientes aparecen en la salida final.

Retirar instrucciones y ejemplo de la salida de uso. Conservar fuentes pertinentes y control de versión según perfil de exportación. La vista previa y el DOCX deben proceder de la misma instantánea. Los aprobadores se registran al aprobar, no como una firma ficticia al generar.

## Casos mínimos por ficha

AVI-01 CA 1. Empresa sin DPD omite toda la sección de DPD y no deja nombres vacíos.

AVI-01 CA 2. Tres finalidades con bases distintas generan tres filas y no mezclan obligatoriedad de entrega.

AVI-01 CA 3. Consentimiento ausente omite el bloque de retiro; recolección indirecta mantiene fuente y contexto.

# PRO-01 Procedimiento de atención de derechos

Interfaz: Asistente de configuración operativa de la empresa. Salida principal: DOCX editable. Las secciones se muestran con condiciones y datos de origen visibles.

## Alcance y canales

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| ALCANCE | O | Obligatorio para esta sección antes de generar para revisión. |

| PROCESOS_Y_CANALES | O | Obligatorio para esta sección antes de generar para revisión. |

| CANAL_DERECHOS | O | Obligatorio para esta sección antes de generar para revisión. |

| CANAL_SEGURO_RESPUESTA | O | Obligatorio para esta sección antes de generar para revisión. |

## Política de gestión de solicitudes

| Variable del maestro | Req | Regla |

| --- | --- | --- |

| DERECHO | O | Obligatorio para esta sección antes de generar para revisión. |

| ARTICULO | C | Cada derecho necesita norma validada en matriz de configuración. |

| EVENTO_INICIAL | O | Obligatorio para esta sección antes de generar para revisión. |

| PLAZO_UNIDAD_CALENDARIO | C | Cada derecho habilitado necesita su regla de cómputo revisada. |

| MOTIVO_Y_FUNDAMENTO_O_NO_APLICA | C | Como regla de análisis por derecho; no motivo de una solicitud concreta. |

| GESTOR | O | Obligatorio para esta sección antes de generar para revisión. |

| REVISOR | O | Obligatorio para esta sección antes de generar para revisión. |

## Metadatos y variables de control

| Variable | Tratamiento |

| --- | --- |

| APRUEBA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| DESCRIPCION_CAMBIO | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| ELABORA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| FECHA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| FECHA_HORA_RECEPCION | Referencia del anexo operativo; no capturar caso real al generar PRO-01. |

| FECHA_LIMITE_VALIDADA | Referencia del anexo operativo; no capturar caso real al generar PRO-01. |

| ORGANIZACION_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| RAZON_SOCIAL | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| REVISA | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| SOLICITUD_ID | Referencia del anexo operativo; no capturar caso real al generar PRO-01. |

| TRATAMIENTO_ID | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

| VERSION_CLIENTE | Dato común o de control; recuperar de empresa, actividad, usuario o revisión según corresponda. |

## Reglas de contenido y migración del maestro

El documento configura el procedimiento de la empresa y sus roles; las solicitudes individuales se registrarán en DER-02 cuando se implemente ese módulo.

SOLICITUD_ID, FECHA_HORA_RECEPCION y FECHA_LIMITE_VALIDADA del maestro son referencias ilustrativas del registro operativo. Trasladarlas a un anexo de campos del registro, sin exigir valores de un caso real para crear el procedimiento.

DERECHO, ARTICULO, EVENTO_INICIAL y PLAZO_UNIDAD_CALENDARIO se convierten en una colección de políticas por derecho. No utilizar un plazo universal ni un solo solicitante para la empresa.

Además de las variables originales, capturar roles de recepción, búsqueda, ejecución, revisión y aprobación. El usuario selecciona cargos o grupos; la salida reemplaza las asignaciones ilustrativas del texto base.

Retirar instrucciones y ejemplo de la salida de uso. Conservar fuentes pertinentes y control de versión según perfil de exportación. La vista previa y el DOCX deben proceder de la misma instantánea. Los aprobadores se registran al aprobar, no como una firma ficticia al generar.

## Casos mínimos por ficha

PRO-01 CA 1. Generar un procedimiento sin solicitudes recibidas funciona sin solicitar ID o fecha de una petición individual.

PRO-01 CA 2. Un derecho habilitado sin regla validada de cómputo impide finalizar y queda marcado Configuración pendiente.

PRO-01 CA 3. Cambiar un rol genera una revisión del procedimiento y conserva el anterior aprobado.
