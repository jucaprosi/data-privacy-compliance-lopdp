# Registro auditable del proceso de reestructuración del Copiloto LOPDP 360

`¤¤qa-engineer`

## Alcance y límite del documento

Este documento registra el procedimiento técnico, lógico, lingüístico y de validación usado para implementar la solicitud anterior sobre el Copiloto de LOPDP 360. Se construye a partir de evidencia observable: requisitos del usuario, archivos inspeccionados, cambios conservados en el repositorio, comandos ejecutados, errores encontrados y resultados de pruebas.

No contiene razonamiento interno privado, texto oculto de deliberación ni cadenas de pensamiento. Es una reconstrucción completa y reproducible de las entradas, reglas, decisiones verificables, acciones y resultados que permiten auditar la solución sin depender de información privada del modelo.

## Solicitud que se procesó

La reestructuración respondió a estos requisitos funcionales:

1. Eliminar el botón **Plan de mis brechas**.
2. Sustituir el menú **Consulta general o todas las brechas** por un casillero de búsqueda capaz de encontrar una brecha por número o descripción, por ejemplo `22` o `revocatoria del consentimiento`.
3. Agregar un menú **Estado** con las opciones **Por iniciar**, **Implementación** y **Seguimiento**.
4. Hacer que la IA priorice la brecha y el estado seleccionados al formular la respuesta.
5. Redactar las respuestas como un profesor de secundaria: lenguaje claro, conceptos necesarios explicados y pasos cortos y ordenados.
6. Analizar y reestructurar el flujo completo, evitando una modificación superficial aislada.

## Precondiciones y gobierno del trabajo

Antes de modificar código se aplicó el triaje obligatorio definido por `AGENTS.md` mediante `mcp_orchestrate_triage`, con la raíz absoluta del proyecto y la solicitud del usuario. El triaje clasificó el trabajo como una modificación técnica de Rama 2 y asignó el rol operativo `¤¤qa-engineer`.

La precondición de trabajo fue:

\[
C = \text{“la solicitud está comprendida, el repositorio está disponible y el triaje fue ejecutado”}
\]

El contrato de ejecución se representó como:

\[
(C \Rightarrow S) \land ((C \land S) \Rightarrow \neg I)
\]

donde:

- \(C\) es la precondición anterior.
- \(S\) es la solución implementada y verificada.
- \(I\) es una intervención que contradiga el contrato o deje una regresión conocida.

También se conservaron estas restricciones del proyecto:

- No superar 500 líneas físicas por archivo de producción.
- Mantener la separación de módulos ADPA y evitar imports laterales indebidos.
- Ejecutar el arnés físico `ejecutar_arnes_tres_pilares.bat`.
- Cerrar la sesión técnica mediante `mcp_close_session` con evidencia verificable.

## Inspección del sistema existente

La inspección se hizo por búsquedas de texto y lecturas dirigidas, evitando recorrer archivos irrelevantes. Se localizaron los componentes de interfaz, tipos compartidos, modelos del dominio, servicio de implementación, proveedor externo y pruebas.

Los archivos principales examinados fueron:

- `frontend/src/components/copilot/CopilotWorkspace.tsx`
- `frontend/src/components/copilot/AssessmentCopilotActions.tsx`
- `frontend/src/components/copilot/CopilotPlan.tsx`
- `frontend/src/types/copilot.ts`
- `frontend/src/lib/copilotClient.ts`
- `features/ai_copilot/domain/assistant_models.py`
- `features/ai_copilot/services/implementation_assistant.py`
- `features/ai_copilot/services/assistant_provider.py`
- `features/ai_copilot/ai_copilot_service.py`
- `tests/test_ai_copilot.py`
- `tests/test_implementation_assistant_provider.py`

La arquitectura encontrada ya tenía un circuito de consulta, sanitización, obtención de fundamentos locales, proveedor DeepSeek opcional, respaldo local y validación de la respuesta. Por eso la reestructuración amplió ese circuito de extremo a extremo en vez de crear un segundo flujo paralelo.

## Descomposición funcional

La solicitud se dividió en seis responsabilidades comprobables:

