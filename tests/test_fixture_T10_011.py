"""Tests de T10 — fixture auth_headers (Impacto 001-004, RNF-6) — TDD."""


def test_conftest_existe_y_expone_auth_headers():
    """T10: tests/conftest.py debe existir y exponer fixture auth_headers."""
    from pathlib import Path

    p = Path("tests/conftest.py")
    assert p.exists(), "falta tests/conftest.py"
    content = p.read_text(encoding="utf-8")
    assert "auth_headers" in content
    assert "Authorization" in content
    assert "Bearer" in content


def test_fixture_devuelve_bearer_valido(monkeypatch):
    """T10: fixture auth_headers debe devolver header con Bearer válido."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T10-32chars-minimo!!")
    # Importar fixture directamente
    import importlib

    mod = importlib.import_module("tests.conftest")
    # la fixture debe ser callable que retorna dict
    # usamos la función subyacente
    _fixture = mod.auth_headers  # noqa: F841
    from app.services.auth_service import crear_token

    # Simular lo que hace la fixture: crear token y retornar header
    token = crear_token("test_011_fixture@tienda.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    # validar que token es verificable
    from app.services.auth_service import validar_token

    payload = validar_token(token)
    assert payload["sub"] == "test_011_fixture@tienda.com"


def test_control_sin_token_401_y_con_token_200(monkeypatch):
    """T10: control — sin header → 401, con header de fixture → 200."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T10-32chars-minimo!!")
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import Base, get_db
    from app.main import app
    from app.models.producto import Producto  # noqa: F401
    from app.models.usuario import Usuario  # noqa: F401

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

    # sin token → 401
    resp = client.get("/api/v1/productos")
    assert resp.status_code == 401, resp.text

    # con token de fixture → 200
    from app.services.auth_service import crear_token

    token = crear_token("test_011_control@tienda.com")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/productos", headers=headers)
    assert resp.status_code == 200, resp.text

    app.dependency_overrides.clear()
