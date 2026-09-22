"""Router de movimientos — solo HTTP y validación Pydantic (RF-1, RF-2, RF-3)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.movimiento import (
    MovimientoCreateEntrada,
    MovimientoCreateSalida,
    MovimientoResponse,
)
from app.services import movimiento_service
from app.services.deps import get_current_user

router = APIRouter(
    prefix="/api/v1/movimientos",
    tags=["movimientos"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/entradas", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED
)
def crear_entrada(
    datos: MovimientoCreateEntrada, db: Session = Depends(get_db)
) -> MovimientoResponse:
    """Registra entrada de stock (RF-1). Delega a service."""
    movimiento = movimiento_service.registrar_entrada(db, datos)
    # Calcular stock actual para respuesta
    from app.services.movimiento_service import calcular_stock

    stock = calcular_stock(db, datos.producto_codigo)
    return MovimientoResponse(
        id=movimiento.id,
        producto_codigo=datos.producto_codigo.strip().upper(),
        proveedor_codigo=datos.proveedor_codigo.strip().upper(),
        tipo=movimiento.tipo,  # type: ignore
        cantidad=movimiento.cantidad,
        motivo=movimiento.motivo,
        fecha=movimiento.created_at.isoformat(),  # type: ignore
        stock_actual=stock["stock_actual"],
    )


@router.post(
    "/salidas", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED
)
def crear_salida(
    datos: MovimientoCreateSalida, db: Session = Depends(get_db)
) -> MovimientoResponse:
    """Registra salida de stock (RF-2). Delega a service."""
    movimiento = movimiento_service.registrar_salida(db, datos)
    from app.services.movimiento_service import calcular_stock

    stock = calcular_stock(db, datos.producto_codigo)
    return MovimientoResponse(
        id=movimiento.id,
        producto_codigo=datos.producto_codigo.strip().upper(),
        proveedor_codigo=None,
        tipo=movimiento.tipo,  # type: ignore
        cantidad=movimiento.cantidad,
        motivo=movimiento.motivo,
        fecha=movimiento.created_at.isoformat(),  # type: ignore
        stock_actual=stock["stock_actual"],
    )


@router.get("", response_model=list[MovimientoResponse])
def listar_historial(
    producto_codigo: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
) -> list[MovimientoResponse]:
    """Historial de movimientos (RF-3). Delega a service."""
    if tipo is not None and tipo not in ("entrada", "salida", "entrada_inicial"):
        raise HTTPException(status_code=422, detail="Tipo inválido")
    movimientos = movimiento_service.listar_historial(
        db, producto_codigo=producto_codigo, tipo=tipo
    )
    # Mapear a response con códigos
    from app.models.producto import Producto
    from app.models.proveedor import Proveedor

    result: list[MovimientoResponse] = []
    for m in movimientos:
        prod = db.query(Producto).filter(Producto.id == m.producto_id).first()
        prov_codigo = None
        if m.proveedor_id is not None:
            prov = db.query(Proveedor).filter(Proveedor.id == m.proveedor_id).first()
            prov_codigo = prov.codigo if prov else None
        result.append(
            MovimientoResponse(
                id=m.id,
                producto_codigo=prod.sku if prod else "",  # type: ignore
                proveedor_codigo=prov_codigo,
                tipo=m.tipo,  # type: ignore
                cantidad=m.cantidad,
                motivo=m.motivo,
                fecha=m.created_at.isoformat(),  # type: ignore
            )
        )
    return result
