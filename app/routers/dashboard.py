from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from app.db import get_session
from app.models import Client, PointsBag, PointsUseHeader, Survey, LoyaltyLevel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

#Total de Puntos Canjeados
@router.get("/puntos-canjeados")
def puntos_canjeados(session: Session = Depends(get_session)):
    total = session.exec(
        select(func.sum(PointsUseHeader.puntaje_utilizado))
    ).one() or 0

    return {"puntos_canjeados": int(total)}

#Calculo de retención de clientes, son activos si tienen actividad en ultimos 90 días
@router.get("/retencion")
def tasa_retencion(session: Session = Depends(get_session)):
    hoy = datetime.utcnow()
    hace_90_dias = hoy - timedelta(days=90)

    activos_bolsa = session.exec(
        select(PointsBag.cliente_id)
        .where(PointsBag.fecha_asignacion >= hace_90_dias)
    ).all()

    activos_canjes = session.exec(
        select(PointsUseHeader.cliente_id)
        .where(PointsUseHeader.fecha >= hace_90_dias)
    ).all()

    activos_encuestas = session.exec(
        select(Survey.cliente_id)
        .where(Survey.fecha >= hace_90_dias)
    ).all()

    activos = set(activos_bolsa + activos_canjes + activos_encuestas)

    total_clientes = session.exec(
        select(func.count(Client.id))
    ).one()

    if total_clientes == 0:
        return {"tasa_retencion": 0}

    tasa = (len(activos) / total_clientes) * 100

    return {
        "clientes_totales": total_clientes,
        "clientes_activos_ultimos_90_dias": len(activos),
        "tasa_retencion": round(tasa, 2)
    }

#Retorno de Inversión 
@router.get("/roi")
def calcular_roi(session: Session = Depends(get_session)):
    monto_total = session.exec(
        select(func.sum(PointsBag.monto_operacion))
    ).one() or 0

    puntos_canjeados = session.exec(
        select(func.sum(PointsUseHeader.puntaje_utilizado))
    ).one() or 0

    costo_por_punto = 100  # puedes ajustarlo
    costo_total_puntos = puntos_canjeados * costo_por_punto

    if costo_total_puntos == 0:
        return {"roi": None, "detalle": "No hubo canjes aún"}

    roi = (monto_total - costo_total_puntos) / costo_total_puntos

    return {
        "monto_total_generado": int(monto_total),
        "puntos_canjeados": int(puntos_canjeados),
        "costo_programa_puntos": costo_total_puntos,
        "roi": round(roi, 2)
    }

#Indicadores de Rendimiento Extras
#Total de clientes registrados en el sistema
# @router.get("/total-clientes")
# def total_clientes(session: Session = Depends(get_session)):
#     total = session.exec(select(func.count(Client.id))).one()
#     return {"total_clientes": total}

#Puntos Vigentes del sistema
@router.get("/puntos/vigentes")
def puntos_vigentes(session: Session = Depends(get_session)):
    total = session.exec(
        select(func.sum(PointsBag.saldo_puntos))
        .where(PointsBag.fecha_caducidad >= datetime.utcnow())
    ).one() or 0
    return {"puntos_vigentes": int(total)}

#Total de puntos no utilizados/vencidos
@router.get("/puntos/vencidos")
def puntos_vencidos(session: Session = Depends(get_session)):
    total = session.exec(
        select(func.sum(PointsBag.saldo_puntos))
        .where(PointsBag.fecha_caducidad < datetime.utcnow())
    ).one() or 0
    return {"puntos_vencidos": int(total)}

#Puntos asignados por mes(Cuantos puntos son destinados a clientes)
@router.get("/puntos-asignados-mensual")
def puntos_asignados_mensual(session: Session = Depends(get_session)):
    results = session.exec(
        select(
            func.strftime('%Y-%m', PointsBag.fecha_asignacion).label("mes"),
            func.sum(PointsBag.puntos_asignados).label("total_puntos")
        )
        .group_by(func.strftime('%Y-%m', PointsBag.fecha_asignacion))
        .order_by(func.strftime('%Y-%m', PointsBag.fecha_asignacion))
    ).all()

    return [
        {
            "mes": row[0],
            "puntos_asignados": row[1]
        } for row in results
    ]

#Puntos canjeados por mes(Cuantos puntos canjean los clientes)
@router.get("/puntos/canjeados-por-mes")
def puntos_canjeados_por_mes(session: Session = Depends(get_session)):
    rows = session.exec(
        select(
            func.strftime("%Y-%m", PointsUseHeader.fecha),
            func.sum(PointsUseHeader.puntaje_utilizado)
        ).group_by(func.strftime("%Y-%m", PointsUseHeader.fecha))
    ).all()
    return [{"mes": r[0], "puntos_canjeados": int(r[1])} for r in rows]

#Canjes realizados por mes(Cantidad de Compras realizadas)
@router.get("/canjes/por-mes")
def canjes_por_mes(session: Session = Depends(get_session)):
    rows = session.exec(
        select(
            func.strftime("%Y-%m", PointsUseHeader.fecha),
            func.count(PointsUseHeader.id)
        ).group_by(func.strftime("%Y-%m", PointsUseHeader.fecha))
    ).all()
    return [{"mes": r[0], "canjes": r[1]} for r in rows]

#Encuestas promedio por mes
@router.get("/encuestas/promedio-por-mes")
def encuestas_promedio_por_mes(session: Session = Depends(get_session)):
    rows = session.exec(
        select(
            func.strftime("%Y-%m", Survey.fecha),
            func.avg(Survey.puntuacion),
            func.count(Survey.id)
        ).group_by(func.strftime("%Y-%m", Survey.fecha))
    ).all()
    return [
        {"mes": r[0], "promedio": round(r[1], 2), "cantidad_encuestas": r[2]}
        for r in rows
    ]

#Distribucion de calificaciones
@router.get("/encuestas/distribucion")
def distribucion_encuestas(session: Session = Depends(get_session)):
    rows = session.exec(
        select(
            Survey.puntuacion,
            func.count(Survey.id)
        ).group_by(Survey.puntuacion)
    ).all()
    return [{"puntuacion": r[0], "cantidad": r[1]} for r in rows]

#Clientes por nivel de fidelización
@router.get("/clientes/niveles")
def clientes_por_nivel(session: Session = Depends(get_session)):
    # Obtener niveles
    levels = session.exec(select(LoyaltyLevel)).all()
    
    # Inicializar contador
    resultado = {lvl.name: 0 for lvl in levels}

    # Obtener todos los clientes
    clientes = session.exec(select(Client)).all()

    # Para cada cliente determinar su nivel igual que hace _client_with_points
    for c in clientes:
        # Calcular puntos totales vigentes
        bolsas = session.exec(
            select(PointsBag)
            .where(PointsBag.cliente_id == c.id)
            .where(PointsBag.fecha_caducidad >= datetime.utcnow())
        ).all()
        total = sum(b.saldo_puntos for b in bolsas)

        # Obtener nivel correspondiente
        nivel = session.exec(
            select(LoyaltyLevel)
            .where(LoyaltyLevel.min_points <= total)
            .order_by(LoyaltyLevel.min_points.desc())
        ).first()

        if nivel:
            resultado[nivel.name] += 1

    # Convertir dict → lista de objetos
    return [{"nivel": k, "clientes": v} for k, v in resultado.items()]
