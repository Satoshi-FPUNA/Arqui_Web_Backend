from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from datetime import timedelta
from ..db import get_session
from ..models import ExpirationParam
from ..schemas import ExpirationParamCreate, ExpirationParamUpdate  # agrega Update si no lo tienes

router = APIRouter(prefix="/expirations", tags=["Vencimientos"])

# Crear una expiración
@router.post("", response_model=ExpirationParam)
def create_exp(payload: ExpirationParamCreate, session: Session = Depends(get_session)):
    data = payload.dict()
    # Calcula la fecha de fin automáticamente
    if data.get("fecha_inicio_validez") and data.get("dias_duracion"):
        data["fecha_fin_validez"] = data["fecha_inicio_validez"] + timedelta(days=data["dias_duracion"])

    e = ExpirationParam(**data)
    session.add(e)
    session.commit()
    session.refresh(e)
    return e


# Listado
@router.get("", response_model=List[ExpirationParam])
def list_exp(session: Session = Depends(get_session)):
    return list(session.exec(select(ExpirationParam)).all())


# Actualizar
@router.put("/{exp_id}", response_model=ExpirationParam)
def update_exp(exp_id: int, payload: ExpirationParamUpdate, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e:
        raise HTTPException(404, "Parámetro no encontrado")

    data = payload.dict(exclude_unset=True)

    # Si se cambian la fecha o los días, recalcula el vencimiento
    if "fecha_inicio_validez" in data or "dias_duracion" in data:
        fecha_inicio = data.get("fecha_inicio_validez", e.fecha_inicio_validez)
        dias = data.get("dias_duracion", e.dias_duracion)
        data["fecha_fin_validez"] = fecha_inicio + timedelta(days=dias)

    for k, v in data.items():
        setattr(e, k, v)

    session.add(e)
    session.commit()
    session.refresh(e)
    return e


# Eliminar
@router.delete("/{exp_id}")
def delete_exp(exp_id: int, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e:
        raise HTTPException(404, "Parámetro no encontrado")
    session.delete(e)
    session.commit()
    return {"ok": True}