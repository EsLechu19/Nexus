"""Base declarativa y sesión para SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# URL por defecto para desarrollo local (SQLite). En producción vía .env Postgres.
SQLALCHEMY_DATABASE_URL = "sqlite:///nexus.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base para todos los modelos."""

    pass


def get_db():
    """Dependencia FastAPI que provee sesión DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
