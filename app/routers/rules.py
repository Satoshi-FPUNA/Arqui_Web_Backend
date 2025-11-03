from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select
from ..db import get_session
from ..models import Rule
from ..schemas import RuleCreate

router = APIRouter(prefix="/rules", tags=["Reglas"])

# Crear reglas
@router.post("", response_model=Rule, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleCreate, session: Session = Depends(get_session)):
    # Validar coherencia de límites
    if payload.limite_superior is not None and payload.limite_superior < payload.limite_inferior:
        raise HTTPException(
            status_code=400,
            detail="El límite superior no puede ser menor que el límite inferior."
        )

    # Validar que no se solape con otras reglas existentes
    overlaps = session.exec(
        select(Rule)
        .where(
            Rule.limite_superior >= payload.limite_inferior,  # se superpone por abajo
        )
        .where(
            (Rule.limite_inferior <= payload.limite_superior) | (Rule.limite_superior == None)
        )
    ).all()

    if overlaps:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una regla que se solapa con este rango de montos."
        )

    # Crear la nueva regla
    regla = Rule(**payload.dict())
    session.add(regla)
    session.commit()
    session.refresh(regla)
    return regla

# Listar Reglas
@router.get("", response_model=List[Rule])
def list_rules(session: Session = Depends(get_session)):
    return list(session.exec(select(Rule)).all())

# Actualizar una regla
@router.put("/{rule_id}", response_model=Rule)
def update_rule(rule_id: int, payload: RuleCreate, session: Session = Depends(get_session)):
    r = session.get(Rule, rule_id)
    if not r: raise HTTPException(404, "Regla no encontrada")
    for k, v in payload.dict().items(): setattr(r, k, v)
    session.add(r); session.commit(); session.refresh(r); return r

# Eliminar una regla 
@router.delete("/{rule_id}")
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    r = session.get(Rule, rule_id)
    if not r: raise HTTPException(404, "Regla no encontrada")
    session.delete(r); session.commit(); return {"ok": True}
