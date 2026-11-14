# Propuesta de adopción ligera de TOGAF en EVYDENTIA
`¤sdd` `¤adpa` `¤arbitro`

Autor: Arquitecto ADPA. Fecha: 2026-11-13. Estado: propuesta, pendiente de decisión del CTO.

## 1. Qué se propone

Adoptar TOGAF (The Open Group Architecture Framework) como **marco de referencia**, no como proceso nuevo. TOGAF pide un ciclo de arquitectura (ADM), un repositorio de arquitectura y una gobernanza que compruebe que lo construido cumple lo decidido. El proyecto ya tiene casi todo eso con otros nombres. La propuesta es nombrar esa correspondencia, cubrir los tres huecos reales y no añadir documentos que nadie mantenga.

Regla de entrada: cada pieza nueva tiene un árbitro exógeno (prueba, script o CI). Una pieza sin árbitro no entra.

## 2. Correspondencia con lo que ya existe

| Fase o pieza de TOGAF | Qué pide | Qué tenemos hoy |
| :--- | :--- | :--- |
| Preliminar | principios, marco, roles | `governance/DOCTRINAS.md`, `AGENTS.md`, flujo CTO → Arquitecto → UX/UI → Tech Lead |
| A · Visión | alcance, partes interesadas, objetivos | PRD de EVYDENTIA (`governance/artefactos/PRD.md`) |
| B · Negocio | capacidades, procesos, normativa | LOPDP y su reglamento, fuentes en `FUENTES_Y_BIBLIOGRAFIA.md`, invariantes de negocio |
| C · Datos y aplicaciones | modelo de datos, aplicaciones e interfaces | salas ADPA, pasillos `app_core/pasillo/`, migraciones Alembic, RLS por organización |
| D · Tecnología | plataforma | programa RET (plataforma única en GCP), `deploy-gcp.yml` |
| E · Oportunidades y soluciones | paquetes de trabajo | fichas TOML en `governance/tareas/` |
| F · Plan de migración | orden y dependencias | `depende_de` de las fichas, tandas, una sola cabeza de Alembic |
| G · Gobernanza de la implementación | comprobar que se construye lo diseñado | especificaciones SDD, `verificar_especificaciones.py`, árbitros ADPA, revisión del Arquitecto y fusión del CTO |
| H · Gestión del cambio | decidir cambios de arquitectura | decisiones del CTO anotadas en las especificaciones y en `governance/partes/` |
| Gestión de requisitos (centro del ADM) | trazar requisitos | sección 6 de cada especificación, `INVARIANTS.md` |
| Repositorio de arquitectura | dónde vive todo | `governance/` |

## 3. Huecos reales

1. **Decisiones de arquitectura dispersas.** Están en especificaciones, partes y mensajes entre chats. No hay un registro único que diga qué se decidió, por qué y qué lo sustituye. TOGAF lo pide en la fase H y en el repositorio.
2. **Sin mapa de capacidades.** No hay una vista que una cada capacidad de negocio de la LOPDP (consentimiento, derechos ARCO, RAT, EIPD, brechas, DPO) con la sala que la implementa. Hoy cuesta ver qué capacidad no tiene sala o tiene dos.
3. **Principios sin árbitro.** Varios principios de `DOCTRINAS.md` no tienen una prueba que los haga cumplir.

## 4. Lo que se añadiría

| Pieza | Dónde | Árbitro |
| :--- | :--- | :--- |
| Registro de decisiones de arquitectura (ADR): un archivo por decisión con contexto, decisión, consecuencias y estado (`vigente`, `sustituida por ADR-n`) | `governance/arquitectura/decisiones/ADR-NNN.md` | prueba que exige los campos, que cada `sustituida por` apunte a un ADR que existe y que cada especificación que cite «decisión del CTO» enlace un ADR |
| Mapa de capacidades: tabla capacidad → artículos de la LOPDP → sala → fichas | `governance/arquitectura/CAPACIDADES.md` | prueba que comprueba que cada sala listada existe en `features/` y que toda sala de `features/` aparece en el mapa |
| Principios con árbitro: cada principio enlaza la prueba que lo hace cumplir, o se marca como «sin árbitro» para eliminarlo o cubrirlo | `governance/DOCTRINAS.md` (columna nueva) | prueba que falla si un principio no enlaza un archivo de prueba existente ni lleva la marca |

No se adoptan: la certificación, el Enterprise Continuum completo, las matrices de partes interesadas ni los entregables formales por fase. Para un equipo de este tamaño serían documentos sin dueño.

## 5. Orden propuesto

1. **ARQ-01 · Registro de ADR.** Plantilla, la prueba y los primeros ADR retroactivos con las decisiones del CTO de 2026-11-12 y 2026-11-13 (cuatro ojos en RM-27, hojas anteriores con etiqueta, instantánea de SEC-24, plataforma única del programa RET).
2. **ARQ-02 · Mapa de capacidades.** Con su prueba de cobertura. Lo revisa el DPO por la parte normativa.
3. **ARQ-03 · Principios con árbitro.** Repasa `DOCTRINAS.md`; los principios que queden sin árbitro van a decisión del CTO.

Cada una es una ficha de gobernanza, solo documentos y pruebas, sin código de producto ni migraciones. Pueden ir en una misma tanda (regla del PR de gobernanza por tanda).

## 6. Costo y riesgo

- Costo: tres fichas pequeñas y, después, un ADR por cada decisión nueva del CTO.
- Riesgo principal: que el registro de ADR se quede atrás. Lo cubre la prueba que obliga a enlazar un ADR desde toda especificación que cite una decisión.
- No cambia el flujo de trabajo ni el formato de las especificaciones.

## 7. Decisión que se pide al CTO

Aprobar o no las tres fichas ARQ-01 a ARQ-03. Si se aprueban, el Arquitecto escribe sus especificaciones SDD y el Tech Lead las reparte.

## 8. Fuentes

- The Open Group, *The TOGAF Standard, 10th Edition* (2022): Architecture Development Method, Architecture Repository y Architecture Governance.
- Michael Nygard, «Documenting Architecture Decisions» (2011), origen del formato ADR.
