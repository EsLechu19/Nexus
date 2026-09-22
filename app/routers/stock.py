"""Router de stock — solo HTTP y validación Pydantic (RF-1)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stock import StockResponse
from app.services import stock_service
from app.services.deps import get_current_user

router = APIRouter(
    prefix="/api/v1/stock", tags=["stock"], dependencies=[Depends(get_current_user)]
)


@router.get("/{codigo}", response_model=StockResponse)
def obtener_stock(codigo: str, db: Session = Depends(get_db)) -> StockResponse:
    """Stock actual por código con alerta (RF-1). Delega a service."""
    # Validación sintáctica de código via Pydantic (trim+mayúsculas, 3-20)
    from app.schemas.stock import StockQuery

    try:
        StockQuery(codigo=codigo)  # valida 422 si formato inválido
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    stock = stock_service.calcular_stock(db, codigo)
    return StockResponse(**stock)


@router.get("", response_model=list[StockResponse])
def listar_stock(db: Session = Depends(get_db)) -> list[StockResponse]:
    """Stock global solo activos ordenados por codigo con alerta (RF-1). Delega a service."""
    stocks = stock_service.listar_stock(db)
    return [StockResponse(**s) for s in stocks]
