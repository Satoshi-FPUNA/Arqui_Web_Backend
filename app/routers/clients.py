from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from ..db import get_session
from ..models import Client, PointsBag, LoyaltyLevel
from ..schemas import ClientCreate, ClientUpdate, ClientWithPoints

router = APIRouter(prefix="/clients", tags=["Clientes"])

# Para devolver listado de clientes y sus puntos totales y no repetir código
def _client_with_points(c: Client, session: Session) -> ClientWithPoints:
    bolsas = session.exec(
        select(PointsBag).where(PointsBag.cliente_id == c.id)
    ).all()
    total = sum(b.saldo_puntos for b in bolsas) if bolsas else 0

    return ClientWithPoints(
        id=c.id,
        nombre=c.nombre,
        apellido=c.apellido,
        nro_documento=c.nro_documento,
        tipo_documento=c.tipo_documento,
        nacionalidad=c.nacionalidad,
        email=c.email,
        telefono=c.telefono,
        fecha_nacimiento=c.fecha_nacimiento,
        referral_code=c.referral_code,
        referred_by_id=c.referred_by_id,
        puntos_totales=total,
    )

# Crear cliente si es que no está duplicado
BONUS_REFERENTE = 20  # Puntos para quien refiere
BONUS_REFERIDO = 10   # Puntos para el nuevo cliente

@router.post("", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)):
    data = payload.dict()
    codigo_referidor = data.pop("codigo_referidor", None)

    c = Client(**data)
    session.add(c)

    try:
        # Para que c.id exista antes de crear la bolsa del referido
        session.flush()

        # Si vino un código de referidor, procesamos el bono
        if codigo_referidor:
            referidor = session.exec(
                select(Client).where(Client.referral_code == codigo_referidor)
            ).first()

            if not referidor:
                session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Código de referidor inválido.",
                )

            # Guardar quién lo refirió
            c.referred_by_id = referidor.id

            hoy = date.today()
            fecha_cad = hoy + timedelta(days=365)  # 1 año de vigencia

            # Bolsa de puntos para el referidor
            bolsa_referente = PointsBag(
                cliente_id=referidor.id,
                fecha_asignacion=hoy,
                fecha_caducidad=fecha_cad,
                puntos_asignados=BONUS_REFERENTE,
                puntos_utilizados=0,
                saldo_puntos=BONUS_REFERENTE,
                monto_operacion=0,
            )
            session.add(bolsa_referente)

            # Bolsa de puntos para el nuevo cliente (referido)
            bolsa_referido = PointsBag(
                cliente_id=c.id,
                fecha_asignacion=hoy,
                fecha_caducidad=fecha_cad,
                puntos_asignados=BONUS_REFERIDO,
                puntos_utilizados=0,
                saldo_puntos=BONUS_REFERIDO,
                monto_operacion=0,
            )
            session.add(bolsa_referido)

        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Cliente duplicado (documento o email ya existe)")

    session.refresh(c)
    return c

# Listar clientes
@router.get("", response_model=List[ClientWithPoints])
def list_clients(
    q: Optional[str] = Query(None, description="Buscar por nombre/apellido"),
    session: Session = Depends(get_session),
):
    clientes = session.exec(select(Client)).all()
    if q:
        ql = q.lower()
        clientes = [
            c for c in clientes
            if ql in c.nombre.lower() or ql in c.apellido.lower()
        ]

    # Mapear cada cliente a ClientWithPoints
    return [_client_with_points(c, session) for c in clientes]

# Búsqueda específica
@router.get("/find", response_model=List[ClientWithPoints])
def find_clients(
    nro_documento: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    session: Session = Depends(get_session),
):
    stmt = select(Client)
    if nro_documento:
        stmt = stmt.where(Client.nro_documento == nro_documento)
    if email:
        stmt = stmt.where(Client.email.ilike(email))  # o == si tenés normalizado
    if telefono:
        stmt = stmt.where(Client.telefono == telefono)

    clientes = session.exec(stmt).all()
    return [_client_with_points(c, session) for c in clientes]

# Obtener cliente por id
@router.get("/{client_id}", response_model=ClientWithPoints)
def get_client(client_id: int, session: Session = Depends(get_session)):
    c = session.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Cliente no encontrado")

    return _client_with_points(c, session)


# Actualizar
@router.put("/{client_id}", response_model=Client)
def update_client(client_id: int, payload: ClientUpdate, session: Session = Depends(get_session)):
    c = session.get(Client, client_id)
    if not c: raise HTTPException(404, "Cliente no encontrado")
    if payload.telefono is not None: c.telefono = payload.telefono
    if payload.email is not None: c.email = payload.email
    session.add(c); session.commit(); session.refresh(c)
    return c

# Eliminar cliente
@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, session: Session = Depends(get_session)):
    c = session.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Cliente no encontrado")
    session.delete(c); session.commit()
    return
