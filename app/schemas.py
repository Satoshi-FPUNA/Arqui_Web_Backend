from pydantic import BaseModel, EmailStr
from datetime import date, timedelta, datetime
from typing import Optional, List
from typing import Optional
from pydantic import BaseModel

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
    codigo_referidor: Optional[str] = None   # Referidos

class ClientUpdate(BaseModel):
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None

# CLIENTE BÁSICO PARA MOSTRAR EN ENCUESTAS
class ClientRead(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr

    class Config:
        orm_mode = True

class ClientWithPoints(BaseModel):
    id: int
    nombre: str
    apellido: str
    nro_documento: str
    tipo_documento: str
    nacionalidad: str
    email: str
    telefono: str
    fecha_nacimiento: date
    referral_code: str
    referred_by_id: Optional[int] = None
    puntos_totales: int
    level_id: Optional[int] = None
    level_name: Optional[str] = None

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

# ASIGNACIÓN DE PUNTOS
class AssignPointsResponse(BaseModel):
    ok: bool
    cliente_id: int
    puntos_asignados: int
    fecha_caducidad: date
    saldo_total: int
    level_id: Optional[int] = None
    level_name: Optional[str] = None

# NIVELES DE FIDELIZACIÓN
class LoyaltyLevelBase(BaseModel):
    name: str
    min_points: int
    priority: int = 0 
    benefits: Optional[str] = None 

class LoyaltyLevelCreate(LoyaltyLevelBase):
    pass

class LoyaltyLevelUpdate(BaseModel):
    name: Optional[str] = None
    min_points: Optional[int] = None
    priority: Optional[int] = None
    benefits: Optional[str] = None

class LoyaltyLevelRead(LoyaltyLevelBase):
    id: int

class ClientLevelRead(BaseModel):
    client_id: int
    total_points: int
    level_id: Optional[int]
    level_name: Optional[str]
class ProductCreate(BaseModel):
    name: str
    points_required: int
    description: Optional[str] = None

class ProductRead(BaseModel):
    id: int
    name: str
    points_required: int
    description: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True
        
class RedeemRequest(BaseModel):
    client_id: int
    product_id: int


class RedeemResponse(BaseModel):
    message: str
    product_name: str
    points_used: int
    remaining_points: int

# ENCUESTAS DE SATISFACCIÓN
class SurveyCreate(BaseModel):
    cliente_id: int
    puntuacion: int
    comentario: Optional[str] = None

class SurveyRead(BaseModel):
    id: int
    cliente_id: int
    fecha: datetime
    puntuacion: int
    comentario: Optional[str] = None

class SurveyWithClient(BaseModel):
    id: int
    fecha: datetime
    puntuacion: int
    comentario: Optional[str] = None
    cliente: ClientRead

    class Config:
        orm_mode = True
