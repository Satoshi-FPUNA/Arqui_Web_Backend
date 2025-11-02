from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlmodel import Session, select
from ..db import get_session
from ..models import Client
from ..schemas import ClientCreate, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clientes"])

# Crear cliente
@router.post("", response_model=Client)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)):
    c = Client(**payload.dict())
    session.add(c); session.commit(); session.refresh(c)
    return c

# Listar clientes
@router.get("", response_model=List[Client])
def list_clients(q: Optional[str] = Query(None, description="Buscar por nombre/apellido"), session: Session = Depends(get_session)):
    res = session.exec(select(Client)).all()
    if q:
        ql = q.lower()
        res = [c for c in res if ql in c.nombre.lower() or ql in c.apellido.lower()]
    return res

# Búsqueda específica
@router.get("/find", response_model=List[Client])
def find_clients(
    nro_documento: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    session: Session = Depends(get_session)
):
    stmt = select(Client)
    results = session.exec(stmt).all()
    if nro_documento:
        results = [c for c in results if c.nro_documento == nro_documento]
    if email:
        results = [c for c in results if c.email.lower() == email.lower()]
    if telefono:
        results = [c for c in results if c.telefono == telefono]
    return results

# Obtener cliente por id
@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, session: Session = Depends(get_session)):
    c = session.get(Client, client_id)
    if not c: raise HTTPException(404, "Cliente no encontrado")
    return c

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
@router.delete("/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    c = session.get(Client, client_id)
    if not c: raise HTTPException(404, "Cliente no encontrado")
    session.delete(c); session.commit()
    return {"ok": True}
