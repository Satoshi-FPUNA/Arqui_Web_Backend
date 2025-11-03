from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from app.db import get_session
from app.models import Expiration
from app.schemas import ExpirationCreate

router = APIRouter(prefix="/expirations", tags=["Vencimientos"])

# 🔹 Crear una nueva configuración de vencimiento
@router.post("", response_model=Expiration)
def create_expiration(payload: ExpirationCreate, session: Session = Depends(get_session)):
    # 🔸 Validar que las fechas tengan sentido lógico
    if payload.fecha_fin_validez < payload.fecha_inicio_validez:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio."
        )

    # 🔸 Validar que no haya solapamientos con otros periodos
    overlaps = session.exec(
        select(Expiration)
        .where(Expiration.fecha_inicio_validez <= payload.fecha_fin_validez)
        .where(Expiration.fecha_fin_validez >= payload.fecha_inicio_validez)
    ).all()

    if overlaps:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un periodo de vencimiento que se solapa con estas fechas."
        )

    # 🔸 Crear y guardar la nueva configuración
    expiracion = Expiration(**payload.dict())
    session.add(expiracion)
    session.commit()
    session.refresh(expiracion)
    return expiracion


# 🔹 Listar todas las configuraciones de vencimiento
@router.get("", response_model=List[Expiration])
def list_expirations(session: Session = Depends(get_session)):
    return list(session.exec(select(Expiration)).all())


# 🔹 Obtener una configuración específica por ID
@router.get("/{expiration_id}", response_model=Expiration)
def get_expiration(expiration_id: int, session: Session = Depends(get_session)):
    expiracion = session.get(Expiration, expiration_id)
    if not expiracion:
        raise HTTPException(status_code=404, detail="Configuración de vencimiento no encontrada.")
    return expiracion


# 🔹 Actualizar una configuración existente
@router.put("/{expiration_id}", response_model=Expiration)
def update_expiration(expiration_id: int, payload: ExpirationCreate, session: Session = Depends(get_session)):
    expiracion = session.get(Expiration, expiration_id)
    if not expiracion:
        raise HTTPException(status_code=404, detail="Configuración de vencimiento no encontrada.")

    # Validar coherencia de fechas
    if payload.fecha_fin_validez < payload.fecha_inicio_validez:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio."
        )

    # Validar solapamiento con otras configuraciones (excepto consigo misma)
    overlaps = session.exec(
        select(Expiration)
        .where(Expiration.id != expiration_id)
        .where(Expiration.fecha_inicio_validez <= payload.fecha_fin_validez)
        .where(Expiration.fecha_fin_validez >= payload.fecha_inicio_validez)
    ).all()

    if overlaps:
        raise HTTPException(
            status_code=400,
            detail="Ya existe otro periodo que se solapa con estas fechas."
        )

    for key, value in payload.dict().items():
        setattr(expiracion, key, value)

    session.add(expiracion)
    session.commit()
    session.refresh(expiracion)
    return expiracion


# 🔹 Eliminar una configuración
@router.delete("/{expiration_id}")
def delete_expiration(expiration_id: int, session: Session = Depends(get_session)):
    expiracion = session.get(Expiration, expiration_id)
    if not expiracion:
        raise HTTPException(status_code=404, detail="Configuración de vencimiento no encontrada.")
    session.delete(expiracion)
    session.commit()
    return {"ok": True, "mensaje": "Configuración de vencimiento eliminada correctamente."}
