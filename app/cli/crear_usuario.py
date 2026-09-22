"""Comando CLI para crear usuario — fuera de API (RF-4, RNF-1)."""

import argparse
import sys

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.usuario import Usuario
from app.services.auth_service import (
    hash_password,
    normalizar_email,
    validar_email_formato,
)


def crear_usuario(email: str, password: str) -> Usuario:
    """Crea usuario con validaciones de RF-4. Lanza ValueError si falla."""
    email_norm = normalizar_email(email)
    if not validar_email_formato(email):
        raise ValueError("Email inválido")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.email == email_norm).first()
        if existente is not None:
            raise ValueError("Email ya existe")
        usuario = Usuario(email=email_norm, password_hash=hash_password(password))
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email ya existe") from exc
    finally:
        db.close()


def main() -> None:
    """Entry point para `python -m app.cli.crear_usuario`."""
    parser = argparse.ArgumentParser(description="Crear usuario administrativo")
    parser.add_argument("--email", required=True, help="Email del usuario")
    parser.add_argument(
        "--password", required=True, help="Contraseña (mínimo 8 caracteres)"
    )
    args = parser.parse_args()

    try:
        usuario = crear_usuario(args.email, args.password)
        print(f"Usuario creado: {usuario.email}")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def run() -> None:
    """Alias para compatibilidad."""
    main()


if __name__ == "__main__":
    main()
