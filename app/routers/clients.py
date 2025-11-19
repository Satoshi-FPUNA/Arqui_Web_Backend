from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from ..db import get_session
from ..models import Client, PointsBag, LoyaltyLevel
from ..schemas import ClientCreate, ClientUpdate, ClientWithPoints

router = APIRouter(prefix="/clients", tags=["Clientes"])

#Promocioens
PROMOS_BY_LEVEL = {
    "Bronce": ["Cupón de bienvenida", "+10 puntos por su próxima compra"],
    "Plata": ["10% descuento en compras mayores a 50.000 Gs", "+20 puntos extra"],
    "Oro": ["15% de descuento", "Envío gratuito", "+50 puntos por compra"],
    "Diamante": ["20% de descuento", "Regalo exclusivo", "+100 puntos mensuales"]
}

PROMOS_BY_NACIONALIDAD = {
    "Paraguaya": ["10% descuento en productos nacionales"],
    "Argentina": ["Promo turista: +20 puntos en la primera compra"],
    "Brasileña": ["Envío gratis en compras mayores a 100.000 Gs"],
}

PROMOS_BY_POINTS = [
    (0, 100, ["Motivación: +15 puntos si compra esta semana"]),
    (101, 500, ["10% descuento", "+25 puntos por compra"]),
    (501, 1000, ["15% descuento", "Acceso a catálogo premium"]),
    (1001, 999999, ["Regalo VIP", "2×1 en productos seleccionados"])
]

# Para devolver listado de clientes y sus puntos totales y no repetir código
def _client_with_points(c: Client, session: Session) -> ClientWithPoints:
    # Obtener bolsas
    bolsas = session.exec(
        select(PointsBag).where(PointsBag.cliente_id == c.id)
    ).all()
    total = sum(b.saldo_puntos for b in bolsas) if bolsas else 0

    # Obtener su nivel actual
    level = session.exec(
        select(LoyaltyLevel)
        .where(LoyaltyLevel.min_points <= total)
        .order_by(LoyaltyLevel.min_points.desc())
    ).first()

    level_id = level.id if level else None
    level_name = level.name if level else None

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
        level_id=level_id,
        level_name=level_name,
    )

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

# Segmentación de clientes
@router.get("/segment", response_model=List[ClientWithPoints])
def segment_clients(
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    nacionalidad: Optional[str] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    level_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    clientes = session.exec(select(Client)).all()
    hoy = date.today()
    resultado = []

    for c in clientes:
        incluir = True

        # Calcular edad
        edad = hoy.year - c.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (c.fecha_nacimiento.month, c.fecha_nacimiento.day):
            edad -= 1

        # Edad
        if min_age is not None and edad < min_age:
            incluir = False
        if max_age is not None and edad > max_age:
            incluir = False

        # Nacionalidad
        if nacionalidad and c.nacionalidad.lower() != nacionalidad.lower():
            incluir = False

        # Calcular puntos del cliente
        bolsas = session.exec(
            select(PointsBag).where(PointsBag.cliente_id == c.id)
        ).all()
        puntos = sum(b.saldo_puntos for b in bolsas) if bolsas else 0

        # Puntos
        if min_points is not None and puntos < min_points:
            incluir = False
        if max_points is not None and puntos > max_points:
            incluir = False

        # Nivel fidelización
        if level_id is not None:
            nivel = session.exec(
                select(LoyaltyLevel)
                .where(LoyaltyLevel.min_points <= puntos)
                .order_by(LoyaltyLevel.min_points.desc())
            ).first()

            if not nivel or nivel.id != level_id:
                incluir = False

        #  Si pasa los filtros, agregar cliente con puntos
        if incluir:
            resultado.append(_client_with_points(c, session))

    return resultado


@router.get("/promotions")
def get_promotions(
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    nacionalidad: Optional[str] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    level_id: Optional[int] = None,
    session: Session = Depends(get_session)
):

    # Obtenemos los clientes segmentados
    clientes = segment_clients(
        min_age=min_age,
        max_age=max_age,
        nacionalidad=nacionalidad,
        min_points=min_points,
        max_points=max_points,
        level_id=level_id,
        session=session
    )

    promociones_finales = []

    for client in clientes:
        promo_cliente = []

        # Por nivel
        if client.level_name:
            nivel = client.level_name
            if nivel in PROMOS_BY_LEVEL:
                promo_cliente.extend(PROMOS_BY_LEVEL[nivel])

        # Por Nacionalidad
        if client.nacionalidad:
            nac = client.nacionalidad.capitalize()
            if nac in PROMOS_BY_NACIONALIDAD:
                promo_cliente.extend(PROMOS_BY_NACIONALIDAD[nac])

        # Por rango de puntos
        for min_p, max_p, promos in PROMOS_BY_POINTS:
            if min_p <= client.puntos_totales <= max_p:
                promo_cliente.extend(promos)
                break

        promociones_finales.append({
            "cliente": client,
            "promociones": promo_cliente
        })

    return promociones_finales


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
