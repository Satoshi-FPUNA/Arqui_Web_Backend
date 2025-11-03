from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta
from typing import List, Optional
from sqlmodel import Session, select, desc
from ..db import get_session
from ..models import ExpirationParam
from ..schemas import ExpirationParamCreate, ExpirationParamRead, ExpirationParamUpdate

router = APIRouter(prefix="/expirations", tags=["Vencimientos"])

# Calcula el vencimiento sumandole al inicio los días
def _calc_fin(inicio, dias):
    return inicio + timedelta(days=dias)

# Crear una expiración
@router.post("", response_model=ExpirationParamRead)
def create_expiration(payload: ExpirationParamCreate, session: Session = Depends(get_session)):
    if payload.dias_duracion is None or payload.dias_duracion <= 0:
        raise HTTPException(status_code=422, detail="dias_duracion debe ser > 0")
    if payload.fecha_inicio_validez is None:
        raise HTTPException(status_code=422, detail="fecha_inicio_validez es requerida")

    fecha_fin = _calc_fin(payload.fecha_inicio_validez, payload.dias_duracion)
    e = ExpirationParam(
        fecha_inicio_validez=payload.fecha_inicio_validez,
        fecha_fin_validez=fecha_fin,
        dias_duracion=payload.dias_duracion,
    )
    session.add(e)
    session.commit()
    session.refresh(e)
    return e

# Lista todos los vencimientos
@router.get("", response_model=List[ExpirationParamRead])
def list_expirations(session: Session = Depends(get_session)):
    return list(session.exec(select(ExpirationParam)).all())

# Obtiene vencimientos actualmente activos o recientes
@router.get("/current", response_model=Optional[ExpirationParamRead])
def get_current_expiration(session: Session = Depends(get_session)):
    stmt = select(ExpirationParam).order_by(desc(ExpirationParam.fecha_inicio_validez), desc(ExpirationParam.id)).limit(1)
    current = session.exec(stmt).first()
    return current  # puede ser None si no hay registros

# Actualiza una expiración
@router.put("/{exp_id}", response_model=ExpirationParamRead)
def update_expiration(exp_id: int, payload: ExpirationParamUpdate, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e:
        raise HTTPException(404, "Parámetro no encontrado")

    data = payload.dict(exclude_unset=True)

    # Validaciones antes de aplicar
    nuevo_inicio = data.get("fecha_inicio_validez", e.fecha_inicio_validez)
    nuevos_dias = data.get("dias_duracion", e.dias_duracion)

    if nuevos_dias is not None and nuevos_dias <= 0:
        raise HTTPException(status_code=422, detail="dias_duracion debe ser > 0")
    if nuevo_inicio is None:
        raise HTTPException(status_code=422, detail="fecha_inicio_validez no puede quedar vacío")

    # Aplicar cambios
    for k, v in data.items():
        setattr(e, k, v)

    # Recalcular fin
    e.fecha_fin_validez = _calc_fin(nuevo_inicio, nuevos_dias)

    session.add(e)
    session.commit()
    session.refresh(e)
    return e

# Eliminar una expiración
@router.delete("/{exp_id}")
def delete_expiration(exp_id: int, session: Session = Depends(get_session)):
    e = session.get(ExpirationParam, exp_id)
    if not e:
        raise HTTPException(404, "Parámetro no encontrado")
    session.delete(e)
    session.commit()
    return {"ok": True}
