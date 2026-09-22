"""Tests de T08 — Protección retroactiva de routers 001-004 (RF-2) — TDD."""

import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.producto import Producto  # noqa: F401
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
from app.models.proveedor import Proveedor  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401


def _make_app():
    """Crea app de test con todos los routers protegidos (main real)."""
    from app.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def _crear_usuario_y_token(
    SessionLocal, email="admin@tienda.com", password="secreto123", monkeypatch=None
):
    """Crea usuario y devuelve token Bearer."""
    if monkeypatch:
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T08-32chars-minimo!!")
    else:
        os.environ["JWT_SECRET_KEY"] = "test-secret-T08-32chars-minimo!!"
    from app.services.auth_service import crear_token, hash_password, normalizar_email

    email_norm = normalizar_email(email)
    h = hash_password(password)
    db = SessionLocal()
    try:
        u = Usuario(email=email_norm, password_hash=h)
        db.add(u)
        db.commit()
    finally:
        db.close()
    token = crear_token(email_norm)
    return token


def test_protegidos_sin_token_401(monkeypatch):
    """T08: todos los /api/v1/* sin Authorization → 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T08-32chars-minimo!!")
    client, _ = _make_app()

    for method, path in [
        ("get", "/api/v1/productos"),
        ("post", "/api/v1/productos"),
        ("get", "/api/v1/proveedores"),
        ("get", "/api/v1/movimientos"),
        ("post", "/api/v1/movimientos/entradas"),
        ("post", "/api/v1/movimientos/salidas"),
        ("get", "/api/v1/stock"),
        ("get", "/api/v1/stock/PROD-001"),
    ]:
        if method == "post":
            resp = getattr(client, method)(path, json={}, headers={})
        else:
            resp = getattr(client, method)(path, headers={})
        assert resp.status_code == 401, (
            f"{method.upper()} {path} sin token debe ser 401, dio {resp.status_code} {resp.text}"
        )


def test_protegidos_con_token_valido_200(monkeypatch):
    """T08: con Bearer válido → 200/201 (misma lógica 001-004)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T08-32chars-minimo!!")
    client, SessionLocal = _make_app()
    token = _crear_usuario_y_token(SessionLocal, monkeypatch=monkeypatch)
    headers = {"Authorization": f"Bearer {token}"}

    # productos GET vacío → 200 (antes era 200 sin token, ahora con token)
    resp = client.get("/api/v1/productos", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []

    # crear proveedor con token → 201
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-001", "nombre": "Central"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    # stock global con token → 200
    resp = client.get("/api/v1/stock", headers=headers)
    assert resp.status_code == 200


def test_protegidos_con_token_invalido_401(monkeypatch):
    """T08: Bearer vacío, Basic, firma alterada, expirado → 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T08-32chars-minimo!!")
    client, SessionLocal = _make_app()
    token = _crear_usuario_y_token(SessionLocal, monkeypatch=monkeypatch)

    for header in [
        "Bearer ",
        "Basic abc",
        f"Bearer {token[:-1]}a" if token[-1] != "a" else f"Bearer {token[:-1]}b",
        "bearer " + token,  # case-sensitive
    ]:
        resp = client.get("/api/v1/productos", headers={"Authorization": header})
        assert resp.status_code == 401, (
            f"header {header[:20]} debe ser 401, dio {resp.status_code}"
        )

    # expirado
    import jwt
    import time

    payload = {"sub": "admin@tienda.com", "exp": int(time.time()) - 10}
    expirado = jwt.encode(
        payload, "test-secret-T08-32chars-minimo!!", algorithm="HS256"
    )
    resp = client.get(
        "/api/v1/productos", headers={"Authorization": f"Bearer {expirado}"}
    )
    assert resp.status_code == 401


def test_stock_inactivo_sigue_404_no_401_con_token(monkeypatch):
    """T08: GET /stock con producto inactivo y token válido → 404 (no 401 por negocio)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T08-32chars-minimo!!")
    client, SessionLocal = _make_app()
    token = _crear_usuario_y_token(SessionLocal, monkeypatch=monkeypatch)
    headers = {"Authorization": f"Bearer {token}"}

    # crear producto activo luego dar de baja
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "INACT-001", "nombre": "Inactivo", "categoria": "consola"},
        headers=headers,
    )
    assert resp.status_code == 201
    resp = client.delete("/api/v1/productos/INACT-001", headers=headers)
    assert resp.status_code == 200
    # stock de inactivo → 404
    resp = client.get("/api/v1/stock/INACT-001", headers=headers)
    assert resp.status_code == 404
    assert (
        "no encontrado" in resp.json()["detail"].lower()
        or "not found" in resp.json()["detail"].lower()
    )


def test_proteccion_no_toca_logica_interna():
    """T08: routers delegan a service, sin queries directas con token."""
    from pathlib import Path

    for name in ["productos.py", "proveedores.py", "movimientos.py", "stock.py"]:
        content = Path(f"app/routers/{name}").read_text(encoding="utf-8")
        # debe tener get_current_user
        assert "get_current_user" in content, f"{name} debe tener get_current_user"
        # no debe tener lógica de stock directa por auth
        assert "SELECT" not in content
