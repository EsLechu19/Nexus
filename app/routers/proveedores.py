"""Router de proveedores — solo HTTP y validación Pydantic (RF-1, RF-2, RF-3, RF-4, RF-5)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorListResponse,
    ProveedorResponse,
    ProveedorUpdate,
)
from app.services import proveedor_service
from app.services.deps import get_current_user

router = APIRouter(
    prefix="/api/v1/proveedores",
    tags=["proveedores"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    datos: ProveedorCreate, db: Session = Depends(get_db)
) -> ProveedorResponse:
    """Alta de proveedor (RF-1). Delega a service, retorna 201."""
    proveedor = proveedor_service.crear_proveedor(db, datos)
    return ProveedorResponse(
        codigo=proveedor.codigo,
        nombre=proveedor.nombre,
        email=proveedor.email,
        telefono=proveedor.telefono,
        direccion=proveedor.direccion,
        estado=proveedor.estado,  # type: ignore[arg-type]
    )


@router.get("", response_model=list[ProveedorListResponse])
def listar_proveedores(
    db: Session = Depends(get_db),
) -> list[ProveedorListResponse]:
    """Listado de proveedores activos (RF-2). Delega a service."""
    proveedores = proveedor_service.listar_activos(db)
    return [
        ProveedorListResponse(
            codigo=p.codigo,
            nombre=p.nombre,
            email=p.email,
            telefono=p.telefono,
            direccion=p.direccion,
        )
        for p in proveedores
    ]


@router.get("/{codigo}", response_model=ProveedorResponse)
def obtener_proveedor(codigo: str, db: Session = Depends(get_db)) -> ProveedorResponse:
    """Detalle por código normalizado (RF-3). Delega a service."""
    proveedor = proveedor_service.obtener_por_codigo(db, codigo)
    return ProveedorResponse(
        codigo=proveedor.codigo,
        nombre=proveedor.nombre,
        email=proveedor.email,
        telefono=proveedor.telefono,
        direccion=proveedor.direccion,
        estado=proveedor.estado,  # type: ignore[arg-type]
    )


@router.patch("/{codigo}", response_model=ProveedorResponse)
def actualizar_proveedor(
    codigo: str, datos: ProveedorUpdate, db: Session = Depends(get_db)
) -> ProveedorResponse:
    """Edición de proveedor (RF-4). Delega a service."""
    proveedor = proveedor_service.actualizar_proveedor(db, codigo, datos)
    return ProveedorResponse(
        codigo=proveedor.codigo,
        nombre=proveedor.nombre,
        email=proveedor.email,
        telefono=proveedor.telefono,
        direccion=proveedor.direccion,
        estado=proveedor.estado,  # type: ignore[arg-type]
    )


@router.delete("/{codigo}", response_model=ProveedorResponse)
def baja_proveedor(codigo: str, db: Session = Depends(get_db)) -> ProveedorResponse:
    """Baja lógica (RF-5). Delega a service."""
    proveedor = proveedor_service.baja_proveedor(db, codigo)
    return ProveedorResponse(
        codigo=proveedor.codigo,
        nombre=proveedor.nombre,
        email=proveedor.email,
        telefono=proveedor.telefono,
        direccion=proveedor.direccion,
        estado=proveedor.estado,  # type: ignore[arg-type]
    )
