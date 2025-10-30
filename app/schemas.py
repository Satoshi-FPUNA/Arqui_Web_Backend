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

class ExpirationParamCreate(BaseModel):
    fecha_inicio_validez: Optional[date] = None
    fecha_fin_validez: Optional[date] = None
    dias_duracion: Optional[int] = None

class ConceptCreate(BaseModel):
    descripcion: str
    puntos_requeridos: int

class AssignPointsRequest(BaseModel):
    cliente_id: int
    monto_operacion: int

class UsePointsRequest(BaseModel):
    cliente_id: int
    concepto_id: int
    puntos: int