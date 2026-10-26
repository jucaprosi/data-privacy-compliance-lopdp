# Plan de registro de Biblioteca EVYDENTIA

Fecha: 2026-10-25. Solo planificación y gobernanza. Las 23 fichas están pendientes; no existe autorización de implementación, publicación, migración ni despliegue por crear estos documentos.

## Fuente de verdad y trazabilidad
<!-- ¤adpa -->

Una ficha por requisito, sin cambiar sus IDs ni sus 70 criterios de aceptación. El índice se genera, no se edita a mano. En la cabecera se añaden dependencias técnicas; cada ficha conserva también las originales del kit. No hay BIB-000 ni tarea artificial para alcanzar un número.

Kit versionado: `data/biblioteca/kit_v1/`. Orden de lectura: PRD canónico, fichas, backlog JSON, LEER_PRIMERO, catálogo XLSX, diseño, especificación JSON y ocho referencias. Los originales conservan sus huellas en `MANIFIESTO.sha256`; incorporarlos a Git no los publica ni autoriza su importación en base de datos.

PRD del kit manda sobre alcance, fichas sobre captura y backlog sobre trazabilidad. Contratos JSON propuestos se adaptan al código real. Catálogo 50 = ocho archivos para revisión + dos salidas existentes por mapear + 40 planificadas. Ruta heredada `02_Plantillas/` se resuelve al directorio real `03_Plantillas_Referencia/` por manifiesto; no se alteran originales.


<!-- ¤adpa/ -->

## Situación técnica al registrar
<!-- ¤adpa -->

Base del PR: `origin/main` en 3c22394, tras integrar el PR #156. DIAG-01, RAT-01 y MTGE-01 figuran hechas; este registro conserva esos cierres. Persistencia del diagnóstico ya existe; falta comprobar migración/operación en el entorno de aceptación. MTGE se calcula por servidor; integrar su motor no publica el resto de reglas jurídicas.

RM-19 está bloqueada por decisión del propietario: banco de 80 preguntas, sin correspondencia inventada con P1-P73 del plan. Biblioteca no crea IDs de requisitos, brechas o acciones para rellenar vacíos. PLA-01 lee el plan canónico; RAT conserva actividades e IDs y escritura del coordinador.


<!-- ¤adpa/ -->

## Reparto y orden
<!-- ¤adpa -->

| Etapa | Requisitos | Asignación |
| :--- | :--- | :--- |
| Entrega 1 | BIB-101…108 | BL-83 prepara BIB-105 → BIB-108; resto sin asignar |
| Entrega 2 | BIB-201…208 | Sin asignar; depende de salida E1 y contratos de fuentes |
| Entrega 3 | BIB-301…307 | Sin asignar; depende de E2 y relaciones reales con plan/brechas |

BL-83 es un bloque secuencial, una rama/PR por task, no dos tareas paralelas. La tanda 19 del reparto es una posición de coordinación, no una fecha ni una orden de lanzamiento. No cambiar estados a en_curso hasta que se encomiende implementar.

Dependencias relevantes: BIB-101 espera FE-17 por la propiedad del dashboard/store; esta espera FE-14 y DIAG-01. No añadir una modificación al dashboard mientras otras tareas lo poseen sin esa dependencia. BIB-105 y BIB-108 pueden prepararse sin tocarlo.


<!-- ¤adpa/ -->

## Primer bloque concreto BL-83
<!-- ¤adpa -->

Declaración resuelta: Biblioteca figura en PRD §7.1 como sala planificada y las 23 fichas tienen adscripción definitiva a Biblioteca y sus áreas colaboradoras. El parche provisional se aplicó documentalmente y se retira del PR; no se ha creado la compuerta ni código funcional. El responsable técnico autorizó esta corrección, sin autorizar implementación.

La validación usa el mapa local conforme a GOB-01 y tests/test_vpa_map.py: los rastros existentes se conservan y ¤niif18 se registra como capacidad ya existente. El preflight remoto utiliza un catálogo incompleto respecto al repositorio y no se presenta como certificación de este proyecto. Los encabezados del PRD quedan anclados con el rastro existente ¤adpa.

