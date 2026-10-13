# Boceto Arquitectónico: Sala ADPA Firma Electrónica con ANF (FIRMA-01)
`¤adpa` `¤firma-electronica` `¤seguridad`

> **Estado:** Boceto (Fase BBAP, paso 1 - Decisión de diseño D-4).  
> **Árbitro:** Aprobación del propietario (usuario humano). Sin proveedor real ni credenciales.

---

## 1. Contexto y Decisión Doctrinal D-4

En el marco de la **Ley de Comercio Electrónico, Firmas Electrónicas y Mensajes de Datos del Ecuador** y la **Ley Orgánica de Protección de Datos Personales (LOPDP)**, las evidencias documentales de cumplimiento ($E1+$ a $E3$), las actas de comités de privacidad y los dictámenes de diligencia del DPO requieren validez probatoria plena mediante firma electrónica avanzada o cualificada emitida por una entidad de certificación acreditada ante la **ARCOTEL** (Agencia de Regulación y Control de las Telecomunicaciones).

La Decisión **D-4** del plan maestro establece la selección de **ANF Autoridad de Certificación Ecuador** como entidad certificadora para el ecosistema JUBYS Plataforma LOPDP 360.

---

## 2. Límites y Filosofía BBAP (Paso 1)

Conforme a la metodología BBAP del proyecto (ver `governance/METODOLOGIAS.md`):
1. **Paso 1 (Boceto libre):** Define la arquitectura conceptual, los mamparos herméticos ADPA, los esquemas de intercambio y la interfaz de la compuerta pública sin acoplar librerías de terceros, credenciales secretas ni servicios externos en runtime.
2. **Paso 2 (Sellado):** Implementación determinista, integración de la API remota de ANF, pruebas con dobles de red y certificados de prueba en entorno acotado.

Este documento y los archivos en `features/firma_electronica/` constituyen la entrega completa y exclusiva del **Paso 1**.

---

## 3. Arquitectura Confinada ADPA

La sala `firma_electronica` se estructura como una sala hermética e independiente dentro del directorio `features/`:

```
features/firma_electronica/
├── __init__.py
├── firma_electronica_service.py   # Compuerta pública única de la sala
└── domain/
    ├── __init__.py
    └── models.py                   # Modelos de dominio y DTOs
```

### Invariantes de la Sala:
- **Cero Imports Cruzados Internos:** Ningún módulo fuera de `features/firma_electronica/` puede importar submódulos internos; toda interacción se realiza exclusivamente a través de `features/firma_electronica/firma_electronica_service.py`.
- **Invariante Multi-Tenant:** Toda solicitud y registro de firma asienta de forma obligatoria el `tenant_id` y el hash notarial SHA-256 del documento original.
- **Sellado Temporal TSA:** Los formatos objetivo corresponden a **PAdES-B-LTV** (Long-Term Validation) para PDFs y **XAdES-BES** para metadatos XML, incorporando marca de tiempo notarial (TSA).

---

## 4. Especificación de la Compuerta Pública (`firma_electronica_service.py`)

La compuerta expone:

- **Estructuras de datos:**
  - `FormatoFirma`: Enumeración de estándares normativos admitidos (`PAdES-BES`, `PAdES-B-LTV`, `XAdES-BES`).
  - `EstadoFirma`: Ciclo de vida (`borrador`, `pendiente_firma`, `firmado`, `rechazado`, `error_validacion`).
  - `CertificadoInfo`: Metadatos del certificado del titular (cédula, emisor acreditado por ARCOTEL, vigencia).
  - `DocumentoParaFirma`: Descriptor del activo documental a firmar (hash SHA-256, `tenant_id`, tamaño).
  - `ResultadoFirma`: Atestación notarial del documento firmado.

- **Funciones de compuerta:**
  - `boceto_firmar_documento_anf(documento, firmante_id, formato)`: Simulación determinista del proceso de firma.
  - `boceto_verificar_firma_anf(sha256_firmado)`: Validación conceptual de firma, vigencia y no revocación.

---

## 5. Próximos Pasos para Fase 2 (Paso 2 - Sellado)

1. Selección del canal de conexión con ANF (API REST Cloud Signing vs. agente local PKCS#11 / token criptográfico).
2. Definición del modelo relacional en PostgreSQL con RLS (`firmas_electronicas`, `transacciones_anf`).
3. Creación del router `api/routers/firma_electronica.py` con autoregistro.
4. Pruebas de integración con dobles de red que verifiquen el cumplimiento estricto de mamparos ADPA.