1. **Selección de brecha:** convertir el antiguo selector general en búsqueda textual y numérica.
2. **Selección de estado:** representar el momento del proceso del usuario mediante un conjunto cerrado de tres valores.
3. **Contrato de transporte:** enviar brecha y estado desde React hasta FastAPI.
4. **Validación de dominio:** rechazar estados desconocidos y brechas que no estén en el conjunto remitido.
5. **Priorización semántica:** cambiar el foco de la explicación según el estado.
6. **Estilo didáctico:** aplicar instrucciones consistentes tanto al proveedor externo como al respaldo local.

Esta separación permitió verificar cada responsabilidad sin duplicar la lógica legal ni alterar el sistema de auditoría existente.

## Proceso lógico y matemático

### Normalización de la búsqueda

Para que la búsqueda por descripción no dependa de mayúsculas ni tildes, se usa una función conceptual de normalización:

\[
N(s) = \operatorname{lower}(\operatorname{stripDiacritics}(s))
\]

Si \(q\) es el texto escrito y \(B\) el conjunto de brechas disponibles, las coincidencias se calculan como:

\[
M(q) = \{b \in B \mid N(\operatorname{id}(b)) \supseteq N(q) \lor N(\operatorname{control}(b)) \supseteq N(q)\}
\]

La interfaz limita la presentación a las primeras seis coincidencias:

\[
M_6(q) = \operatorname{take}(M(q), 6)
\]

Con ello, `22` puede encontrar la brecha cuyo `pregunta_id` contiene ese número, y una frase puede encontrar coincidencias en el nombre del control.

### Selección de la brecha prioritaria

Sea \(p\) el identificador opcional elegido. El subconjunto procesado por el asistente es:

\[
S(B,p) = \{b \in B \mid p = \varnothing \lor \operatorname{id}(b)=p\}
\]

El modelo de dominio añade una invariante: si \(p\) existe, debe pertenecer a los identificadores de las brechas enviadas.

\[
p \neq \varnothing \Rightarrow p \in \{\operatorname{id}(b):b\in B\}
\]

Así se evita priorizar una brecha inexistente o ajena al contexto de la consulta.

### Dominio cerrado del estado

El estado se modeló como un tipo enumerado:

\[
E = \{\text{Por iniciar},\text{Implementación},\text{Seguimiento}\}
\]

La validación de FastAPI/Pydantic rechaza cualquier valor fuera de \(E\). La interfaz TypeScript usa la misma unión literal, de modo que frontend y backend comparten el mismo contrato.

### Función de priorización

El estado se transforma en un enfoque mediante la función:

\[
F(e)=
\begin{cases}
\text{pasos iniciales y responsables}, & e=\text{Por iniciar}\\
\text{ejecución y evidencias}, & e=\text{Implementación}\\
\text{control, medición y mejora}, & e=\text{Seguimiento}
\end{cases}
\]

La pregunta del usuario conserva prioridad contextual, pero el estado determina qué parte del plan debe recibir mayor atención.

### Proyección mínima al proveedor

El contexto externo se construye como una proyección controlada del estado interno:

\[
P(x)=\{\text{pregunta saneada},\text{brechas necesarias},\text{guías legales locales},\text{prioridad de usuario}\}
\]

La prioridad añadida tiene esta estructura:

```json
{
  "brecha_id": 21,
  "estado": "Implementación",
  "instruccion": "Prioriza este estado al explicar el plan."
}
```

No se incorporó el historial completo al contexto del proveedor. La reestructuración mantuvo la proyección mínima ya prevista por la arquitectura.

### Invariantes de respuesta

La respuesta externa no sustituye el fundamento legal local. Se mantiene el principio de que los identificadores y fundamentos citados deben pertenecer al corpus y a las guías recuperadas por la aplicación:

\[
\operatorname{CitasRespuesta} \subseteq \operatorname{CitasContextoLocal}
\]

El resultado final conserva los planes y fundamentos locales como fuente estructural, mientras el proveedor mejora el enfoque y la explicación dentro del contexto permitido.

## Proceso informático de extremo a extremo

El flujo implementado es el siguiente:

