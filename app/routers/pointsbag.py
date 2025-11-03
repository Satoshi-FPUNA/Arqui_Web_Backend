from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import date, timedelta
from typing import List
from sqlmodel import Session, select
from ..db import get_session
from ..models import PointsBag, Client, Rule, ExpirationParam
from ..schemas import AssignPointsRequest
from ..core.mailer import send_points_assigned_email, PointsAssignedEmail

router = APIRouter(prefix="/pointsbag", tags=["Bolsa de puntos"])

def _get_expiration_settings(session: Session) -> ExpirationParam:
    exp = session.exec(select(ExpirationParam).order_by(ExpirationParam.id.desc())).first()
    if not exp:
        raise HTTPException(400, "No hay parámetros de vencimiento configurados.")
    if not exp.fecha_inicio_validez and not exp.dias_duracion and not exp.fecha_fin_validez:
        raise HTTPException(400, "El parámetro de vencimiento está incompleto.")
    return exp

def _calc_expiry(exp: ExpirationParam, asignacion: date) -> date:
    """
    Regla: si hay dias_duracion => fin = inicio + dias; 
           si no, usa fecha_fin_validez si está; 
           fallback: 30 días.
    """
    if exp.dias_duracion and exp.fecha_inicio_validez:
        return exp.fecha_inicio_validez + timedelta(days=exp.dias_duracion)
    if exp.dias_duracion:
        return asignacion + timedelta(days=exp.dias_duracion)
    if exp.fecha_fin_validez:
        return exp.fecha_fin_validez
    return asignacion + timedelta(days=30)

def _puntos_por_monto(session: Session, monto: int) -> int:
    """
    Usa la primera regla que coincida con el rango; si ninguna tiene rango, usa equivalencia general.
    equivalencia_monto = cuántos puntos por cada X guaraníes.
    """
    reglas: List[Rule] = list(session.exec(select(Rule)))
    if not reglas:
        raise HTTPException(400, "No hay reglas de puntos configuradas.")

    # prioriza las que tienen rango
    for r in reglas:
        if r.limite_inferior is not None and r.limite_superior is not None:
            if r.limite_inferior <= monto <= r.limite_superior:
                return monto // r.equivalencia_monto

    # si no matcheó rangos, usa la primera equivalencia general
    regla_general = next((r for r in reglas if r.limite_inferior is None and r.limite_superior is None), None)
    if not regla_general:
        # o en última instancia usa la primera regla
        regla_general = reglas[0]
    return monto // regla_general.equivalencia_monto

@router.post("/assign", response_model=dict)
async def assign_points(
    payload: AssignPointsRequest,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
):
    # valida cliente
    cliente = session.get(Client, payload.cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # calcula puntos y vencimiento
    puntos = _puntos_por_monto(session, payload.monto_operacion)
    hoy = date.today()
    exp = _get_expiration_settings(session)
    fecha_cad = _calc_expiry(exp, hoy)

    # crea bolsa
    bag = PointsBag(
        cliente_id=payload.cliente_id,
        fecha_asignacion=hoy,
        fecha_caducidad=fecha_cad,
        puntos_asignados=puntos,
        puntos_utilizados=0,
        saldo_puntos=puntos,
        monto_operacion=payload.monto_operacion,
    )
    session.add(bag)
    session.commit()
    session.refresh(bag)

    # calcula saldo total actual del cliente (opcional, sumando bolsas vigentes)
    saldo_total = session.exec(
        select(PointsBag).where(PointsBag.cliente_id == payload.cliente_id)
    )
    saldo_sum = sum(b.saldo_puntos for b in saldo_total)

    # dispara email en background (no bloquea)
    if cliente.email:
        background.add_task(
            send_points_assigned_email,
            PointsAssignedEmail(
                to=cliente.email,
                nombre=f"{cliente.nombre} {cliente.apellido}".strip(),
                puntos_asignados=puntos,
                saldo_puntos=saldo_sum,
                fecha_caducidad=str(fecha_cad),
                monto_operacion=payload.monto_operacion,
            ),
        )

    return {
        "ok": True,
        "cliente_id": payload.cliente_id,
        "puntos_asignados": puntos,
        "fecha_caducidad": str(fecha_cad),
        "saldo_total": saldo_sum,
    }

@router.get("", response_model=List[PointsBag])
def list_bags(session: Session = Depends(get_session)):
    return list(session.exec(select(PointsBag)).all())
