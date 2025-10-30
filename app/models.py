from datetime import date
from typing import Optional
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
