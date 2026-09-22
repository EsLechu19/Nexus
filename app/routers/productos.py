"""Router de productos — solo HTTP y validación Pydantic (RF-1, RF-2, RF-3, RF-4, RF-5)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.producto import (
    ProductoCreate,
    ProductoListResponse,
    ProductoResponse,
    ProductoUpdate,
)
from app.services import producto_service
from app.services.deps import get_current_user

router = APIRouter(
    prefix="/api/v1/productos",
    tags=["productos"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    datos: ProductoCreate, db: Session = Depends(get_db)
) -> ProductoResponse:
    """Alta de producto (RF-1). Delega a service, retorna 201."""
    producto = producto_service.crear_producto(db, datos)
    return ProductoResponse(
        sku=producto.sku,
        nombre=producto.nombre,
        categoria=producto.categoria,  # type: ignore[arg-type]
        stock_inicial=producto.stock_inicial,
        stock_minimo=producto.stock_minimo,
        estado=producto.estado,  # type: ignore[arg-type]
    )


@router.get("", response_model=list[ProductoListResponse])
def listar_productos(db: Session = Depends(get_db)) -> list[ProductoListResponse]:
    """Listado de productos activos (RF-2). Delega a service."""
    productos = producto_service.listar_activos(db)
    return [
        ProductoListResponse(
            sku=p.sku,
            nombre=p.nombre,
            categoria=p.categoria,  # type: ignore[arg-type]
            stock_inicial=p.stock_inicial,
            stock_minimo=p.stock_minimo,
        )
        for p in productos
    ]


@router.get("/{sku}", response_model=ProductoResponse)
def obtener_producto(sku: str, db: Session = Depends(get_db)) -> ProductoResponse:
    """Detalle por SKU normalizado (RF-3). Delega a service."""
    producto = producto_service.obtener_por_sku(db, sku)
    return ProductoResponse(
        sku=producto.sku,
        nombre=producto.nombre,
        categoria=producto.categoria,  # type: ignore[arg-type]
        stock_inicial=producto.stock_inicial,
        stock_minimo=producto.stock_minimo,
        estado=producto.estado,  # type: ignore[arg-type]
    )


@router.patch("/{sku}", response_model=ProductoResponse)
def actualizar_producto_endpoint(
    sku: str, datos: ProductoUpdate, db: Session = Depends(get_db)
) -> ProductoResponse:
    """Edición de producto (RF-4). Delega a service."""
    producto = producto_service.actualizar_producto(db, sku, datos)
    return ProductoResponse(
        sku=producto.sku,
        nombre=producto.nombre,
        categoria=producto.categoria,  # type: ignore[arg-type]
        stock_inicial=producto.stock_inicial,
        stock_minimo=producto.stock_minimo,
        estado=producto.estado,  # type: ignore[arg-type]
    )


@router.delete("/{sku}", response_model=ProductoResponse)
def baja_producto_endpoint(sku: str, db: Session = Depends(get_db)) -> ProductoResponse:
    """Baja lógica (RF-5). Delega a service."""
    producto = producto_service.baja_producto(db, sku)
    return ProductoResponse(
        sku=producto.sku,
        nombre=producto.nombre,
        categoria=producto.categoria,  # type: ignore[arg-type]
        stock_inicial=producto.stock_inicial,
        stock_minimo=producto.stock_minimo,
        estado=producto.estado,  # type: ignore[arg-type]
    )
