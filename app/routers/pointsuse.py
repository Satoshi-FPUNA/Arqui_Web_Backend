from datetime import date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlmodel import Session, select
from pydantic import EmailStr
from typing import List, Optional
from ..db import get_session
from ..models import (
    Client,
    PointConcept,
    PointsBag,
    PointsUseHeader,
    PointsUseDetail,
)
from ..schemas import UsePointsRequest, PointsUseHeaderRead

import os

router = APIRouter(prefix="/pointsuse", tags=["Uso de Puntos"])

# Configuración de FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


# Enviar correo de comprobante
async def send_comprobante_email(cliente: Client, concepto: PointConcept, puntos: int, fecha: date):
    subject = "Comprobante de Canje de Puntos"
    body = f"""
    <h3>¡Hola {cliente.nombre} {cliente.apellido}!</h3>
    <p>Tu canje se ha realizado correctamente.</p>
    <ul>
        <li><b>Concepto:</b> {concepto.descripcion}</li>
        <li><b>Puntos utilizados:</b> {puntos}</li>
        <li><b>Fecha:</b> {fecha.strftime('%d/%m/%Y')}</li>
    </ul>
    <p>Gracias por participar en nuestro programa de fidelización.</p>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[cliente.email],
        body=body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# Canjear puntos (FIFO) + Envío de correo
@router.post("/use", response_model=PointsUseHeader)
async def use_points(payload: UsePointsRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    cliente = session.get(Client, payload.cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado.")

    concepto = session.get(PointConcept, payload.concepto_id)
    if not concepto:
        raise HTTPException(404, "Concepto no encontrado.")

    puntos_requeridos = concepto.puntos_requeridos
    if puntos_requeridos <= 0:
        raise HTTPException(400, "El concepto requiere un puntaje válido mayor a cero.")

    # Bolsas activas (FIFO)
    hoy = date.today()
    bolsas = session.exec(
        select(PointsBag)
        .where(PointsBag.cliente_id == payload.cliente_id)
        .where(PointsBag.saldo_puntos > 0)
        .where(PointsBag.fecha_caducidad >= hoy)
        .order_by(PointsBag.fecha_asignacion.asc(), PointsBag.id.asc())
    ).all()

    if not bolsas:
        raise HTTPException(400, "El cliente no tiene puntos disponibles.")

    saldo_total = sum(b.saldo_puntos for b in bolsas)
    if saldo_total < puntos_requeridos:
        raise HTTPException(
            400,
            f"Puntos insuficientes. Requerido: {puntos_requeridos}, disponible: {saldo_total}.",
        )

    # Crear cabecera
    cabecera = PointsUseHeader(
        cliente_id=payload.cliente_id,
        concepto_id=payload.concepto_id,
        puntaje_utilizado=puntos_requeridos,
        fecha=hoy,
    )
    session.add(cabecera)
    session.commit()
    session.refresh(cabecera)

    # Aplicar consumo FIFO
    restante = puntos_requeridos
    for bolsa in bolsas:
        if restante <= 0:
            break

        usar = min(bolsa.saldo_puntos, restante)
        bolsa.saldo_puntos -= usar
        bolsa.puntos_utilizados += usar

        detalle = PointsUseDetail(
            cabecera_id=cabecera.id,
            bolsa_id=bolsa.id,
            puntaje_utilizado=usar,
        )
        session.add(detalle)
        session.add(bolsa)
        restante -= usar

    session.commit()
    session.refresh(cabecera)

    # Enviar comprobante por correo en background
    background_tasks.add_task(send_comprobante_email, cliente, concepto, puntos_requeridos, hoy)

    return cabecera


# Historial de canjes por cliente
@router.get("/history/{cliente_id}", response_model=List[PointsUseHeader])
def get_use_history(cliente_id: int, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(PointsUseHeader)
            .where(PointsUseHeader.cliente_id == cliente_id)
            .order_by(PointsUseHeader.fecha.desc())
        ).all()
    )


# Detalles de un canje
@router.get("/details/{cabecera_id}", response_model=List[PointsUseDetail])
def get_use_details(cabecera_id: int, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(PointsUseDetail)
            .where(PointsUseDetail.cabecera_id == cabecera_id)
            .order_by(PointsUseDetail.id.asc())
        ).all()
    )


# Listar Canje
@router.get("", response_model=List[PointsUseHeader])
def list_pointsuse(cliente_id: Optional[int] = None, session: Session = Depends(get_session)):
    q = select(PointsUseHeader).order_by(PointsUseHeader.fecha.desc())
    if cliente_id is not None:
        q = q.where(PointsUseHeader.cliente_id == cliente_id)
    return list(session.exec(q).all())