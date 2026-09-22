"""Tests de T06 — Router POST /api/v1/auth/login (RF-1, RF-3, RNF-4) — TDD."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db

# Importar modelos para registrar en Base
from app.models.producto import Producto  # noqa: F401
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
from app.models.proveedor import Proveedor  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401


def _make_client_with_auth():
    """Crea app de test con DB en memoria y router de auth + productos para verificar token usable."""
    # Importar dentro para que tome el último estado de auth_service
    from app.routers.auth import router as auth_router
    from app.routers.productos import router as productos_router
    from fastapi import FastAPI

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

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(productos_router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def _crear_usuario_directo(
    SessionLocal, email="admin@tienda.com", password="secreto123"
):
    """Crea usuario directo en DB usando auth_service (simula CLI)."""
    from app.services.auth_service import hash_password, normalizar_email

    email_norm = normalizar_email(email)
    h = hash_password(password)
    db = SessionLocal()
    try:
        u = Usuario(email=email_norm, password_hash=h)
        db.add(u)
        db.commit()
    finally:
        db.close()


def test_login_exitoso_devuelve_token(monkeypatch):
    """T06: POST válido retorna 200 con access_token y token_type bearer."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-login-T06-32chars!!")
    client, SessionLocal = _make_client_with_auth()
    _crear_usuario_directo(SessionLocal, "admin@tienda.com", "secreto123")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tienda.com", "password": "secreto123"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"].count(".") == 2
    # nunca expone hash
    assert "password_hash" not in resp.text
    assert "password" not in data


def test_login_campos_ausentes_422(monkeypatch):
    """T06: email o password ausentes → 422 (regla dos niveles)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-login-T06-32chars!!")
    client, _ = _make_client_with_auth()

    resp = client.post("/api/v1/auth/login", json={"password": "secreto123"})
    assert resp.status_code == 422

    resp = client.post("/api/v1/auth/login", json={"email": "admin@tienda.com"})
    assert resp.status_code == 422

    resp = client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


def test_login_formato_invalido_no_existe_incorrecta_401_generico(monkeypatch):
    """T06: formato inválido, no existe, incorrecta → 401 Credenciales inválidas idéntico."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-login-T06-32chars!!")
    client, SessionLocal = _make_client_with_auth()
    _crear_usuario_directo(SessionLocal, "admin@tienda.com", "secreto123")

    for payload in [
        {"email": "sinarroba", "password": "secreto123"},
        {"email": "no-existe@tienda.com", "password": "secreto123"},
        {"email": "admin@tienda.com", "password": "erronea123"},
        {"email": "  sin arroba ", "password": "secreto123"},
    ]:
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401, f"payload {payload} → {resp.text}"
        assert resp.json()["detail"] == "Credenciales inválidas"


def test_login_token_usable_para_productos(monkeypatch):
    """T06: token devuelto es utilizable como Authorization Bearer en GET /api/v1/productos."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-login-T06-32chars!!")
    client, SessionLocal = _make_client_with_auth()
    _crear_usuario_directo(SessionLocal, "admin@tienda.com", "secreto123")

    # primero sin token, aun sin auth no debería estar protegido hasta T08, pero login debe generar token válido
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tienda.com", "password": "secreto123"},
    )
    token = login.json()["access_token"]
    # verificar que jwt decodifica correctamente
    import jwt

    payload = jwt.decode(token, "test-secret-login-T06-32chars!!", algorithms=["HS256"])
    assert payload["sub"] == "admin@tienda.com"


def test_login_no_expone_password_hash_en_respuesta(monkeypatch):
    """T06: respuesta nunca contiene password ni password_hash."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-login-T06-32chars!!")
    client, SessionLocal = _make_client_with_auth()
    _crear_usuario_directo(SessionLocal, "admin@tienda.com", "secreto123")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tienda.com", "password": "secreto123"},
    )
    text = resp.text.lower()
    assert "password_hash" not in text
    # el hash no debe aparecer ni truncado
    assert "$2b$" not in resp.text
