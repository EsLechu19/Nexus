"""Tests de T03 — auth_service hasheo y verificación (RF-4, RNF-1, RNF-3) — TDD."""


def test_normalizar_email():
    """T03: normalizar_email trim+lower."""
    from app.services.auth_service import normalizar_email

    assert normalizar_email("  ADMIN@Tienda.COM ") == "admin@tienda.com"
    assert normalizar_email("USER@Example.COM") == "user@example.com"
    assert normalizar_email("  test@tienda.com  ") == "test@tienda.com"


def test_validar_email_formato():
    """T03: validar_email_formato regex 002, sin validar dominio."""
    from app.services.auth_service import validar_email_formato

    assert validar_email_formato("admin@tienda.com") is True
    assert validar_email_formato("user.name+tag@sub.dominio.com") is True
    assert validar_email_formato("ADMIN@TIENDA.COM") is True
    # inválidos
    assert validar_email_formato("sinarroba") is False
    assert validar_email_formato("sin@punto") is False
    assert validar_email_formato("con espacios@tienda.com") is False
    assert validar_email_formato("") is False
    assert validar_email_formato("a@b.c") is False  # TLD <2
    # longitud >254
    largo = "a" * 250 + "@b.com"
    assert validar_email_formato(largo) is False


def test_hash_password_no_expone_claro_y_salt_distinto():
    """T03: hash_password != claro y dos hashes del mismo claro son distintos (salt)."""
    from app.services.auth_service import hash_password

    claro = "secreto123"
    h1 = hash_password(claro)
    h2 = hash_password(claro)
    assert h1 != claro
    assert h2 != claro
    assert h1 != h2
    assert h1.startswith("$2b$") or h1.startswith("$2a$")


def test_verificar_password():
    """T03: verificar_password correcto True, incorrecto False."""
    from app.services.auth_service import hash_password, verificar_password

    claro = "secreto123"
    h = hash_password(claro)
    assert verificar_password(claro, h) is True
    assert verificar_password("erronea", h) is False
    assert verificar_password("", h) is False


def test_hash_no_loguea_claro():
    """T03: ningún log expone claro/hash (verificación estática)."""
    from pathlib import Path

    content = Path("app/services/auth_service.py").read_text(encoding="utf-8")
    # no debe haber print/log que incluya password en claro
    assert (
        "print(" not in content
        or "password" not in content.lower().split("print(")[-1][:100]
    )
    # no debe loguear hash completo
    assert "logger" not in content.lower() or "password_hash" not in content.lower()