1. BIB-105 define modelos, esquema editorial y permisos, compuerta y puntos de extensión; administración editorial. Sus decisiones humanas son editores, revisores y reglas de publicación. Por defecto se deniega publicación si no se han definido.
2. Tras integrar BIB-105, BIB-108 incorpora manifiesto e importador reproducible con verificación sin escritura, checksums, apertura e idempotencia. Los ocho archivos quedan en revisión.

La lista exacta de escritura y el árbitro están en cada ficha y en el brief. Ningún archivo de código de esa lista se crea en esta sesión de planificación. No se crea rama de implementación ni se ejecuta migración.


<!-- ¤adpa/ -->

## Contratos entre tareas y propiedad compartida
<!-- ¤adpa -->

- BIB-105 crea `biblioteca_service.py` y reserva secciones con el ID de cada task. Las tareas siguientes editan solo su sección y sus archivos privados. Crear toda la compuerta es propiedad de la raíz; todos los consumidores dependen transitivamente de ella.
- BIB-101 crea BibliotecaWorkspace con secciones reservadas de composición para el resto y un registro de vistas por código. Los componentes y clientes de cada task se conectan solo en su sección; no se reescribe el workspace completo desde varias tareas independientes.
- BIB-105 proporciona el cliente HTTP común; usa autenticación existente y errores reales. Biblioteca no toma los fallbacks demostrativos de api.ts como datos verificados.
- BIB-201 define contratos de edición y validación con puntos explícitos para el guardado condicional de BIB-207 y renderizado por ficha de BIB-208. Esas tareas no necesitan editar borradores.py ni el editor de la primera: los contratos deben aceptar esos adaptadores desde su creación.
- BIB-205 define un modelo de salida y un puerto de trabajo/generación; BIB-206 lo usa para preview, BIB-207 para ejecución/idempotencia y BIB-208 para ocho mapas. No escribir la misma implementación desde tareas paralelas.
- BIB-105 incluye metadatos editoriales y estructuras base; documentos/revisiones privados se implementan en BIB-106, borradores en BIB-201, snapshots en BIB-205, trabajos en BIB-207 y revisión/aprobación en BIB-301. No duplicar entidades; se amplían en migraciones sucesivas.
- RLS real por tenant y validación de ambos extremos en enlaces; claves compuestas cuando corresponda. Catálogo global solo se escribe con capacidad editorial explícita, nunca por ser admin de una empresa.
- Si una integración exige extender persistencia de otra sala fuera de propiedad, preparar antes una ampliación coordinada de la ficha y reparto; no ignorar el campo ni simularlo para dar aceptación.


<!-- ¤adpa/ -->

## Puertas humanas y operativas
<!-- ¤adpa -->

No se resuelven automáticamente: permisos editoriales y autoridad delegada; revisión de ocho maestros; fuentes/reglas jurídicas; proveedor de análisis y cuarentena; límite 10 MB actual frente a objetivo de 20 MB; motores DOCX/recálculo XLSX y compatibilidad Office; política de conservación/bloqueo y RPO/RTO.

E1 no sale sin acceso aislado, publicación controlada y escaneo real de archivos externos. E2 no sale sin ocho esquemas/salidas compatibles y completos; E3 no sale con mocks de brechas/acciones ni IDs inventados. LIA/RIE/ESC y otras plantillas planificadas no se ofrecen como archivos existentes: faltantes quedan explícitos o se vinculan a evidencia externa autorizada.

El servidor tiene ejemplos de roles/funciones distintos de las fichas: no convertir DPO en ejecutor. La aprobación documental no implica ejecución, evidencia suficiente ni eficacia. Estado completada del plan no equivale sin revisión a verificada eficaz.


<!-- ¤adpa/ -->

## Adaptaciones editoriales obligatorias
<!-- ¤adpa -->

AVI-01: finalidades repetibles, sin límite de dos. PRO-01: políticas por derecho/rol; campos de solicitud solo en anexo. EIPD-00: respuesta y evidencia por criterio, sin suma de casillas. INV/RAT/LEG: referencias reales, validación por tenant, contactos y finalidades estructurados. PLA: IDs y datos del plan, fecha de corte, R/S calculadas con motor probado. Generados de uso sin ejemplos, instrucciones, variables pendientes o bloques no aplicables; guía separada, fuentes pertinentes conservadas. Borradores incompletos claramente marcados.