```text
Diagnóstico terminado
        ↓
Catálogo de brechas disponible en React
        ↓
Usuario busca por número o descripción
        ↓
Usuario selecciona una brecha y un estado
        ↓
CopilotWorkspace construye ConsultaCopiloto
        ↓
copilotClient envía POST /api/v1/ai_copilot/consulta
        ↓
FastAPI y Pydantic validan brecha_id y estado
        ↓
implementation_assistant sanea y filtra el contexto
        ↓
Se recuperan planes y fundamentos legales locales
        ↓
Se crea prioridad_usuario con brecha y estado
        ↓
DeepSeek responde si está configurado
        ↓
Si no está disponible, se usa el respaldo normativo local
        ↓
Se validan y combinan la explicación y la estructura local
        ↓
React muestra la respuesta, fundamentos, evidencias y seguimiento
```

### Construcción de la consulta en frontend

`CopilotWorkspace.tsx` mantiene dos nuevos estados de interfaz:

- Texto de búsqueda de brecha.
- Estado de implementación seleccionado.

Al enviar, construye un objeto con `pregunta`, `brechas`, `historial`, `estado` y, cuando existe selección, `brecha_id`. Al cambiar de alcance o reiniciar la sesión, restablece la búsqueda y el estado a **Por iniciar**.

### Búsqueda y selección

El antiguo menú general se eliminó. En su lugar, un campo de búsqueda filtra el catálogo actual de brechas. Los resultados se muestran como opciones seleccionables con identificador y descripción. La selección se guarda como `brecha_id` y permanece visible para que el usuario sepa cuál se priorizará.

### Estado de implementación

El selector **Estado** presenta exactamente tres opciones. La selección viaja en todas las consultas. Cuando el usuario inicia una pregunta de seguimiento desde un plan ya mostrado, la interfaz cambia automáticamente el estado a **Seguimiento** porque ese acto corresponde a revisar una implementación existente.

### Acción contextual desde el assessment

Se eliminó la acción global **Preparar plan de mis brechas**. La acción específica **Cómo resolverla** se conserva porque opera sobre una brecha concreta. Ahora esa acción selecciona la brecha y prepara la pregunta para que el usuario pueda ajustar estado o texto antes del envío.

### Validación del backend

`ConsultaAsistente` incorporó:

- `brecha_id`, entero opcional dentro del rango admitido.
- `estado`, unión literal con valor predeterminado **Por iniciar**.
- Validación cruzada para comprobar que la brecha seleccionada está incluida en las brechas del payload.

La sanitización reconstruye el modelo conservando ambos campos. Esto evita que los datos de prioridad se pierdan entre la entrada del API y la llamada al proveedor.

### Construcción de la respuesta

`implementation_assistant.py` filtra los planes por `brecha_id`, calcula el enfoque mediante `enfoque_por_estado` y crea `prioridad_usuario` para el proveedor. Si DeepSeek entrega contenido válido, se usa su enfoque dentro de la estructura controlada. Si no, el servicio genera una explicación local determinista.

El respaldo local incluye:

- Una introducción didáctica.
- La prioridad y el estado.
- El objetivo del control.
- Pasos de implementación.
- Evidencias esperadas.
- Criterio de cierre.
- Seguimiento.
- Fundamento legal proveniente del corpus local.

## Proceso lingüístico

El estilo solicitado se convirtió en reglas explícitas, no en una expectativa implícita.

### Reglas aplicadas al proveedor

La instrucción del sistema en `assistant_provider.py` ordena actuar como un buen profesor de secundaria y aplicar estas pautas:

1. Usar palabras sencillas antes que jerga técnica.
2. Explicar solamente los conceptos jurídicos o de proceso necesarios.
3. Presentar pasos cortos, concretos y ordenados.
4. Priorizar la brecha y el estado indicados en el contexto.
5. Mantener los fundamentos legales suministrados por la aplicación.
6. Evitar inventar artículos o fuentes fuera del corpus controlado.

### Reglas aplicadas al respaldo local

El generador local se ajustó para que la claridad no dependa de DeepSeek. Cada plan empieza con una explicación directa de qué se va a resolver, declara la prioridad y el estado, y organiza las acciones en una secuencia comprensible.

