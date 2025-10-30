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
