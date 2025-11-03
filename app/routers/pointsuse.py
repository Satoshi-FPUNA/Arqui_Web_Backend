from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.db import engine
from app.models import PointsUseHeader, PointsUseDetail, PointConcept

router = APIRouter(prefix="/pointsuse", tags=["Historial de Canjes"])

@router.get("/cliente/{cliente_id}")
def get_use_history(cliente_id: int):
    with Session(engine) as session:
        # Traer todas las cabeceras de canjes del cliente
        cabeceras = session.exec(
            select(PointsUseHeader)
            .where(PointsUseHeader.cliente_id == cliente_id)
            .order_by(PointsUseHeader.fecha.desc())
        ).all()

        if not cabeceras:
            raise HTTPException(status_code=404, detail="El cliente no tiene historial de canjes")

        resultado = []

        for cab in cabeceras:
            # Buscar el concepto canjeado (ej: Café, Postre)
            concepto = session.get(PointConcept, cab.concepto_id)

            # Buscar detalles del canje (bolsas utilizadas)
            detalles = session.exec(
                select(PointsUseDetail)
                .where(PointsUseDetail.cabecera_id == cab.id)
            ).all()

            resultado.append({
                "id": cab.id,
                "fecha": cab.fecha,
                "concepto": concepto.descripcion if concepto else "Desconocido",
                "puntos_utilizados": cab.puntaje_utilizado,
                "detalles": [
                    {
                        "bolsa_id": d.bolsa_id,
                        "puntos_usados": d.puntaje_utilizado
                    }
                    for d in detalles
                ]
            })

        return {
            "cliente_id": cliente_id,
            "canjes": resultado
        }
