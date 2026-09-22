"""Router de ventas — solo HTTP y delegación a venta_service (RF-1, RF-2, RF-3, RF-4, RNF-5)."""

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.venta import VentaCreate, VentaItemResponse, VentaResponse
from app.services import venta_service
from app.services.deps import get_current_user

router = APIRouter(
    prefix="/api/v1/ventas",
    tags=["ventas"],
    dependencies=[Depends(get_current_user)],
)


def _format_created_at_z(dt) -> str:
    """Formatea datetime a ISO 8601 UTC con sufijo Z."""
    if dt is None:
        from datetime import datetime

        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # Formato YYYY-MM-DDTHH:MM:SSZ sin microsegundos
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _venta_to_response(venta, db: Session) -> VentaResponse:
    """Convierte Venta + sus VentaItems a VentaResponse."""
    from app.models.producto import Producto
    from app.models.venta_item import VentaItem

    items_db = (
        db.query(VentaItem)
        .filter(VentaItem.venta_id == venta.id)
        .order_by(VentaItem.id)
        .all()
    )
    movimientos_ids: list[int] = []
    items_resp: list[VentaItemResponse] = []
    for item in items_db:
        movimientos_ids.append(int(item.movimiento_id))  # type: ignore[arg-type]
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        codigo = producto.sku if producto else ""  # type: ignore[attr-defined]
        items_resp.append(
            VentaItemResponse(
                producto_codigo=codigo,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal,
            )
        )
    created_at_str = _format_created_at_z(venta.created_at)  # type: ignore[attr-defined]
    return VentaResponse(
        id=venta.id,  # type: ignore[attr-defined]
        created_at=created_at_str,
        cliente={"nombre": venta.cliente_nombre, "email": venta.cliente_email},  # type: ignore[arg-type]
        items=items_resp,
        total=venta.total,  # type: ignore[attr-defined]
        movimientos_ids=movimientos_ids,
    )


@router.post("", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def crear_venta(
    datos: VentaCreate,
    db: Session = Depends(get_db),
) -> VentaResponse:
    """Registra venta atómica con carrito (RF-1, RF-2). Delega a venta_service."""
    datos_dict = datos.model_dump()
    venta = venta_service.registrar_venta(db, datos_dict)
    return _venta_to_response(venta, db)


@router.get("", response_model=list[VentaResponse])
def listar_ventas(
    db: Session = Depends(get_db),
) -> list[VentaResponse]:
    """Lista ventas ordenadas por created_at DESC, id DESC (RF-3)."""
    from app.models.venta import Venta

    ventas = db.query(Venta).order_by(Venta.created_at.desc(), Venta.id.desc()).all()
    return [_venta_to_response(v, db) for v in ventas]


@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(
    venta_id: int,
    db: Session = Depends(get_db),
) -> VentaResponse:
    """Detalle de venta por id (RF-4)."""
    from app.models.venta import Venta

    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return _venta_to_response(venta, db)
