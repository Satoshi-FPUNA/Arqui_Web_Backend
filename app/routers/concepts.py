from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from ..db import get_session
from ..models import PointConcept
from ..schemas import ConceptCreate, ConceptUpdate

router = APIRouter(prefix="/concepts", tags=["Conceptos"])

# Crear Concepto
@router.post("", response_model=PointConcept)
def create_concept(payload: ConceptCreate, session: Session = Depends(get_session)):
    c = PointConcept(**payload.dict())
    session.add(c)
    session.commit()
    session.refresh(c)
    return c

# Listar Concepto
@router.get("", response_model=List[PointConcept])
def list_concepts(session: Session = Depends(get_session)):
    return list(session.exec(select(PointConcept)).all())

# Actualizar un concepto
@router.put("/{concept_id}", response_model=PointConcept)
def update_concept(concept_id: int, payload: ConceptUpdate, session: Session = Depends(get_session)):
    c = session.get(PointConcept, concept_id)
    if not c:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    # Pydantic v1: dict(exclude_unset=True)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(c, k, v)

    session.add(c)
    session.commit()
    session.refresh(c)
    return c

#Eliminar un concepto
@router.delete("/{concept_id}")
def delete_concept(concept_id: int, session: Session = Depends(get_session)):
    c = session.get(PointConcept, concept_id)
    if not c:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    session.delete(c)
    session.commit()
    return {"ok": True}