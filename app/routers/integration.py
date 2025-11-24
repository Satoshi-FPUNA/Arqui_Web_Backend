from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from app.db import get_session
from app.models import Client, PointsBag, Product
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/integration",
    tags=["Integración con Sistemas Externos"],
    responses={
        401: {"description": "No autorizado (API Key inválida)"},
        404: {"description": "Recurso no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)

# 🔐 API KEY para sistemas externos
API_KEY = "SECRET123"


def verify_api_key(x_api_key: str = Header(..., description="Llave de autenticación del sistema externo")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


# ------------------------------------------------------
# 1) Healthcheck externo
# ------------------------------------------------------
@router.get(
    "/ping",
    summary="Verificar conexión externa",
    description="Permite a un sistema externo comprobar si la API está disponible.",
    response_description="Estado de disponibilidad del servicio"
)
def ping():
    return {
        "success": True,
        "data": "Sistema disponible",
        "error": None
    }


# ------------------------------------------------------
# 2) Obtener cliente por documento
# ------------------------------------------------------
@router.get(
    "/client/{documento}",
    summary="Obtener información de cliente",
    description="Devuelve información básica del cliente junto con sus puntos totales.",
    responses={
        200: {
            "description": "Cliente encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": 1,
                            "nombre": "Ana",
                            "apellido": "Gonzales",
                            "puntos_totales": 120
                        },
                        "error": None
                    }
                }
            }
        }
    }
)
def get_client_info(
    documento: str,
    session: Session = Depends(get_session),
    _: str = Depends(verify_api_key)
):
    cliente = session.exec(select(Client).where(Client.nro_documento == documento)).first()

    if not cliente:
        return {"success": False, "data": None, "error": "Cliente no encontrado"}

    bolsas = session.exec(select(PointsBag).where(PointsBag.cliente_id == cliente.id)).all()
    total = sum(b.saldo_puntos for b in bolsas)

    return {
        "success": True,
        "data": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "puntos_totales": total
        },
        "error": None
    }


# ------------------------------------------------------
# 3) Asignar puntos desde sistema externo
# ------------------------------------------------------
@router.post(
    "/points/assign",
    summary="Asignar puntos (sistema externo)",
    description="Permite que un sistema externo asigne puntos por compras realizadas.",
    responses={
        200: {
            "description": "Puntos asignados correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "cliente_id": 1,
                            "puntos_asignados": 50,
                            "bolsa_id": 4
                        },
                        "error": None
                    }
                }
            }
        }
    }
)
def assign_points(
    cliente_id: int,
    monto_compra: float,
    session: Session = Depends(get_session),
    _: str = Depends(verify_api_key)
):
    cliente = session.get(Client, cliente_id)

    if not cliente:
        return {"success": False, "data": None, "error": "Cliente no existe"}

    puntos = int(monto_compra // 10000)  # Regla simple

    bolsa = PointsBag(
        cliente_id=cliente_id,
        fecha_asignacion=datetime.now().date(),
        fecha_caducidad=datetime.now().date().replace(year=datetime.now().year + 1),
        puntos_asignados=puntos,
        puntos_utilizados=0,
        saldo_puntos=puntos,
        monto_operacion=monto_compra
    )

    session.add(bolsa)
    session.commit()
    session.refresh(bolsa)

    return {
        "success": True,
        "data": {
            "cliente_id": cliente_id,
            "puntos_asignados": puntos,
            "bolsa_id": bolsa.id
        },
        "error": None
    }


# ------------------------------------------------------
# 4) Canjear puntos desde sistema externo
# ------------------------------------------------------
@router.post(
    "/points/redeem",
    summary="Canjear puntos (sistema externo)",
    description="Permite a un sistema externo descontar puntos del cliente por canje.",
    responses={
        200: {
            "description": "Canje exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "cliente_id": 1,
                            "producto": "Café Latte",
                            "puntos_usados": 150
                        },
                        "error": None
                    }
                }
            }
        }
    }
)
def redeem_points(
    cliente_id: int,
    product_id: int,
    session: Session = Depends(get_session),
    _: str = Depends(verify_api_key)
):
    cliente = session.get(Client, cliente_id)
    producto = session.get(Product, product_id)

    if not cliente:
        return {"success": False, "data": None, "error": "Cliente no existe"}

    if not producto:
        return {"success": False, "data": None, "error": "Producto no existe"}

    bolsas = session.exec(select(PointsBag).where(PointsBag.cliente_id == cliente_id)).all()
    total = sum(b.saldo_puntos for b in bolsas)

    if total < producto.points_required:
        return {"success": False, "data": None, "error": "Puntos insuficientes"}

    puntos_usar = producto.points_required
    for bolsa in bolsas:
        if puntos_usar <= 0:
            break
        usar = min(bolsa.saldo_puntos, puntos_usar)
        bolsa.saldo_puntos -= usar
        bolsa.puntos_utilizados += usar
        puntos_usar -= usar
        session.add(bolsa)

    session.commit()

    return {
        "success": True,
        "data": {
            "cliente_id": cliente_id,
            "producto": producto.name,
            "puntos_usados": producto.points_required
        },
        "error": None
    }
