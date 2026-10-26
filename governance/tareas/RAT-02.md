+++
id = "RAT-02"
titulo = "Plantilla sectorial de salud: el RAT arranca de un catálogo de establecimientos de salud"
ola = "D"
estado = "hecha"
sala = "rat, frontend"
depende_de = ["RAT-01", "DIAG-01", "ENT-02", "RM-00"]
propiedad = ["features/rat/domain/plantillas/salud.json", "features/rat/services/plantilla_engine.py", "features/rat/rat_service.py#RAT-02", "api/routers/rat_plantillas.py", "main.py#RAT-02", "tests/test_rat_plantilla_salud.py", "frontend/src/components/modules/rat/PlantillaSectorial.tsx", "frontend/src/components/modules/RatModule.tsx", "frontend/tests/rat/plantilla.spec.ts"]
arbitro = "pytest tests/test_rat_plantilla_salud.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/rat; prueba de mutación documentada"
rastros = ["¤rat", "¤diagnostico"]
+++

# RAT-02 · Plantilla sectorial de salud

**Fuente.** Matrices de trabajo del equipo consultor en la carpeta compartida SALUDATA (Google Drive): «MATRIZ_RAT_Consultorio_Medico_SALUDATA» (25 actividades típicas de un consultorio con finalidad, datos, titulares, base legal, área, soporte, encargados, conservación y medidas) y «Matriz_Diagnostico_Centro_Medico_Pequeno_SALUDATA» (50 preguntas con evidencia, acción y responsable sugerido). Ambas se declaran **borrador consultivo** que debe validar el consultor y, cuando corresponda, un profesional legal.

**Requisito previo del propietario:** autorización de los autores para incorporar el contenido al producto y validación jurídica de bases legales y plazos de conservación antes de publicarla.

## Entrega
- `salud.json`: las 25 actividades como plantilla, cada base legal y plazo marcado «sugerido, validar» con la fuente normativa que cita la matriz. Sin datos de pacientes.
- Si la ficha organizacional indica sector salud, el coordinador ve «Cargar plantilla de salud» (el DPO consulta, no modifica el RAT: SoD, art. 48 LOPDP): elige qué actividades aplican y se crean en el RAT (RAT-01) con `origen = "plantilla:salud"`, editables. Nunca se cargan sin confirmación.
- Cada actividad lleva el **actor sugerido** (gerencia, administración, médico responsable, TI o proveedor, recepción, consultor), base para el área de las tareas (ORG-12).
- Pruebas: la plantilla es válida contra el modelo; cargar una selección crea exactamente esas actividades; cargarla dos veces no duplica; una organización de otro sector no ve la opción.
- **Prueba de mutación documentada:** quitar la comprobación de duplicados y comprobar que una prueba falla.

## Límites
- Solo el sector salud. Otros sectores, con su propia fuente, son otras tareas.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.

## Autorización y correcciones del coordinador al completar (2026-10-25)
- **Autorización:** el autor de las matrices SALUDATA es miembro del equipo y dio autorización expresa para incorporarlas, según confirmó el propietario el 2026-10-25. Sigue pendiente la **validación jurídica** de bases legales y plazos: se cargan como «sugerido, validar» y la advertencia queda en las observaciones de cada actividad.
- `salud.json` (generado por el agente) se contrastó con la matriz original: 25 actividades con los mismos nombres; conserva el texto original de base legal y conservación y su fuente.
- La plantilla la carga solo el **coordinador** (mismos permisos que RAT-01; el DPO recibe «Violación SoD»). Sector: el texto libre de la ficha organizacional que contenga «salud».
- La tabla del RAT no tiene restricción de código único: el motor evita duplicar las actividades ya cargadas desde la plantilla (`omitidas`).
- `RatModule.tsx` entra en la propiedad para montar el componente. El router se registra solo (`AUTO_REGISTRO`); `main.py` no cambia.
- **Hallazgo para otra tarea:** `getActividadesRAT` en `frontend/src/lib/api.ts` devuelve actividades inventadas si el servidor falla (mismo patrón que MTGE-01 retiró en la calculadora).
