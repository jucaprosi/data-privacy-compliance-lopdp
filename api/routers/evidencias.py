"""Enrutador REST para la Sala ADPA: Evidencias y Custodia Criptográfica.

Contrato de integridad: el SHA-256 del documento se envía en ``sha256_hash`` (calculado
en el cliente; el archivo no sale del equipo) o el servidor lo calcula desde
``contenido_texto``. Un hash precalculado nunca se vuelve a hashear.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from api.dependencies import obtener_tenant_id_actual
from features.evidencias.evidencias_service import (
    CONTROL_ID_MAX,
    CONTROL_ID_MIN,
    NORMATIVA_POR_DEFECTO,
    TIPO_MIME_POR_DEFECTO,
    CodigoDuplicado,
    ControlFueraDeRango,
    EvidenciaNoEncontrada,
    EvidenciaRegistro,
    NivelCalidadEvidencia,
    calcular_hash_sha256,
    es_sha256_valido,
    listar_evidencias_tenant,
    normalizar_sha256,
    registrar_evidencia_deduplicada,
    verificar_hash,
    vincular_controles,
)

router = APIRouter(prefix="/evidencias", tags=["Evidencias y Custodia Criptográfica"])

PATRON_SHA256 = r"^[0-9a-fA-F]{64}$"
ControlId = Annotated[int, Field(ge=CONTROL_ID_MIN, le=CONTROL_ID_MAX)]


# ---------------------------------------------------------------- modelos de entrada


class RegistrarEvidenciaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre_archivo: str = Field(..., min_length=1, description="Nombre del archivo o documento")
    sha256_hash: Optional[str] = Field(
        None,
        description="SHA-256 del documento ya calculado por el cliente (64 hex). Se guarda tal cual, en minúsculas.",
    )
    contenido_texto: Optional[str] = Field(
        None,
        description="Contenido textual para que el servidor calcule el SHA-256 (UTF-8). Si llega junto a sha256_hash deben coincidir.",
    )
    contenido_texto_o_hash: Optional[str] = Field(
        None,
        json_schema_extra={"deprecated": True},
        description=(
            "OBSOLETO: usar sha256_hash o contenido_texto. Si el valor tiene forma de SHA-256 "
            "(64 hex) se trata como hash precalculado; en otro caso como texto a hashear."
        ),
    )
    codigo: Optional[str] = Field(
        None, description="Código nemotécnico opcional; si se omite se asigna EVD-AAAA-NNNN correlativo"
    )
    normativa: str = Field(NORMATIVA_POR_DEFECTO, min_length=1, description="Marco normativo (por defecto LOPDP)")
    controles_vinculados: list[ControlId] = Field(
        default_factory=list, description=f"Ids de control del assessment ({CONTROL_ID_MIN}..{CONTROL_ID_MAX})"
    )
    tamano_bytes: Optional[int] = Field(None, ge=0, description="Tamaño del documento en bytes")
    tipo_mime: str = Field(TIPO_MIME_POR_DEFECTO, min_length=1, description="Tipo MIME del documento")
    storage_path: str = Field("", description="Ruta o URI de almacenamiento (vacío si el archivo no sale del equipo)")
    calidad: NivelCalidadEvidencia = NivelCalidadEvidencia.E1_DOCUMENTADA
    propietario_id: str = Field("", description="Usuario custodio de la evidencia")
    fecha_vigencia: Optional[date] = None

    _hash_resuelto: str = PrivateAttr(default="")

    @field_validator("sha256_hash")
    @classmethod
    def _validar_sha256(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        if not es_sha256_valido(valor):
            raise ValueError("sha256_hash debe tener exactamente 64 caracteres hexadecimales")
        return normalizar_sha256(valor)

    @field_validator("normativa", "tipo_mime")
    @classmethod
    def _recortar(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("no puede estar vacío")
        return limpio

    @model_validator(mode="after")
    def _resolver_hash(self) -> "RegistrarEvidenciaRequest":
        candidatos: list[tuple[str, str]] = []
        if self.sha256_hash is not None:
            candidatos.append(("sha256_hash", self.sha256_hash))
        if self.contenido_texto is not None:
            candidatos.append(("contenido_texto", calcular_hash_sha256(self.contenido_texto.encode("utf-8"))))
        legado = self.contenido_texto_o_hash
        if legado is not None and legado != "":
            if es_sha256_valido(legado):
                candidatos.append(("contenido_texto_o_hash", normalizar_sha256(legado)))
            else:
                candidatos.append(("contenido_texto_o_hash", calcular_hash_sha256(legado.encode("utf-8"))))
        if not candidatos:
            raise ValueError("Debe enviarse sha256_hash o contenido_texto para asegurar la integridad")
        distintos = {h for _, h in candidatos}
        if len(distintos) > 1:
            campos = ", ".join(c for c, _ in candidatos)
            raise ValueError(f"Conflicto de integridad: los valores de {campos} no producen el mismo SHA-256")
        self._hash_resuelto = candidatos[0][1]
        return self

    @property
    def hash_resuelto(self) -> str:
        return self._hash_resuelto

    def tamano_resuelto(self) -> int:
        if self.tamano_bytes is not None:
            return self.tamano_bytes
        texto = self.contenido_texto
        if texto is None and self.contenido_texto_o_hash and not es_sha256_valido(self.contenido_texto_o_hash):
            texto = self.contenido_texto_o_hash
        return len(texto.encode("utf-8")) if texto is not None else 0


class ActualizarVinculosRequest(BaseModel):
    agregar: list[ControlId] = Field(default_factory=list, description="Controles a vincular")
    quitar: list[ControlId] = Field(default_factory=list, description="Controles a desvincular")


# ---------------------------------------------------------------- modelos de salida


class EvidenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    codigo: str
    nombre_archivo: str
    sha256_hash: str
    storage_path: str
    calidad: NivelCalidadEvidencia
    fecha_vigencia: date
    propietario_id: str
    controles_vinculados: list[int]
    normativa: str
    tamano_bytes: int
    tipo_mime: str
    created_at: datetime


class RegistrarEvidenciaResponse(BaseModel):
    status: str = "SUCCESS"
    duplicada: bool
    evidencia: EvidenciaOut


class ListarEvidenciasResponse(BaseModel):
    tenant_id: str
    total: int
    evidencias: list[EvidenciaOut]


class EvidenciaResponse(BaseModel):
    status: str = "SUCCESS"
    evidencia: EvidenciaOut


class VerificacionResponse(BaseModel):
    sha256_hash: str
    coincide: bool
    evidencia: Optional[EvidenciaOut] = None


def _a_salida(evidencia: EvidenciaRegistro) -> EvidenciaOut:
    return EvidenciaOut.model_validate(evidencia, from_attributes=True)


# ---------------------------------------------------------------- endpoints


@router.post("", response_model=RegistrarEvidenciaResponse)
def registrar_evidencia(
    payload: RegistrarEvidenciaRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> RegistrarEvidenciaResponse:
    """Registra una evidencia con su SHA-256. Si el documento ya existe para el tenant y la
    normativa, devuelve la evidencia existente con ``duplicada: true``."""
    evidencia = EvidenciaRegistro(
        tenant_id=tenant_id,
        codigo=(payload.codigo or "").strip(),
        nombre_archivo=payload.nombre_archivo,
        sha256_hash=payload.hash_resuelto,
        storage_path=payload.storage_path,
        calidad=payload.calidad,
        propietario_id=payload.propietario_id,
        controles_vinculados=list(payload.controles_vinculados),
        normativa=payload.normativa,
        tamano_bytes=payload.tamano_resuelto(),
        tipo_mime=payload.tipo_mime,
        **({"fecha_vigencia": payload.fecha_vigencia} if payload.fecha_vigencia else {}),
    )
    try:
        guardada, duplicada = registrar_evidencia_deduplicada(evidencia)
    except CodigoDuplicado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RegistrarEvidenciaResponse(duplicada=duplicada, evidencia=_a_salida(guardada))


@router.get("", response_model=ListarEvidenciasResponse)
def listar_evidencias(
    normativa: Optional[str] = Query(None, description="Filtra por marco normativo"),
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> ListarEvidenciasResponse:
    """Obtiene el catálogo de evidencias auditables de la organización."""
    filtro = normativa.strip() if normativa and normativa.strip() else None
    evidencias = listar_evidencias_tenant(tenant_id, filtro)
    return ListarEvidenciasResponse(
        tenant_id=tenant_id, total=len(evidencias), evidencias=[_a_salida(e) for e in evidencias]
    )


@router.get("/verificar/{sha256}", response_model=VerificacionResponse)
def verificar_evidencia(
    sha256: str = Path(..., pattern=PATRON_SHA256, description="SHA-256 (64 hex) a verificar"),
    normativa: Optional[str] = Query(None, description="Restringe la búsqueda a un marco normativo"),
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> VerificacionResponse:
    """Verifica si un SHA-256 coincide con alguna evidencia registrada del tenant."""
    normalizado = normalizar_sha256(sha256)
    filtro = normativa.strip() if normativa and normativa.strip() else None
    encontrada = verificar_hash(tenant_id, normalizado, filtro)
    return VerificacionResponse(
        sha256_hash=normalizado,
        coincide=encontrada is not None,
        evidencia=_a_salida(encontrada) if encontrada is not None else None,
    )


@router.patch("/{evidencia_id}/vinculos", response_model=EvidenciaResponse)
def actualizar_vinculos_evidencia(
    payload: ActualizarVinculosRequest,
    evidencia_id: str = Path(..., min_length=1),
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> EvidenciaResponse:
    """Vincula y/o desvincula controles del assessment (1..80). Quitar tiene prioridad."""
    try:
        evidencia = vincular_controles(
            tenant_id, evidencia_id, list(payload.agregar), list(payload.quitar)
        )
    except EvidenciaNoEncontrada as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada") from exc
    except ControlFueraDeRango as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EvidenciaResponse(evidencia=_a_salida(evidencia))