La composición lingüística sigue este patrón:

```text
Situación → objetivo → pasos → evidencias → criterio de cierre → seguimiento → fundamento legal
```

Este orden responde a una progresión pedagógica: primero ubica al usuario, después explica qué debe hacer, luego muestra cómo demostrarlo y finalmente indica cómo comprobar que la brecha permanece cerrada.

### Tratamiento de términos

Los términos legales se conservan cuando son necesarios, pero se acompañan de una explicación operativa. La redacción evita convertir una cita legal en la totalidad de la respuesta; el artículo funciona como fundamento de las acciones propuestas.

## Cambios por archivo

### `frontend/src/components/copilot/CopilotWorkspace.tsx`

- Eliminó la acción **Plan de mis brechas**.
- Añadió estado React para búsqueda y estado de implementación.
- Implementó normalización sin tildes y búsqueda por ID o descripción.
- Limitó la lista visible a seis coincidencias.
- Añadió el selector **Estado**.
- Envía `brecha_id` y `estado` al backend.
- Cambia a **Seguimiento** cuando se formula una pregunta posterior sobre un plan.
- Actualizó el texto de ayuda para explicar el nuevo flujo.

### `frontend/src/components/copilot/AssessmentCopilotActions.tsx`

- Eliminó la acción global de planificación.
- Conservó la acción contextual por brecha.
- Cambió esa acción para preparar la consulta y selección antes de enviarla.

### `frontend/src/types/copilot.ts`

- Extendió `ConsultaCopiloto` con `brecha_id` opcional.
- Añadió el estado obligatorio como unión literal de los tres valores admitidos.

### `features/ai_copilot/domain/assistant_models.py`

- Añadió `brecha_id` con restricciones numéricas.
- Añadió `estado` como `Literal` cerrado.
- Incorporó la validación cruzada del identificador seleccionado.

### `features/ai_copilot/services/implementation_assistant.py`

- Conservó brecha y estado durante la sanitización.
- Filtró los planes por la brecha seleccionada.
- Añadió la función de enfoque por estado.
- Añadió `prioridad_usuario` al contexto mínimo.
- Adaptó la respuesta local al tono didáctico y al estado.

### `features/ai_copilot/services/assistant_provider.py`

- Añadió reglas de profesor de secundaria al prompt del proveedor.
- Indicó que la brecha y el estado deben guiar la prioridad de la explicación.

### `tests/test_ai_copilot.py`

- Verificó que **Seguimiento** sea aceptado.
- Verificó que un estado fuera del dominio, como `Cerrado`, sea rechazado.
- Hizo determinista la prueba del respaldo local, aislándola de una clave DeepSeek real del ambiente.
- Ajustó la prueba de estado del proveedor para comprobar coherencia con la configuración activa.

### `tests/test_implementation_assistant_provider.py`

- Verificó el transporte del estado **Implementación**.
- Verificó que `prioridad_usuario` contenga la brecha y el estado elegidos.
- Conservó las verificaciones que impiden exponer la clave del proveedor.

## Incidencias encontradas y correcciones

### Conflicto de contexto en una edición inicial

Una edición extensa no coincidió exactamente con el contexto actual de uno de los archivos y fue rechazada. Como no se aplicó parcialmente, no dejó un estado intermedio. La modificación se dividió en cambios más pequeños y verificables, cada uno aplicado sobre el contenido real del archivo.

### Prueba de estado dependiente del ambiente

La primera ejecución dirigida produjo 12 pruebas aprobadas y 1 fallida. La prueba esperaba que la inferencia externa estuviera deshabilitada, pero el ambiente real tenía DeepSeek configurado. La expectativa se corrigió para comprobar coherencia entre los campos del estado, independientemente de si el proveedor está activo.

Después de esa corrección, el conjunto dirigido obtuvo 13 pruebas aprobadas.

### Prueba local que podía invocar DeepSeek

La primera ejecución completa del arnés obtuvo 183 pruebas aprobadas y 1 fallida. La prueba que esperaba el texto del respaldo local estaba heredando la clave DeepSeek del ambiente, por lo que entraba legítimamente en el flujo externo.

