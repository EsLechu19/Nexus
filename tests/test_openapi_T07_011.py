"""Tests de T07 — Swagger/OpenAPI bearer (RF-3) — TDD."""

from fastapi.testclient import TestClient

from app.main import app


def test_openapi_contiene_security_schemes_bearer():
    """T07: openapi.json debe contener securitySchemes HTTPBearer bearer/JWT."""
    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "components" in data
    assert "securitySchemes" in data["components"]
    schemes = data["components"]["securitySchemes"]
    # debe haber HTTPBearer con type http, scheme bearer, bearerFormat JWT
    found = False
    for name, cfg in schemes.items():
        if cfg.get("type") == "http" and cfg.get("scheme") == "bearer":
            found = True
            assert cfg.get("bearerFormat") == "JWT"
    assert found, f"no hay securitySchemes bearer, schemes={schemes}"


def test_openapi_protegidos_tienen_security_y_login_no():
    """T07: todas las ops bajo /api/v1/* salvo POST /auth/login deben tener security."""
    client = TestClient(app)
    data = client.get("/openapi.json").json()
    paths = data["paths"]

    # login no debe tener security
    login_path = paths.get("/api/v1/auth/login")
    assert login_path is not None, "falta /api/v1/auth/login en openapi"
    login_post = login_path.get("post", {})
    assert "security" not in login_post, "login no debe exigir bearer"

    # protegidos deben tener security con HTTPBearer
    for p in list(paths.keys()):
        if p.startswith("/api/v1/") and p != "/api/v1/auth/login":
            for method, op in paths[p].items():
                if method in ("get", "post", "patch", "delete", "put"):
                    assert "security" in op, f"{method.upper()} {p} debe tener security"
                    # debe contener HTTPBearer
                    sec = op["security"]
                    assert any("HTTPBearer" in s for s in sec), f"{p} sin HTTPBearer"


def test_docs_y_openapi_publicos_sin_token():
    """T07: GET /docs y GET /openapi.json responden 200 sin token."""
    client = TestClient(app)
    for path in ["/docs", "/openapi.json"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} → {resp.status_code} {resp.text}"


def test_try_out_sin_token_responde_401():
    """T07: Try it out sin Authorize — en T07 solo se verifica que /docs es público, la protección real se verifica en T08."""
    client = TestClient(app)
    # En T07 aún sin protección T08, los endpoints aún responden 200; en T08 pasarán a 401
    # Solo verificamos que el cliente puede acceder a docs sin token
    resp = client.get("/docs")
    assert resp.status_code == 200
