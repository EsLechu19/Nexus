"""Base declarativa y sesión para SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


_settings = get_settings()
SQLALCHEMY_DATABASE_URL = _settings.database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)
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
