"""App principal — registra routers (RF-1..RF-5)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.routers.auth import router as auth_router
from app.routers.movimientos import router as movimientos_router
from app.routers.productos import router as productos_router
from app.routers.proveedores import router as proveedores_router
from app.routers.stock import router as stock_router
from app.routers.ventas import router as ventas_router

app = FastAPI(
    title="Sistema de Gestión de Inventario",
    version="0.1.0",
    description="Catálogo de productos, proveedores y movimientos para tienda de videojuegos",
)

# CORS para Vite dev en 5173 (RF-4, constitución §3) — sin credenciales hardcodeadas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(productos_router)
app.include_router(proveedores_router)
app.include_router(movimientos_router)
app.include_router(stock_router)
app.include_router(ventas_router)


def custom_openapi() -> dict:
    """Genera OpenAPI con securitySchemes HTTPBearer para endpoints protegidos (RF-3)."""
    if app.openapi_schema:
        return app.openapi_schema  # type: ignore[return-value]
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Definir securitySchemes bearer JWT
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "HTTPBearer"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Añadir security a todos los /api/v1/* salvo login (público)
    for path, methods in openapi_schema.get("paths", {}).items():
        if path.startswith("/api/v1/") and path != "/api/v1/auth/login":
            for method_cfg in methods.values():
                if isinstance(method_cfg, dict):
                    method_cfg.setdefault("security", [{"HTTPBearer": []}])
    app.openapi_schema = openapi_schema  # type: ignore[assignment]
    return openapi_schema


app.openapi = custom_openapi  # type: ignore[assignment]
