from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import LoyaltyLevel, PointsBag
from app.schemas import (
    LoyaltyLevelCreate,
    LoyaltyLevelUpdate,
    LoyaltyLevelRead,
    ClientLevelRead,
)

router = APIRouter(prefix="/loyalty-levels", tags=["Niveles de Fidelización"])

@router.get("/", response_model=list[LoyaltyLevelRead])
def list_levels(session: Session = Depends(get_session)):
    return session.exec(select(LoyaltyLevel)).all()

@router.post("/", response_model=LoyaltyLevelRead)
def create_level(payload: LoyaltyLevelCreate, session: Session = Depends(get_session)):
    level = LoyaltyLevel(**payload.dict())
    session.add(level)
    session.commit()
    session.refresh(level)
    return level

@router.put("/{level_id}", response_model=LoyaltyLevelRead)
def update_level(level_id: int, payload: LoyaltyLevelUpdate, session: Session = Depends(get_session)):
    level = session.get(LoyaltyLevel, level_id)
    if not level:
        raise HTTPException(404, "Nivel no encontrado")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(level, key, value)

    session.add(level)
    session.commit()
    session.refresh(level)
    return level

@router.delete("/{level_id}")
def delete_level(level_id: int, session: Session = Depends(get_session)):
    level = session.get(LoyaltyLevel, level_id)
    if not level:
        raise HTTPException(404, "Nivel no encontrado")

    session.delete(level)
    session.commit()
    return {"message": "Nivel eliminado"}

# Obtener nivel actual del cliente
from app.models import PointsBag, PointsUseDetail

@router.get("/client/{client_id}", response_model=ClientLevelRead)
def get_client_level(client_id: int, session: Session = Depends(get_session)):
    # Obtener todas las bolsas del cliente
    bolsas = session.exec(
        select(PointsBag).where(PointsBag.cliente_id == client_id)
    ).all()

    # Calcular puntos totales disponibles
    total = sum(b.saldo_puntos for b in bolsas) if bolsas else 0

    # Buscar el nivel que le corresponde según min_points
    stmt = (
        select(LoyaltyLevel)
        .where(LoyaltyLevel.min_points <= total)
        .order_by(LoyaltyLevel.min_points.desc())
    )
    level = session.exec(stmt).first()

    return ClientLevelRead(
        client_id=client_id,
        total_points=total,
        level_id=level.id if level else None,
        level_name=level.name if level else None,
    )