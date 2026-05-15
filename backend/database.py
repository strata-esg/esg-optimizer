"""
ESG Optimizer MVP - Connexion DB (hybride SQLite / Postgres).
"""
import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)

url = settings.database_url

# --- Gestion de l'URL pour PostgreSQL (Railway) ---
# Railway peut fournir "postgres://" (sans "ql") ou "postgresql://".
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql+pg8000://", 1)
    connect_args = {}
elif url.startswith("postgresql://"):
    # On passe par pg8000 pour éviter la compilation de psycopg2.
    url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    connect_args = {}
else:
    # --- Gestion SQLite (local) ---
    _db_path = url.replace("sqlite:///", "")
    if _db_path:
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False}

engine = create_engine(
    url,
    connect_args=connect_args,
    echo=settings.is_dev,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def get_db():
    """Dependency FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_light_migrations() -> None:
    """
    Ajoute les colonnes manquantes sur les bases déjà existantes.

    SQLAlchemy ne fait que créer les tables absentes : il ne modifie jamais une
    table existante. On applique ici les quelques ALTER nécessaires, à la main,
    de façon compatible SQLite et PostgreSQL.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    statements: list[str] = []

    if "clerk_id" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN clerk_id VARCHAR(255)")
    if "full_name" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_clerk_id ON users (clerk_id)")
        )
    logger.info("Migrations légères appliquées : %s", ", ".join(statements))


def create_tables():
    """Crée les tables manquantes puis applique les migrations légères."""
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as exc:
        # Une collision "table already exists" est attendue et sans gravité.
        if "already exists" not in str(exc).lower():
            logger.warning("Création des tables : %s", exc)

    try:
        _run_light_migrations()
    except Exception as exc:
        logger.warning("Migrations légères ignorées : %s", exc)
