from pydantic import BaseModel, EmailStr
from datetime import date, timedelta
from typing import Optional, List

# CLIENTES
class ClientCreate(BaseModel):
    nombre: str
    apellido: str
    nro_documento: str
    tipo_documento: str
    nacionalidad: str
    email: EmailStr
    telefono: str
    fecha_nacimiento: date

class ClientUpdate(BaseModel):
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None


# REGLAS DE PUNTOS
class RuleCreate(BaseModel):
    limite_inferior: Optional[int] = None
    limite_superior: Optional[int] = None
    equivalencia_monto: int


# VENCIMIENTOS
class ExpirationParamCreate(BaseModel):
    fecha_inicio_validez: date
    dias_duracion: int


class ExpirationParamUpdate(BaseModel):
    fecha_inicio_validez: Optional[date] = None
    dias_duracion: Optional[int] = None


class ExpirationParamRead(BaseModel):
    id: int
    fecha_inicio_validez: date
    fecha_fin_validez: date
    dias_duracion: int


# CONCEPTOS (Premios)
class ConceptCreate(BaseModel):
    descripcion: str
    puntos_requeridos: int

class ConceptUpdate(BaseModel):
    descripcion: Optional[str] = None
    puntos_requeridos: Optional[int] = None


# BOLSA DE PUNTOS
class AssignPointsRequest(BaseModel):
    cliente_id: int
    monto_operacion: int

class PointsUseHeaderRead(BaseModel):
    id: int
    cliente_id: int
    concepto_id: int
    puntaje_utilizado: int
    fecha: date


# CANJE DE PUNTOS
class UsePointsRequest(BaseModel):
    cliente_id: int
    concepto_id: int
