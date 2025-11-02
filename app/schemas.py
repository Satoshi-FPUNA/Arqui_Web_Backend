from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

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

class RuleCreate(BaseModel):
    limite_inferior: Optional[int] = None
    limite_superior: Optional[int] = None
    equivalencia_monto: int

class ExpirationParamBase(BaseModel):
    fecha_inicio_validez: date
    dias_duracion: int

class ExpirationParamCreate(ExpirationParamBase):
    pass

class ExpirationParamUpdate(BaseModel):
    fecha_inicio_validez: Optional[date] = None
    dias_duracion: Optional[int] = None

class ExpirationParamRead(ExpirationParamBase):
    id: int
    fecha_fin_validez: date

class ConceptCreate(BaseModel):
    descripcion: str
    puntos_requeridos: int

class ConceptUpdate(BaseModel):
    descripcion: Optional[str] = None
    puntos_requeridos: Optional[int] = None

class AssignPointsRequest(BaseModel):
    cliente_id: int
    monto_operacion: int

class UsePointsRequest(BaseModel):
    cliente_id: int
    concepto_id: int
    puntos: int