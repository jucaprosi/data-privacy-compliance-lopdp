# Diseño de seguridad de los portales externos — EVYDENTIA
`¤seguridad` `¤portales-externos`

> **Estado: borrador para revisión de la propietaria (SEC-12, BL-100).** Es solo diseño: no hay código, rutas públicas ni fichas de implementación. Nada de lo descrito está implementado ni verificado en ejecución.
> **Origen:** conflicto D-7 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` (superficie pública nueva sin diseño de seguridad). **Consumidoras:** `DER-02` (portal de solicitudes de titulares) y `TER-02` (portal del encargado/proveedor); ambas dependen de este documento y lo citan en su árbitro.

## 0. Cómo leer las fuentes

- **Fuente técnica verificada:** la página oficial se leyó el 2026-10-28 y lo afirmado coincide con lo leído. Va con su URL.
- **(\*) por verificar:** base legal sin texto oficial leído en esta sesión (LEG-03). **No se cita ningún artículo de memoria**; donde hace falta, el control dice «base legal (\*)» y LEG-03 aporta el artículo literal.
- **Parámetro propuesto:** cifra elegida por este diseño (p. ej. límites de tasa). No es norma; la propietaria la aprueba y se registra como parámetro configurable, no como texto fijo.
- Doctrinas citadas: las del PRD §1 (7 = copiloto con DLP preventivo, 8 = privacidad por diseño, minimización y aislamiento multi-tenant).

### Fuentes técnicas leídas (2026-10-28)

| Clave | Fuente | URL |
| :-- | :-- | :-- |
| NIST-63B | NIST SP 800-63B-4, *Authentication and Authenticator Management* (§3.2.2 limitación de intentos; §3.1.2 secretos de consulta; verificadores fuera de banda) | https://pages.nist.gov/800-63-4/sp800-63b.html |
| OWASP-FP | OWASP *Forgot Password Cheat Sheet* | https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html |
| OWASP-IDOR | OWASP *Insecure Direct Object Reference Prevention Cheat Sheet* | https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html |
| OWASP-LOG | OWASP *Logging Cheat Sheet* | https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html |
| OWASP-UP | OWASP *File Upload Cheat Sheet* | https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html |
| WCAG-338 | W3C WCAG 2.2, criterio 3.3.8 *Accessible Authentication (Minimum)*, nivel AA | https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html |
| PG-RLS | PostgreSQL, *Row Security Policies* | https://www.postgresql.org/docs/current/ddl-rowsecurity.html |

**No verificado:** la numeración exacta de la subsección de NIST-63B sobre verificadores fuera de banda (la página no la mostró; se cita solo la sección 3.2.2 y 3.1.2, que sí aparecieron); el catálogo de amenazas automatizadas de OWASP (la página del proyecto no lista las entradas; no se cita por nombre).

## 1. Superficies y activos

| Superficie | Quién entra | Qué hace | Tarea consumidora |
| :-- | :-- | :-- | :-- |
| P1 · Portal de solicitudes de titulares | Persona no autenticada, por organización | Crea una solicitud de derechos; consulta su estado | DER-02 |
| P2 · Portal del encargado/proveedor | Contacto del proveedor con enlace enviado por la organización | Responde un cuestionario y sube evidencias | TER-02 |

**Activos a proteger:** datos de contacto y descripción del titular; solicitudes de otros titulares; datos de la organización (más allá de su nombre); evidencias subidas por el proveedor; el registro de auditoría; la disponibilidad del equipo interno (bandeja de solicitudes sin ruido).

**Confianza:** todo lo que llega por estas superficies es entrada no confiable. La identidad y la organización nunca salen del cuerpo de la petición: salen del slug resuelto por el servidor (P1) o del token (P2).

## 2. Amenazas (STRIDE resumido)

| # | Amenaza | Superficie | Control que la cubre |
| :-- | :-- | :-- | :-- |
| A1 | Suplantación: alguien presenta una solicitud o consulta el estado haciéndose pasar por el titular | P1 | §3 |
| A2 | Adivinar o enumerar códigos de seguimiento, tokens, slugs u organizaciones | P1, P2 | §4, §5 |
| A3 | Reutilizar un enlace filtrado (correo reenviado, historial, registros de proxy) | P2, P1 | §4 |
| A4 | Lectura cruzada: ver solicitudes, respuestas o evidencias de otro titular u otra organización | P1, P2 | §5, §8 |
| A5 | Inundar la bandeja con solicitudes falsas; agotar almacenamiento o cola con subidas | P1, P2 | §6 |
| A6 | Subir malware, archivos con datos personales de terceros o bases completas | P2 | §9, §10 |
| A7 | Escalada: llegar con un token público a rutas o datos internos | P1, P2 | §5, §8 |
| A8 | Repudio: negar haber enviado o recibido; borrar rastros | P1, P2 | §7 |
| A9 | Fuga por el propio registro (IP, correos, tokens en claro en los logs) | todas | §7, §9 |
| A10 | Mensajes de error o tiempos de respuesta que revelan si un dato existe | P1, P2 | §5 |
| A11 | Un rol de base de datos con `BYPASSRLS` o dueño de tabla sin `FORCE` anula el aislamiento | todas | §8 |

## 3. Verificación proporcional de la identidad del titular (P1)

**Principio:** el esfuerzo de verificar es proporcional a lo que el portal entrega. El portal **no entrega datos personales**: solo recibe la solicitud y devuelve estado y fechas (DER-02 R2). Por eso la verificación se hace en dos niveles, y el segundo lo hace la organización, no el portal.

| Nivel | Qué ocurre | Qué se exige | Qué se expone |
| :-- | :-- | :-- | :-- |
| N0 · Recepción | El portal recibe derecho, nombre, correo y descripción y devuelve un código | Prueba de control del correo opcional por enlace de un solo uso (§4); sin documentos | Solo el código y un acuse genérico |
| N1 · Seguimiento | Consulta del estado con el código | Posesión del código (≥ 128 bits, §4) | `estado`, `recibida_en`, `respondida_en`; nunca contenido ni respuesta |
| N2 · Entrega de la respuesta | La organización responde por un canal propio | Verificación de identidad **a cargo de la organización**, proporcional al dato entregado; el portal no entrega la respuesta | Nada adicional en el portal |

Decisiones del diseño:

1. **El portal nunca pide copia de cédula ni documentos de identidad.** Pedirlos contradice la minimización (Doctrina 8) y crearía una base sensible. Si la organización necesita acreditar identidad, lo pide fuera del portal; la plataforma solo registra que se hizo y cuándo (sin copiar el documento).
2. **Confirmación del correo** (doble verificación) antes de que la solicitud llegue a la bandeja: reduce suplantación y ruido (A1, A5). Parámetro propuesto: el enlace de confirmación caduca a las 24 h; sin confirmar, la solicitud se descarta sin quedar en la bandeja interna.
3. **Respuesta uniforme:** el acuse es el mismo exista o no el correo en otro registro de la organización (A10; OWASP-FP: mismo mensaje y tiempos consistentes).
4. **Representantes** (menores, apoderados): quedan fuera del portal; se tramitan por la organización (decisión abierta, §13).

**Fuentes:** proporcionalidad y control de posesión: NIST-63B (limitación de intentos §3.2.2; secretos de consulta de un solo uso §3.1.2) — aplica por analogía, el portal no es un servicio de autenticación fuerte. **Base legal** de la obligación de atender solicitudes de derechos, de verificar la identidad antes de entregar datos y del plazo de respuesta: (\*) por verificar (LEG-03; hoy sin texto oficial leído). El plazo no se fija aquí (D-9).

## 4. Enlaces que caducan y de un solo uso (P1 confirmación, P2 token)

| Regla | Diseño | Fuente |
| :-- | :-- | :-- |
| Generación | Aleatoriedad criptográfica del servidor; ≥ 32 bytes para tokens de P2 (coincide con TER-02 R1) y ≥ 128 bits para el código de seguimiento de P1 | OWASP-FP (CSPRNG, longitud suficiente contra fuerza bruta) |
| Almacenamiento | Solo el **hash** en base de datos (`token_hash`, `codigo_seguimiento_hash`); el valor en claro se muestra una vez | OWASP-FP remite a almacenamiento seguro; el hash es decisión de este diseño |
| Caducidad | Enlace de confirmación de P1: 24 h (parámetro). Token de P2: `dias_vigencia` elegido por la organización con **máximo configurable** (propuesta: 30 días). Caducado ⇒ no se reactiva: la organización emite otro | OWASP-FP (caducidad apropiada); NIST-63B fija tope de 10 min para códigos fuera de banda de autenticación, valor que no se adopta aquí porque el enlace de P2 no autentica un usuario sino una tarea larga (justificación del diseño) |
| Un solo uso | Se consume al **completarse la acción** (confirmar correo; enviar el cuestionario), no al abrirlo. Abrirlo intercambia el token por una **sesión corta de portal** (cookie `HttpOnly`, ámbito solo del cuestionario) para que el asistente de varios pasos de FE-23 no consuma el enlace con el primer GET | OWASP-FP (invalidar tras uso); NIST-63B §3.1.2 (un secreto de consulta se usa con éxito una sola vez) |
| Intentos fallidos | Contados por token y por IP; superado el tope, el token se deshabilita. Generar un enlace nuevo **no reinicia** la cuenta de fallos | NIST-63B §3.2.2 (tope máximo de 100 fallos; los límites menores son válidos) y regla de no reinicio por regeneración |
| Código de seguimiento (P1) | No caduca mientras la solicitud esté abierta, pero es de solo lectura y solo da estado y fechas; se invalida a los 90 días de cerrada (propuesta) | parámetro propuesto |
| Dónde viaja | En ruta o fragmento, nunca en parámetros que se registren; `Referrer-Policy: no-referrer` y `Cache-Control: no-store` en estas páginas | (\*) por verificar la cabecera exacta contra documentación oficial (no leída en esta sesión) |
| Revocación | La organización puede revocar un enlace; la revocación es inmediata y queda en auditoría (§7) | decisión de diseño |

**Inconsistencia detectada en TER-02 (a corregir antes de implementar, no aquí):** la especificación devuelve 410 para token «caducado o ya respondido» y 404 para «desconocido (idéntico al caducado)». Un 410 distinto del 404 le dice a un atacante qué tokens existieron (A2, A10). El diseño exige una **única respuesta** para desconocido, caducado, usado y revocado (404 con el mismo cuerpo y tiempo; OWASP-IDOR: mismo 404 para inexistente y no accesible). La interfaz puede mostrar «el enlace ya no es válido, pida uno nuevo a la organización» sin distinguir la causa.

## 5. Ninguna exposición de datos de otros titulares ni de otras organizaciones

| Regla | Diseño | Fuente |
| :-- | :-- | :-- |
| Autorización por objeto | Cada petición verifica que el objeto pertenece al token o código presentado; el identificador solo no basta | OWASP-IDOR (autorizar cada petición sobre un objeto; identificadores aleatorios no sustituyen el control) |
| Alcance por consulta | Toda consulta se filtra por `tenant_id` **y** por el objeto del token; no existe consulta «por id» sin ese par | OWASP-IDOR (consultar solo dentro de los datos del usuario) |
| Identidad del token | La organización y el objeto se derivan del token en el servidor, jamás del cuerpo ni de la URL | OWASP-IDOR (usar la identidad de la sesión, no ids de la URL) |
| Sin enumeración | 404 idéntico (cuerpo y tiempo) para slug inexistente, inactivo, código ajeno o token inválido; sin listados públicos de organizaciones; el slug no es autoincremental ni derivable del nombre legal | OWASP-IDOR (404 igual para inexistente e inaccesible); OWASP-FP (respuesta uniforme) |
| Contenido mínimo de respuesta | P1 seguimiento: `estado`, `recibida_en`, `respondida_en`. P2: nombre de la organización y preguntas (TER-02 R3). Ningún campo interno (`respuesta_sha256`, hallazgos, otros terceros) | PRD Doctrina 8 |
| Errores | Mensajes genéricos; sin trazas, sin nombres de tablas, sin distinguir causas | OWASP-FP |
| Funciones privilegiadas | Las funciones `SECURITY DEFINER` previstas por DER-02/TER-02 para resolver slug o token devuelven **solo** `tenant_id` y estado; su dueño no es un rol con `BYPASSRLS` y fijan `search_path` (ver §8) | PG-RLS (los dueños de tabla y los roles con `BYPASSRLS` omiten la seguridad por filas) |
| Pruebas | Para cada ruta pública, una prueba con dos organizaciones y dos titulares que falla si una respuesta contiene un dato del otro; mutación: quitar el filtro ⇒ la prueba cae | OWASP-IDOR (probar con varias cuentas) |

**Base legal** de no revelar datos a quien no es el titular o su representante y del deber de confidencialidad: (\*) por verificar (LEG-03).

## 6. Límites de abuso y CAPTCHA o alternativa accesible

**Capas, de menos a más intrusiva** (se aplica la primera que baste):

1. **Tasa por IP y por ruta** (contador en Redis, como prevé DER-02 R4). Valores iniciales propuestos: creación de solicitud 5 por IP y hora (ya en DER-02); consulta de seguimiento 30 por IP y hora; confirmación de correo 10 por IP y hora; intentos de token inválido 10 por IP y hora.
2. **Tasa por destino**: máximo de solicitudes por correo y por organización y día, para que nadie use el portal como bomba de correo hacia un tercero (A5). Parámetro propuesto: 3 por correo y día, 50 por organización y día antes de pasar a revisión manual.
3. **Tamaño y forma**: cuerpos acotados (la descripción de P1 ya está limitada a 4.000 caracteres en DER-02); subidas de P2 con tope por archivo y por cuestionario (TER-02 fija 10 MB por archivo; se añade tope por cuestionario).
4. **Campo trampa** (honeypot) y tiempo mínimo de envío, sin fricción para personas.
5. **Desafío de bot solo si la señal lo pide**: tras superar la capa 1 o al detectar patrón automático. No se muestra por defecto.
6. **Cortacircuitos por organización**: si una organización recibe una ráfaga anómala, el portal pasa a «solicitudes en revisión» y avisa a la persona administradora; no se cae el portal de otras organizaciones.

**CAPTCHA y accesibilidad (WCAG-338, nivel AA):** el criterio prohíbe exigir una prueba de función cognitiva en la autenticación salvo que haya alternativa, ayuda, reconocimiento de objetos o contenido personal. Por tanto:

- No se usa un desafío de texto distorsionado, rompecabezas ni cálculo como único camino.
- Si se adopta un desafío, debe ofrecer **al menos una alternativa sin prueba cognitiva** (p. ej. enlace de confirmación al correo, o presentar la solicitud por un canal no web de la organización) y declararla en la propia página.
- El reconocimiento de objetos está exceptuado en AA pero no en AAA (WCAG-338); se evita como camino único.
- El proveedor de desafío (propio o tercero) se elige en una tarea aparte; **no se decide aquí** y debe revisarse su política de datos antes de contratarlo (el desafío de un tercero transmite IP y huella del navegador: tema de transferencia, §13). WCAG-338 aplica estrictamente a la autenticación; extenderlo al formulario público es decisión de diseño (accesibilidad, no obligación verificada).

**Base legal** de accesibilidad de la interfaz para personas con discapacidad: (\*) por verificar (LEG-03).

## 7. Registro de auditoría

**Qué se registra** (OWASP-LOG): creación de solicitud o cuestionario; confirmación de correo; apertura/intercambio de token; subida de archivo y resultado del DLP; consumo, caducidad, revocación y reemisión de enlaces; fallos de validación, de autorización y excesos de tasa; cambios de configuración del portal (activar, slug, texto); acciones de la organización sobre lo recibido (asignar, responder, cerrar).

**Qué NO se registra en claro** (OWASP-LOG): el token o código completos (solo un prefijo de 6–8 caracteres del hash o un identificador interno), el contenido de la descripción, las respuestas o los archivos. La IP se guarda **truncada o con hash con sal rotada** (decisión de minimización; el período de conservación está pendiente, D-12). El correo se guarda en la solicitud, no se repite en el log.

**Integridad:** el rol de la aplicación `lopdp_app` solo tiene `SELECT` e `INSERT` sobre las tablas de auditoría (`INV_LOPDP_AUDIT_LOG_APPEND_ONLY`, RM-14); cada fila lleva el hash de la anterior para detectar borrado o alteración (OWASP-LOG: detección de manipulación); los eventos del portal usan formato estructurado y se sanean CR/LF y longitud (OWASP-LOG: inyección en logs).

**Qué se exige al servicio:** que cada evento lleve `tenant_id`, momento, tipo de evento, resultado y un identificador de correlación; que una prueba confirme que un token de entrada **no aparece** en ninguna fila ni línea de log.

**Base legal** del deber de poder demostrar el cumplimiento y plazo de conservación de este registro: (\*) por verificar (LEG-03; la conservación sigue pendiente de confirmación legal, D-12).

## 8. Aislamiento por organización (RLS, sin `BYPASSRLS`)

Fuente: PG-RLS — los superusuarios y los roles con atributo `BYPASSRLS` **siempre** omiten la seguridad por filas; el dueño de una tabla la omite salvo que se use `ALTER TABLE … FORCE ROW LEVEL SECURITY`.

| Control | Diseño |
| :-- | :-- |
| Rol de la aplicación | Las rutas públicas se atienden con `lopdp_app`, **sin** `BYPASSRLS` y sin ser dueño de las tablas. Una prueba consulta `pg_roles` y falla si `rolbypassrls` es verdadero para ese rol o para el dueño de las funciones públicas |
| Tablas por organización | `ENABLE` **y** `FORCE ROW LEVEL SECURITY`, políticas con `USING` y `WITH CHECK` por `tenant_id`, permisos mínimos de `lopdp_app` (patrón de DER-02 y TER-02) |
| Resolución sin sesión de organización | Una petición pública no tiene tenant en el token. Se resuelve con una función `SECURITY DEFINER` mínima (slug→`tenant_id`; token o código→`tenant_id` y estado). Requisitos: dueño sin `BYPASSRLS`; `search_path` fijado; `EXECUTE` solo para `lopdp_app`; devuelve solo lo imprescindible; sin SQL dinámico. Después se **fija el tenant en la sesión de base de datos** y todo lo demás pasa por RLS |
| Portal por tenant | Cada petición pública termina con el tenant restablecido; no hay conexión compartida que arrastre el tenant anterior (prueba de dos peticiones seguidas de organizaciones distintas) |
| Sala `plataforma` | No accede a datos de ningún tenant (D-11); no se usa para atender estos portales |
| Pruebas | Contra una rama Neon de revisión propia, nunca producción: una prueba con `lopdp_app` que intenta leer filas de otro tenant y obtiene cero filas; mutación: quitar `FORCE` o dar `BYPASSRLS` ⇒ la prueba cae |

**Pendiente de comprobar (no verificado):** el comportamiento exacto de `SECURITY DEFINER` y de `FORCE` con el rol de Neon que usa el despliegue; se comprueba en la tarea de implementación contra la rama de revisión.

**Base legal** de las medidas técnicas de seguridad y de la separación de datos entre responsables: (\*) por verificar (LEG-03).

## 9. Datos mínimos (Doctrina 8)

| Dato | P1 | P2 | Regla |
| :-- | :-- | :-- | :-- |
| Derecho ejercido | sí | — | catálogo cerrado |
| Nombre | sí | — | texto libre acotado |
| Correo | sí | contacto del proveedor | necesario para confirmar y responder |
| Descripción | sí (≤ 4.000 caracteres) | — | se advierte «no incluya datos de otras personas ni documentos» |
| Teléfono, dirección, cédula, fecha de nacimiento | **no** | **no** | no se piden; si la organización los necesita, los pide por su canal (§3) |
| Adjuntos | **no** en la primera versión (DER-02 R1) | sí, evidencias del proveedor, con tope | solo del proveedor, nunca del titular |
| IP | truncada/con hash (§7) | ídem | para tasa y auditoría, con conservación acotada |
| Cookies | solo la de sesión de portal en P2 (`HttpOnly`) | ídem | sin rastreadores ni analítica de terceros en estas páginas |

El portal **no almacena bases de titulares ni documentos de identidad** (PRD Doctrina 8, D-6). Las páginas públicas no cargan scripts de terceros; los avisos de privacidad del portal enuncian qué se recoge y para qué, con el texto aprobado por la organización (contenido legal: (\*) por verificar, LEG-03 y dictamen del abogado). El portal de P2 muestra solo el nombre de la organización (TER-02 R3).

## 10. DLP en toda subida (Doctrina 7)

Aplica a la única subida prevista: evidencias del proveedor en P2 (y a cualquier adjunto que se habilite después en P1).

| Control | Diseño | Fuente |
| :-- | :-- | :-- |
| Lista blanca de tipos | Extensiones y tipos MIME permitidos definidos en un solo lugar del servidor (el que fija SEC-05); la interfaz ayuda, decide el servidor; validación del tipo real, no del encabezado | OWASP-UP (lista blanca de extensiones; validar el tipo real porque `Content-Type` lo controla el usuario) |
| Tamaño | Tope por archivo y por cuestionario (propuesta: 10 MB por archivo, como TER-02; tope por cuestionario por decidir) | OWASP-UP (límites de tamaño) |
| Nombre | Se regenera en el servidor (identificador aleatorio); el nombre original se guarda como metadato saneado | OWASP-UP (regenerar el nombre) |
| Almacenamiento | Fuera de la raíz web, bucket privado, sin listado, descarga solo por URL firmada y de corta vida para personal interno autorizado | OWASP-UP (almacenar fuera de la raíz web / en otro host) |
| Antivirus | Escaneo posterior a la subida con estado «pendiente de análisis» y cuarentena hasta resultado; el proveedor lo decide SEC-05 | OWASP-UP (antivirus / sandbox, CDR); SEC-05 |
| **DLP** | Antes de que el archivo sea visible al personal: detección de patrones de datos personales (cédula, correo masivo, tablas con muchas filas de personas) y resultado en uno de tres estados: `limpio`, `advertido` (se avisa y exige confirmación), `bloqueado` (se rechaza). Una subida con aspecto de **base de datos de titulares** se bloquea (Doctrina 8). El resultado se audita sin copiar el contenido (§7) | PRD Doctrina 7 y 8, D-6 («DLP en toda subida»); técnica concreta (\*) por verificar: no se ha leído ninguna norma o guía de DLP en esta sesión |
| Límite de lo que ve el proveedor | El proveedor ve y reemplaza solo sus propios archivos del cuestionario; no hay listado de otros | OWASP-IDOR |
| Autenticación de la subida | La sesión de portal de P2 (§4) autoriza la subida; sin sesión válida no hay subida | OWASP-UP (exigir autorización para subir) |

**Dependencia:** el filtro DLP del copiloto (Doctrina 7) y el de subidas deben compartir motor y reglas, no duplicarse; se decide en la tarea de implementación (propuesta abajo).

**Base legal** del deber de minimizar y de no tratar datos innecesarios: (\*) por verificar (LEG-03).

## 11. Matriz de controles y verificación

| Control | Árbitro propuesto (para la tarea de implementación) |
| :-- | :-- |
| §3 identidad proporcional | prueba: el portal no pide ni guarda documentos de identidad; el acuse es idéntico para correos conocidos y desconocidos |
| §4 enlaces | pruebas: token caducado, usado, revocado y desconocido dan **la misma** respuesta; el token no aparece en logs; regenerar no reinicia fallos |
| §5 sin exposición | pruebas con dos organizaciones y dos titulares; mutación: quitar el filtro de objeto |
| §6 abuso | prueba de tasa (la sexta solicitud desde una IP responde 429); prueba de que el desafío tiene alternativa sin prueba cognitiva |
| §7 auditoría | prueba: `lopdp_app` no puede `UPDATE` ni `DELETE`; el evento existe y no contiene datos del titular |
| §8 RLS | prueba contra rama Neon: `rolbypassrls` falso, `FORCE` activo, lectura cruzada con cero filas |
| §9 mínimo | prueba: el esquema público rechaza campos fuera del catálogo |
| §10 DLP | prueba: un CSV con cédulas simuladas queda `bloqueado`; un PDF limpio queda `limpio`; el rechazo se audita |

Cada prueba debe fallar si el control falta (una prueba que pasa con el control quitado no cuenta; regla común de BRIEFS_POR_BLOQUE).

## 12. Tareas de implementación que abriría (sin fichas todavía)

Orden sugerido; ninguna se abre sin que la propietaria apruebe este diseño. Las dos consumidoras (DER-02, TER-02) ya existen y ya dependen de SEC-12.

1. **Base común de portal público** (`app_core`): tokens y códigos (generación, hash, caducidad, consumo, revocación, no reinicio de fallos), respuesta uniforme 404, sesión corta de portal.
2. **Límites de abuso**: tasa por IP, destino y organización en Redis; cortacircuitos por organización; cabeceras `no-store` y `no-referrer` (tras verificar su fuente).
3. **Desafío de bot accesible**: elección de proveedor con revisión de datos y alternativa sin prueba cognitiva (decisión de la propietaria).
4. **Auditoría de portales**: tablas append-only con cadena de hash y saneamiento; prueba de ausencia de tokens en logs.
5. **Aislamiento por RLS para rutas públicas**: funciones `SECURITY DEFINER` mínimas, prueba de `rolbypassrls` y `FORCE`, fijado de tenant por petición (compartida por DER-02 y TER-02).
6. **DLP y validación de subidas de P2**: lista blanca, nombre regenerado, bucket privado, estados `limpio/advertido/bloqueado`, enlace con el antivirus que fije SEC-05.
7. **Prueba transversal de no exposición** (dos organizaciones × dos titulares) para ambos portales.
8. **Corrección de TER-02** para unificar 404/410 (ajuste de especificación) y de DER-02 para añadir confirmación de correo y los límites de §6.
9. **Revisión legal (LEG-03)**: artículos literales para los (\*) de §3 a §10, aviso de privacidad del portal y dictamen del abogado sobre el texto público.
10. **Revisión de accesibilidad** de las dos páginas públicas con el criterio WCAG-338 y teclado/lector de pantalla (Playwright más revisión manual).

## 13. Decisiones abiertas para la propietaria

1. Valores de §4 y §6 (vigencias, topes de tasa): ¿los aprueba como parámetros iniciales?
2. ¿Confirmación de correo obligatoria en P1? (el diseño la recomienda; añade un paso al titular).
3. Proveedor del desafío de bot, o canal alternativo sin desafío para el lanzamiento.
4. Representantes legales y menores: ¿fuera del portal?
5. Conservación de IP y del registro de auditoría (D-12, pendiente de confirmación legal).
6. Si un desafío de un tercero se considera transferencia de datos: pasa por LEG-03.
7. ¿P1 admite adjuntos en una fase posterior? Hoy no (DER-02 R1); cambiaría §3, §9 y §10.

## 14. Qué no se verificó

- Todas las bases legales (§3 a §10): marcadas (\*); sin artículo ni texto oficial leído (LEG-03).
- Numeración exacta de la subsección de NIST-63B para verificadores fuera de banda; la cifra de 10 minutos de ese apartado se leyó en la página pero su sección no se pudo confirmar, por eso solo se usa como contraste y no como regla.
- Las cabeceras `Referrer-Policy` y `Cache-Control` y cualquier norma de DLP: sin fuente leída.
- Comportamiento de `SECURITY DEFINER`/`FORCE`/`BYPASSRLS` con el rol real de Neon del despliegue.
- Ninguna prueba ejecutada: el documento es diseño.
