from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from ..db import get_session
from ..models import Rule
from ..schemas import RuleCreate

router = APIRouter(prefix="/rules", tags=["Reglas"])

# Crear reglas
@router.post("", response_model=Rule)
def create_rule(payload: RuleCreate, session: Session = Depends(get_session)):
    r = Rule(**payload.dict()); session.add(r); session.commit(); session.refresh(r); return r

# Listar Reglas
@router.get("", response_model=List[Rule])
def list_rules(session: Session = Depends(get_session)):
    return list(session.exec(select(Rule)).all())

# Actualizar una regla
@router.put("/{rule_id}", response_model=Rule)
def update_rule(rule_id: int, payload: RuleCreate, session: Session = Depends(get_session)):
    r = session.get(Rule, rule_id)
    if not r: raise HTTPException(404, "Regla no encontrada")
    for k, v in payload.model_dump().items(): setattr(r, k, v)
    session.add(r); session.commit(); session.refresh(r); return r

# Eliminar una regla 
@router.delete("/{rule_id}")
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    r = session.get(Rule, rule_id)
    if not r: raise HTTPException(404, "Regla no encontrada")
    session.delete(r); session.commit(); return {"ok": True}
