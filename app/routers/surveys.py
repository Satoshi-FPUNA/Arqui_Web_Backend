from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db import get_session
from app.models import Survey, Client
from app.schemas import SurveyCreate, SurveyRead, SurveyWithClient
from datetime import datetime
from typing import List
from app.models import Survey, Client

router = APIRouter(prefix="/surveys", tags=["Encuestas"])

# Crear encuesta
@router.post("", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
def create_survey(payload: SurveyCreate, session: Session = Depends(get_session)):
    # Validar cliente existente
    cliente = session.get(Client, payload.cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    encuesta = Survey(
        cliente_id=payload.cliente_id,
        puntuacion=payload.puntuacion,
        comentario=payload.comentario,
        fecha=datetime.utcnow()
    )
    session.add(encuesta)
    session.commit()
    session.refresh(encuesta)
    return encuesta

# Listar todas las encuestas
@router.get("", response_model=List[SurveyWithClient])
def list_surveys(session: Session = Depends(get_session)):
    encuestas = session.exec(select(Survey)).all()
    result = []

    for e in encuestas:
        cliente = session.get(Client, e.cliente_id)
        result.append({
            "id": e.id,
            "fecha": e.fecha,
            "puntuacion": e.puntuacion,
            "comentario": e.comentario,
            "cliente": cliente
        })

    return result

# Consultar encuestas por cliente
@router.get("/cliente/{cliente_id}", response_model=List[SurveyRead])
def get_surveys_by_client(cliente_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(Survey).where(Survey.cliente_id == cliente_id)
    ).all()
