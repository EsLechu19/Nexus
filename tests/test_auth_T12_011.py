"""Tests de T12 — Integración auth y acceso protegido (RF-1, RF-2, RF-3, RF-5, RNF-4, RNF-8) — TDD."""

import time

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.producto import Producto  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401


def _make_client():
    """Crea app de test con DB en memoria y todos los modelos."""
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
    return client, TestingSessionLocal, engine


def _crear_usuario(SessionLocal, email="admin@tienda.com", password="secreto123"):
    """Crea usuario directo en DB (simula CLI)."""
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
    return email_norm


def test_login_200_con_token_y_422_ausentes_y_401_generico(monkeypatch):
    """T12: POST /auth/login 200 con token, 422 ausentes, 401 sinarroba/no-existe/errónea sin hash."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T12-32chars-minimo!!")
    client, SessionLocal, _ = _make_client()
    _crear_usuario(SessionLocal, "admin@tienda.com", "secreto123")

    # 200 con token
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tienda.com", "password": "secreto123"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data and data["token_type"] == "bearer"
    assert data["access_token"].count(".") == 2
    assert "password_hash" not in resp.text and "$2b$" not in resp.text

    # 422 ausentes
    assert client.post("/api/v1/auth/login", json={"password": "x"}).status_code == 422
    assert (
        client.post("/api/v1/auth/login", json={"email": "a@b.com"}).status_code == 422
    )
    assert client.post("/api/v1/auth/login", json={}).status_code == 422

    # 401 genérico idéntico
    for payload in [
        {"email": "sinarroba", "password": "x"},
        {"email": "no-existe@tienda.com", "password": "x"},
        {"email": "admin@tienda.com", "password": "erronea123"},
    ]:
        r = client.post("/api/v1/auth/login", json=payload)
        assert r.status_code == 401, payload
        assert r.json()["detail"] == "Credenciales inválidas"
        assert "password_hash" not in r.text

    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_protegidos_sin_y_con_token_y_expirado(monkeypatch):
    """T12: GET /productos sin Bearer, con Bearer vacío/Basic/firma alterada/exp expirado → 401; con Bearer válido → 200."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T12-32chars-minimo!!")
    client, SessionLocal, _ = _make_client()
    _crear_usuario(SessionLocal, "admin@tienda.com", "secreto123")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tienda.com", "password": "secreto123"},
    )
    token = login.json()["access_token"]
    headers_ok = {"Authorization": f"Bearer {token}"}

    # sin Bearer → 401
    assert client.get("/api/v1/productos").status_code == 401
    assert client.get("/api/v1/proveedores").status_code == 401
    assert client.get("/api/v1/stock").status_code == 401

    # Bearer vacío / Basic / firma alterada → 401
    assert (
        client.get(
            "/api/v1/productos", headers={"Authorization": "Bearer "}
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/productos", headers={"Authorization": "Basic abc"}
        ).status_code
        == 401
    )
    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert (
        client.get(
            "/api/v1/productos", headers={"Authorization": f"Bearer {alterado}"}
        ).status_code
        == 401
    )
    # case-sensitive bearer
    assert (
        client.get(
            "/api/v1/productos", headers={"Authorization": f"bearer {token}"}
        ).status_code
        == 401
    )

    # expirado
    payload = {"sub": "admin@tienda.com", "exp": int(time.time()) - 10}
    expirado = jwt.encode(
        payload, "test-secret-T12-32chars-minimo!!", algorithm="HS256"
    )
    assert (
        client.get(
            "/api/v1/productos", headers={"Authorization": f"Bearer {expirado}"}
        ).status_code
        == 401
    )

    # con Bearer válido → 200 (misma lógica 001-004)
    assert client.get("/api/v1/productos", headers=headers_ok).status_code == 200
    assert client.get("/api/v1/proveedores", headers=headers_ok).status_code == 200
    assert client.get("/api/v1/stock", headers=headers_ok).status_code == 200

    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_docs_publico_pero_try_out_protegido(monkeypatch):
    """T12: GET /docs 200 sin token pero POST /productos vía Try it out sin Authorize → 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T12-32chars-minimo!!")
    client, _, _ = _make_client()
    # docs y openapi públicos
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    # Try it out sin token → 401 (protegido)
    assert (
        client.post(
            "/api/v1/productos",
            json={"sku": "X", "nombre": "Y", "categoria": "consola"},
        ).status_code
        == 401
    )
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_no_logout_y_rnf8_token_tras_borrado(monkeypatch):
    """T12: no hay POST /logout → 404; RNF-8 token tras DELETE FROM usuarios sigue 200 hasta exp."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T12-32chars-minimo!!")
    client, SessionLocal, engine = _make_client()
    _crear_usuario(SessionLocal, "borrar@tienda.com", "secreto123")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "borrar@tienda.com", "password": "secreto123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # no hay logout
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 404
    assert client.post("/api/v1/logout", headers=headers).status_code == 404

    # borrar usuario fuera de API
    # Usar el mismo engine del client (compartido via Base.metadata)
    from sqlalchemy.orm import sessionmaker as SM

    Session2 = SM(bind=engine)
    db = Session2()
    db.query(Usuario).filter(Usuario.email == "borrar@tienda.com").delete()
    db.commit()
    assert (
        db.query(Usuario).filter(Usuario.email == "borrar@tienda.com").first() is None
    )
    db.close()

    # token antiguo sigue válido hasta exp → 200
    resp = client.get("/api/v1/productos", headers=headers)
    assert resp.status_code == 200, resp.text

    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
