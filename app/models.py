from datetime import date, datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field

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

class Rule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    limite_inferior: Optional[int] = None
    limite_superior: Optional[int] = None
    equivalencia_monto: int                # Cuántos puntos equivale x guaranies

class Expiration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_inicio_validez: Optional[date] = None
    fecha_fin_validez: Optional[date] = None
    dias_duracion: Optional[int] = None

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

class PointsUseHeader(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="client.id")
    puntaje_utilizado: int
    fecha: date = Field(default_factory=date.today)  # ✅ siempre guarda la fecha actual
    concepto_id: int = Field(foreign_key="pointconcept.id")

class PointsUseDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cabecera_id: int = Field(foreign_key="pointsuseheader.id")
    puntaje_utilizado: int
    bolsa_id: int = Field(foreign_key="pointsbag.id")