La corrección no alteró el código de producción. La prueba pasó a:

- Redirigir temporalmente la ruta del archivo de entorno.
- Eliminar `DEEPSEEK_API_KEY` mediante `monkeypatch` durante ese caso.
- Restaurar automáticamente el ambiente al terminar.

Esto aisló el caso que pretende comprobar el respaldo local y evitó llamadas externas o consumo de crédito durante la prueba.

## Validación ejecutada

### Pruebas dirigidas

Se ejecutaron las pruebas del API y del proveedor del asistente. Resultado final:

```text
13 passed, 1 warning
```

### Comprobación TypeScript

Se ejecutó el compilador TypeScript con `--noEmit` para validar tipos sin generar archivos. Resultado: correcto.

### Arnés completo del proyecto

Se ejecutó físicamente:

```powershell
cmd /c ejecutar_arnes_tres_pilares.bat
```

Resultado final:

```text
Exit code: 0
184 tests passed, 21 warnings
Next.js 15.5.25 Turbopack production build: passed
UTF-8 sin BOM: passed
Huellas temporales abiertas: ninguna
```

Las advertencias no bloquearon la ejecución y el arnés terminó con código cero.

## Matriz de aceptación

| Requisito | Evidencia | Estado |
|---|---|---|
| Eliminar **Plan de mis brechas** | Acción retirada de `CopilotWorkspace.tsx` y `AssessmentCopilotActions.tsx` | Cumplido |
| Buscar por número | Comparación contra `pregunta_id` normalizado | Cumplido |
| Buscar por descripción | Comparación textual sin mayúsculas ni tildes | Cumplido |
| Agregar los tres estados | Unión TypeScript, `Literal` Python y selector visual | Cumplido |
| Priorizar brecha | `brecha_id`, filtrado de planes y `prioridad_usuario` | Cumplido |
| Priorizar estado | `enfoque_por_estado` y contexto externo | Cumplido |
| Tono de profesor de secundaria | Prompt externo y redacción local | Cumplido |
| Mantener fundamento legal | Guías y corpus locales conservados | Cumplido |
| Evitar regresiones | 184 pruebas y build de producción aprobados | Cumplido |

## Límites conocidos

- La búsqueda es léxica: encuentra coincidencias por número o fragmento de descripción; no es una búsqueda semántica por embeddings.
- Solo puede seleccionar brechas presentes en el catálogo recibido desde el assessment actual.
- El estado prioriza el contenido de la respuesta; no reemplaza por sí solo un sistema persistente de gestión de tareas.
- El estilo del proveedor generativo puede variar ligeramente, aunque está limitado por instrucciones explícitas. El respaldo local mantiene una estructura determinista.
- La exactitud jurídica depende del corpus normativo local y de sus versiones. La IA externa no se usa como fuente autónoma de artículos.

## Procedimiento de reproducción

1. Levantar backend y frontend del proyecto con su configuración habitual.
2. Completar un diagnóstico que genere al menos una brecha.
3. Abrir el Copiloto desde la vista de brechas.
4. Escribir un número válido en el buscador y seleccionar la coincidencia.
5. Repetir con un fragmento de descripción, incluyendo una consulta sin tildes.
6. Elegir **Por iniciar** y solicitar acciones; comprobar énfasis en pasos iniciales.
7. Elegir **Implementación** y repetir; comprobar énfasis en ejecución y evidencias.
8. Elegir **Seguimiento** y repetir; comprobar énfasis en control y mejora.
9. Revisar que la respuesta incluya fundamento legal del corpus local.
10. Ejecutar las pruebas dirigidas, `tsc --noEmit` y el arnés completo.

## Resultado observable

El Copiloto quedó integrado al flujo de brechas: el usuario busca una brecha concreta, indica el estado de trabajo y recibe una explicación didáctica que prioriza esa combinación. La respuesta conserva planes, evidencias, criterios de cierre y fundamentos legales controlados por la aplicación, con DeepSeek como proveedor opcional y un respaldo normativo local cuando no está disponible.
