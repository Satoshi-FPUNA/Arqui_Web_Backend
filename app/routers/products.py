from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models import Product
from app.schemas import ProductCreate, ProductRead
from app.db import engine, get_session

router = APIRouter(
    prefix="/products",
    tags=["Productos"]
)

# Crear producto
@router.post("/", response_model=ProductRead, summary="Crear producto")
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    db_product = Product(**product.dict())
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


# Listar productos
@router.get("/", response_model=list[ProductRead], summary="Listar productos")
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    return products


# Obtener producto por ID
@router.get("/{product_id}", response_model=ProductRead, summary="Obtener producto por ID")
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


# Actualizar producto
@router.put("/{product_id}", response_model=ProductRead, summary="Actualizar producto")
def update_product(product_id: int, data: ProductCreate, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product.name = data.name
    product.points_required = data.points_required
    product.description = data.description

    session.commit()
    session.refresh(product)
    return product


# Desactivar producto
@router.delete("/{product_id}", summary="Desactivar producto")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product.is_active = False
    session.commit()
    return {"message": "Producto desactivado correctamente"}
