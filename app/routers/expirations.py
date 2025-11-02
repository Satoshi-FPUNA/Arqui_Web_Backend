from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from ..db import get_session
from ..models import ExpirationParam
from ..schemas import ExpirationParamCreate

router = APIRouter(prefix="/expirations", tags=["Vencimientos"])

# Crear una expiración
@router.post("", response_model=ExpirationParam)
def create_exp(payload: ExpirationParamCreate, session: Session = Depends(get_session)):
    e = ExpirationParam(**payload.dict()); session.add(e); session.commit(); session.refresh(e); return e

# Listado
@router.get("", response_model=List[ExpirationParam])
def list_exp(session: Session = Depends(get_session)):
    return list(session.exec(select(ExpirationParam)).all())

# Actualizar
@router.put("/{exp_id}", response_model=ExpirationParam)
def update_exp(exp_id: int, payload: ExpirationParamCreate, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e: raise HTTPException(404, "Parámetro no encontrado")
    for k, v in payload.model_dump().items(): setattr(e, k, v)
    session.add(e); session.commit(); session.refresh(e); return e

# Eliminar
@router.delete("/{exp_id}")
def delete_exp(exp_id: int, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e: raise HTTPException(404, "Parámetro no encontrado")
    session.delete(e); session.commit(); return {"ok": True}