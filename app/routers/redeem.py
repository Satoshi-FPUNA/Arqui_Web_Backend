from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.models import Product, PointsUseHeader, PointsUseDetail, PointsBag, PointConcept
from app.schemas import RedeemRequest, RedeemResponse
from app.db import engine, get_session
from datetime import date

router = APIRouter(
    prefix="/redeem",
    tags=["Canje"]
)

@router.post("/", response_model=RedeemResponse, summary="Canjear producto")
def redeem_product(data: RedeemRequest):
    client_id = data.client_id
    product_id = data.product_id

    with Session(engine) as session:

        # 1. Buscar producto
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if not product.is_active:
            raise HTTPException(status_code=400, detail="Producto no está activo")

        points_needed = product.points_required

        # 2. Verificar si el cliente tiene suficientes puntos
        bags = session.exec(
            select(PointsBag).where(
                PointsBag.cliente_id == client_id,
                PointsBag.saldo_puntos > 0,
                PointsBag.fecha_caducidad >= date.today()
            ).order_by(PointsBag.fecha_asignacion)
        ).all()

        total_points = sum(b.saldo_puntos for b in bags)

        if total_points < points_needed:
            raise HTTPException(status_code=400, detail="Puntos insuficientes")

        # 3. Crear cabecera de uso
        concepto = session.exec(select(PointConcept)).first()
        if not concepto:
            raise HTTPException(status_code=500, detail="Debe existir al menos un concepto")

        header = PointsUseHeader(
            cliente_id=client_id,
            concepto_id=concepto.id,
            puntaje_utilizado=points_needed,
            fecha=date.today()
        )
        session.add(header)
        session.commit()
        session.refresh(header)

        remaining = points_needed

        # 4. Descontar puntos usando FIFO
        for bag in bags:
            if remaining <= 0:
                break

            use_points = min(bag.saldo_puntos, remaining)
            bag.saldo_puntos -= use_points
            bag.puntos_utilizados += use_points
            remaining -= use_points

            detail = PointsUseDetail(
                cabecera_id=header.id,
                bolsa_id=bag.id,
                puntaje_utilizado=use_points
            )
            session.add(detail)

        session.commit()

        # 5. Calcular puntos restantes del cliente
        new_total = sum(b.saldo_puntos for b in bags)

        return RedeemResponse(
            message="Canje realizado con éxito",
            product_name=product.name,
            points_used=points_needed,
            remaining_points=new_total
        )

