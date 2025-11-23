from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from pydantic import BaseModel

class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    nro_documento: str
    tipo_documento: str
    nacionalidad: str
    email: str
    telefono: str
    fecha_nacimiento: date

    # Sistema de referidos
    referral_code: str = Field(
        default_factory=lambda: uuid4().hex[:8],  # código corto. Ej: a1b2c3d4
        index=True
    )
    referred_by_id: Optional[int] = Field(
        default=None,
        foreign_key="client.id"
    )

class Rule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    limite_inferior: Optional[int] = None
    limite_superior: Optional[int] = None
    equivalencia_monto: int                # Cuántos puntos equivale x guaranies


class ExpirationParam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_inicio_validez: Optional[date] = None
    fecha_fin_validez: Optional[date] = None
    dias_duracion: Optional[int] = None


class PointConcept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str
    puntos_requeridos: int


class PointsBag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="client.id")
    fecha_asignacion: date
    fecha_caducidad: date
    puntos_asignados: int
    puntos_utilizados: int = 0
    saldo_puntos: int
    monto_operacion: int

    # Relaciones
    usos_detalle: List["PointsUseDetail"] = Relationship(back_populates="bolsa")


class PointsUseHeader(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="client.id")
    concepto_id: int = Field(foreign_key="pointconcept.id")
    puntaje_utilizado: int
    fecha: date = Field(default_factory=date.today)

    # Relación uno a muchos con los detalles
    detalles: List["PointsUseDetail"] = Relationship(back_populates="cabecera")


class PointsUseDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cabecera_id: int = Field(foreign_key="pointsuseheader.id")
    bolsa_id: int = Field(foreign_key="pointsbag.id")
    puntaje_utilizado: int

    # Relaciones inversas
    cabecera: Optional[PointsUseHeader] = Relationship(back_populates="detalles")
    bolsa: Optional[PointsBag] = Relationship(back_populates="usos_detalle")

class PointsBagCreate(BaseModel):
    cliente_id: int
    puntos_asignados: int
    monto_operacion: int

class LoyaltyLevel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    min_points: int = Field(ge=0)
    priority: int = 0
    benefits: Optional[str] = None

class Survey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="client.id")
    fecha: datetime = Field(default_factory=datetime.utcnow)
    puntuacion: int                    # Rango del 1 a 5
    comentario: Optional[str] = None   # opcional