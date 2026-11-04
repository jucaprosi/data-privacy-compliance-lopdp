# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Tablas de captura (BIB-203): filas de inventarios, RAT y LEG dentro de un borrador estructurado.

- El ID técnico lo pone el servidor; el `codigo` visible es único por organización y tabla.
- Pegar hasta 100 filas: primero una validación previa por fila (no escribe) y después una confirmación
  atómica: si una sola fila falla, no se guarda ninguna.
- Las referencias a tratamientos se comprueban contra el RAT de la organización de la sesión, que llega
  por `PuertoTratamientos` (lo arma el router con la compuerta RAT). Biblioteca no importa otras salas.
- Estas filas son datos del borrador: no crean un segundo RAT ni un segundo plan, ni son fuente validada.
- PLA es de solo lectura: se deriva del plan canónico y sus columnas calculadas no se editan. Una fecha
  inválida o ausente nunca aparece «En plazo».
"""
import json
import re
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

MAX_FILAS = 100
MAX_TEXTO = 2000
CODIGO = re.compile(r"^[A-Za-z0-9._-]{1,40}$")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
Tabla = Literal["INV", "RAT", "LEG"]

# Bases de legitimación del RAT (art. 7 LOPDP), como texto: Biblioteca no importa la sala RAT.
BASES = ("CONSENTIMIENTO", "OBLIGACION_LEGAL", "CUMPLIMIENTO_CONTRATO", "PROTECCION_INTERES_VITAL",
         "INTERES_LEGITIMO", "MISION_INTERES_PUBLICO")
CATEGORIAS = ("IDENTIFICATIVOS", "CONTACTO", "FINANCIEROS", "LABORALES", "SALUD", "BIOMETRICOS", "OTROS")
SOPORTES = ("DIGITAL", "PAPEL", "MIXTO")


# ¤adpa
@dataclass(frozen=True)
class Columna:
    clave: str
    etiqueta: str
    tipo: Literal["texto", "fecha", "catalogo", "tratamiento"] = "texto"
    obligatoria: bool = False
    catalogo: tuple[str, ...] = ()


ESQUEMAS: dict[str, tuple[Columna, ...]] = {
    "INV": (Columna("nombre", "Activo o base de datos", obligatoria=True),
            Columna("categoria", "Categoría de datos", "catalogo", True, CATEGORIAS),
            Columna("soporte", "Soporte", "catalogo", False, SOPORTES),
            Columna("tratamiento_id", "Tratamiento", "tratamiento"),
            Columna("fecha_revision", "Última revisión", "fecha")),
    "RAT": (Columna("actividad", "Actividad", obligatoria=True),
            Columna("base_legal", "Base de legitimación", "catalogo", True, BASES),
            Columna("tratamiento_id", "Tratamiento", "tratamiento"),
            Columna("fecha_inicio", "Inicio del tratamiento", "fecha")),
    "LEG": (Columna("norma", "Norma o fundamento", obligatoria=True),
            Columna("articulo", "Artículo"),
            Columna("base_legal", "Base de legitimación", "catalogo", True, BASES),
            Columna("tratamiento_id", "Tratamiento", "tratamiento", True)),
}

# Lee los tratamientos vigentes de la organización de la sesión (RAT-01, solo lectura): sus IDs.
PuertoTratamientos = Callable[[AsyncSession, str], Awaitable[Iterable[str]]]


# ¤adpa
class Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ¤adpa
class FilaEntrada(Contrato):
    codigo: str = Field(max_length=40)
    datos: dict[str, str] = Field(default_factory=dict)


# ¤adpa
class PegarFilas(Contrato):
    tabla: Tabla
    filas: list[FilaEntrada] = Field(max_length=MAX_FILAS)


# ¤adpa
class EditarFila(Contrato):
    datos: dict[str, str]
    revision: int = Field(ge=1)


# ¤adpa
class ResultadoFila(Contrato):
    indice: int
    codigo: str
    errores: list[str]


# ¤adpa
class Previa(Contrato):
    tabla: Tabla
    valida: bool
    filas: list[ResultadoFila]


# ¤adpa
class Fila(Contrato):
    id: str
    borrador_id: str
    tabla: Tabla
    codigo: str
    datos: dict[str, str]
    tratamiento_id: str | None
    revision: int
    actualizado_en: datetime


# ¤adpa
class FilaPlan(Contrato):
    """Fila de PLA, solo lectura: `estado` es calculado y ninguna columna es editable."""
    id: str
    titulo: str
    control_ref: str
    fecha_inicio: str | None
    fecha_fin: str | None
    estado: Literal["En plazo", "Vencida", "Completada", "Sin fecha válida"]
    editable: Literal[False] = False


LEER = ("SELECT id, borrador_id, tabla, codigo, datos, tratamiento_id, revision, actualizado_en "
        "FROM biblioteca_filas WHERE id=:id")
LEER_BLOQUEANDO = ("SELECT id, borrador_id, tabla, codigo, datos, tratamiento_id, revision, actualizado_en "
                   "FROM biblioteca_filas WHERE id=:id FOR UPDATE")


# ¤adpa
async def _fijar_contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": actor})


# ¤adpa
def _esquema(tabla: str) -> tuple[Columna, ...]:
    if tabla not in ESQUEMAS:  # PLA y cualquier otra: no se capturan aquí
        raise ErrorNegocio("BIB_FILA_TABLA_INVALIDA")
    return ESQUEMAS[tabla]


# ¤adpa
def fecha_real(valor: str) -> date | None:
    """Fecha ISO que existe en el calendario (rechaza 2026-02-30); None si no lo es."""
    if not isinstance(valor, str) or not FECHA.match(valor):
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


# ¤adpa
def validar_fila(tabla: str, fila: FilaEntrada, tratamientos: set[str]) -> tuple[dict[str, str], list[str]]:
    """Normaliza una fila y devuelve sus errores; sin errores, los datos son guardables."""
    columnas = {c.clave: c for c in _esquema(tabla)}
    errores: list[str] = []
    if not CODIGO.match(fila.codigo or ""):
        errores.append("codigo: usa de 1 a 40 letras, números, punto, guion o guion bajo.")
    datos: dict[str, str] = {}
    for clave in fila.datos:
        if clave not in columnas:
            errores.append(f"{clave}: no es una columna de {tabla}.")
    for clave, columna in columnas.items():
        valor = (fila.datos.get(clave) or "").strip()
        if not valor:
            if columna.obligatoria:
                errores.append(f"{clave}: es obligatorio.")
            continue
        if len(valor) > MAX_TEXTO:
            errores.append(f"{clave}: supera {MAX_TEXTO} caracteres.")
        elif columna.tipo == "catalogo" and valor not in columna.catalogo:
            errores.append(f"{clave}: «{valor}» no está en el catálogo permitido.")
        elif columna.tipo == "fecha" and fecha_real(valor) is None:
            errores.append(f"{clave}: «{valor}» no es una fecha real (AAAA-MM-DD).")
        elif columna.tipo == "tratamiento" and valor not in tratamientos:
            errores.append(f"{clave}: el tratamiento no existe en el RAT de tu organización.")
        datos[clave] = valor
    return datos, errores


# ¤adpa
async def _exigir_borrador(session: AsyncSession, borrador_id: str) -> None:
    fila = (await session.execute(text("SELECT id FROM biblioteca_borradores WHERE id=:id"),
                                  {"id": borrador_id})).first()
    if fila is None:  # la RLS oculta los de otra organización: igual que uno inexistente
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")


# ¤adpa
async def _codigos_existentes(session: AsyncSession, tabla: str, codigos: list[str]) -> set[str]:
    if not codigos:
        return set()
    filas = (await session.execute(text(
        "SELECT codigo FROM biblioteca_filas WHERE tabla=:tabla AND codigo = ANY(:codigos)"),
        {"tabla": tabla, "codigos": codigos})).scalars().all()
    return set(filas)


# ¤adpa
async def _previa(session: AsyncSession, tratamientos: PuertoTratamientos, tenant_id: str,
                  entrada: PegarFilas) -> tuple[Previa, list[dict[str, str]]]:
    if len(entrada.filas) > MAX_FILAS:
        raise ErrorNegocio("BIB_FILAS_DEMASIADAS")
    _esquema(entrada.tabla)
    propios = set(await tratamientos(session, tenant_id))
    existentes = await _codigos_existentes(session, entrada.tabla, [f.codigo for f in entrada.filas])
    vistos: set[str] = set()
    resultados, normalizadas = [], []
    for indice, fila in enumerate(entrada.filas):
        datos, errores = validar_fila(entrada.tabla, fila, propios)
        if fila.codigo in vistos:
            errores.append("codigo: repetido dentro de lo pegado.")
        elif fila.codigo in existentes:
            errores.append("codigo: ya existe en esta tabla de tu organización.")
        vistos.add(fila.codigo)
        resultados.append(ResultadoFila(indice=indice, codigo=fila.codigo, errores=errores))
        normalizadas.append(datos)
    previa = Previa(tabla=entrada.tabla, valida=all(not r.errores for r in resultados), filas=resultados)
    return previa, normalizadas


# ¤adpa
def _vista(fila: Mapping) -> Fila:
    datos = fila["datos"] if isinstance(fila["datos"], dict) else json.loads(fila["datos"])
    return Fila(id=fila["id"], borrador_id=fila["borrador_id"], tabla=fila["tabla"], codigo=fila["codigo"],
                datos=datos, tratamiento_id=fila["tratamiento_id"], revision=fila["revision"],
                actualizado_en=fila["actualizado_en"])


# ¤adpa
async def validar_filas(session: AsyncSession, tratamientos: PuertoTratamientos, tenant_id: str, actor: str,
                        borrador_id: str, entrada: PegarFilas) -> Previa:
    """Validación previa por fila; no escribe nada."""
    await _fijar_contexto(session, tenant_id, actor)
    await _exigir_borrador(session, borrador_id)
    return (await _previa(session, tratamientos, tenant_id, entrada))[0]


# ¤adpa
async def confirmar_filas(session: AsyncSession, tratamientos: PuertoTratamientos, tenant_id: str, actor: str,
                          borrador_id: str, entrada: PegarFilas) -> list[Fila]:
    """Guarda todas las filas o ninguna: valida antes de la primera inserción."""
    await _fijar_contexto(session, tenant_id, actor)
    await _exigir_borrador(session, borrador_id)
    previa, normalizadas = await _previa(session, tratamientos, tenant_id, entrada)
    if not previa.valida:
        malas = [str(r.indice + 1) for r in previa.filas if r.errores]
        raise ErrorNegocio("BIB_FILAS_INVALIDAS", "Revisa las filas: " + ", ".join(malas[:20]))
    ids: list[str] = []
    for fila, datos in zip(entrada.filas, normalizadas):
        identificador = str(uuid4())
        await session.execute(text(
            "INSERT INTO biblioteca_filas(id, tenant_id, borrador_id, tabla, codigo, datos, tratamiento_id, "
            "creado_por, actualizado_por) VALUES (:id, :t, :b, :tabla, :codigo, CAST(:datos AS jsonb), :trat, "
            ":u, :u)"),
            {"id": identificador, "t": tenant_id, "b": borrador_id, "tabla": entrada.tabla, "codigo": fila.codigo,
             "datos": json.dumps(datos, ensure_ascii=False), "trat": datos.get("tratamiento_id"), "u": actor})
        ids.append(identificador)
    return [_vista((await session.execute(text(LEER), {"id": i})).mappings().one()) for i in ids]


# ¤adpa
async def listar_filas(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str,
                       tabla: str) -> list[Fila]:
    await _fijar_contexto(session, tenant_id, actor)
    _esquema(tabla)
    await _exigir_borrador(session, borrador_id)
    filas = (await session.execute(text(
        "SELECT id, borrador_id, tabla, codigo, datos, tratamiento_id, revision, actualizado_en "
        "FROM biblioteca_filas WHERE borrador_id=:b AND tabla=:tabla ORDER BY codigo"),
        {"b": borrador_id, "tabla": tabla})).mappings().all()
    return [_vista(f) for f in filas]


# ¤adpa
async def editar_fila(session: AsyncSession, tratamientos: PuertoTratamientos, tenant_id: str, actor: str,
                      fila_id: str, entrada: EditarFila) -> Fila:
    """Edita los datos de una fila; el código y la tabla no cambian. Revisión desfasada: 409."""
    await _fijar_contexto(session, tenant_id, actor)
    actual = (await session.execute(text(LEER_BLOQUEANDO), {"id": fila_id})).mappings().first()
    if actual is None:
        raise ErrorNegocio("BIB_FILA_NO_ENCONTRADA")
    if actual["revision"] != entrada.revision:
        raise ErrorNegocio("BIB_FILA_REVISION_DESFASADA")
    propios = set(await tratamientos(session, tenant_id))
    datos, errores = validar_fila(actual["tabla"], FilaEntrada(codigo=actual["codigo"], datos=entrada.datos), propios)
    if errores:
        raise ErrorNegocio("BIB_FILAS_INVALIDAS", "; ".join(errores[:20]))
    await session.execute(text(
        "UPDATE biblioteca_filas SET datos=CAST(:datos AS jsonb), tratamiento_id=:trat, revision=revision+1, "
        "actualizado_por=:u, actualizado_en=now() WHERE id=:id AND revision=:rev"),
        {"datos": json.dumps(datos, ensure_ascii=False), "trat": datos.get("tratamiento_id"), "u": actor,
         "id": fila_id, "rev": entrada.revision})
    return _vista((await session.execute(text(LEER), {"id": fila_id})).mappings().one())


# ¤adpa
def _como_fecha(valor: object) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return fecha_real(valor) if isinstance(valor, str) else None


# ¤adpa
def estado_plan(inicio: object, fin: object, estado: str, hoy: date) -> str:
    """Columna calculada de PLA. Sin fecha real de fin (o fin antes del inicio): nunca «En plazo»."""
    if estado == "completada":
        return "Completada"
    fecha_fin, fecha_inicio = _como_fecha(fin), _como_fecha(inicio)
    if fecha_fin is None or (inicio not in (None, "") and fecha_inicio is None):
        return "Sin fecha válida"
    if fecha_inicio is not None and fecha_inicio > fecha_fin:
        return "Sin fecha válida"
    return "Vencida" if fecha_fin < hoy else "En plazo"


# ¤adpa
def filas_del_plan(plan: Mapping | None, hoy: date | None = None) -> list[FilaPlan]:
    """PLA en solo lectura desde el plan canónico (roadmap con olas y tareas); nada se guarda aquí."""
    hoy = hoy or date.today()
    if not plan:
        return []
    filas: list[FilaPlan] = []
    for ola in plan.get("waves", []):
        for tarea in ola.get("tasks", []):
            inicio, fin = tarea.get("start_date"), tarea.get("end_date")
            filas.append(FilaPlan(
                id=str(tarea["id"]), titulo=str(tarea.get("title") or ""), control_ref=str(tarea.get("control_ref") or ""),
                fecha_inicio=None if inicio is None else str(inicio), fecha_fin=None if fin is None else str(fin),
                estado=estado_plan(inicio, fin, str(tarea.get("status") or ""), hoy)))
    return filas


# ¤adpa
def esquemas() -> dict[str, list[dict]]:
    """Columnas editables por tabla, para que el cliente pinte la tabla (la regla es la del servidor)."""
    return {tabla: [{"clave": c.clave, "etiqueta": c.etiqueta, "tipo": c.tipo, "obligatoria": c.obligatoria,
                     "catalogo": list(c.catalogo)} for c in cols] for tabla, cols in ESQUEMAS.items()}