<!-- ¤adpa/ -->

## Verificación de este registro
<!-- ¤adpa -->

Comandos de gobernanza: `python scripts/generar_indice_tareas.py --escribir`, después `--verificar`; `python scripts/verificar_reparto.py`. Pruebas puras existentes: `python -m pytest --noconftest -p no:cacheprovider tests/test_indice_tareas.py tests/test_reparto.py` (sin conftest de DB).

Los árbitros de cada ficha son obligaciones para implementación futura; crear las fichas no los ejecuta ni acredita RLS, generación o despliegue. Las pruebas de mutación especifican el defecto que debe detectar cada árbitro, no resultados ya observados. No se fabrica certificado del arnés ni se cambian tests para aceptar este reparto.


<!-- ¤adpa/ -->

## Registro de tareas
<!-- ¤adpa -->

| ID | Entrega | Fuente | Dependencias técnicas |
| :--- | :--- | :--- | :--- |
| [BIB-101](../tareas/BIB-101.md) | 1 | Contexto y acceso | BIB-105, FE-17, FE-10, FE-19, ORG-09 |
| [BIB-102](../tareas/BIB-102.md) | 1 | Catálogo y búsqueda | BIB-101, BIB-108 |
| [BIB-103](../tareas/BIB-103.md) | 1 | Ficha de plantilla | BIB-102 |
| [BIB-104](../tareas/BIB-104.md) | 1 | Descarga controlada | BIB-103 |
| [BIB-105](../tareas/BIB-105.md) | 1 | Administración editorial | ORG-00, ORG-09, QA-04, RM-00 |
| [BIB-106](../tareas/BIB-106.md) | 1 | Documentos externos del cliente | BIB-101, BIB-104 |
| [BIB-107](../tareas/BIB-107.md) | 1 | Documentos por empresa | BIB-106 |
| [BIB-108](../tareas/BIB-108.md) | 1 | Migración e inventario inicial | BIB-105 |
| [BIB-201](../tareas/BIB-201.md) | 2 | Formulario por versión | BIB-107, BIB-108 |
| [BIB-202](../tareas/BIB-202.md) | 2 | Reutilización y procedencia | BIB-201, DIAG-01, RAT-01 |
| [BIB-203](../tareas/BIB-203.md) | 2 | Tablas de captura | BIB-201, BIB-202 |
| [BIB-204](../tareas/BIB-204.md) | 2 | Aplicabilidad explicable | BIB-202, MTGE-01 |
| [BIB-205](../tareas/BIB-205.md) | 2 | Generación de Word y Excel | BIB-201, BIB-202, BIB-203 |
| [BIB-206](../tareas/BIB-206.md) | 2 | Vista previa y fidelidad | BIB-205 |
| [BIB-207](../tareas/BIB-207.md) | 2 | Concurrencia y trabajos de generación | BIB-205 |
| [BIB-208](../tareas/BIB-208.md) | 2 | Cobertura de ocho fichas | BIB-203, BIB-204, BIB-206, BIB-207, RM-19 |
| [BIB-301](../tareas/BIB-301.md) | 3 | Revisión y aprobación | BIB-107, BIB-208 |
| [BIB-302](../tareas/BIB-302.md) | 3 | Integración con acciones | BIB-301, RM-19 |
| [BIB-303](../tareas/BIB-303.md) | 3 | Evidencias y verificación | BIB-302 |
| [BIB-304](../tareas/BIB-304.md) | 3 | Actualización normativa y documental | BIB-105, BIB-301, NOTIF-01 |
| [BIB-305](../tareas/BIB-305.md) | 3 | Indicadores verificables | BIB-303 |
| [BIB-306](../tareas/BIB-306.md) | 3 | Historial y conservación | BIB-303 |
| [BIB-307](../tareas/BIB-307.md) | 3 | Aceptación de extremo a extremo | BIB-304, BIB-305, BIB-306, TEST-03 |

<!-- ¤adpa/ -->
