"""
ESG Optimizer MVP — Connexion DB (Hybride SQLite/Postgres).
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config import settings

url = settings.database_url

# --- Gestion de l'URL pour PostgreSQL (Railway) ---
# Railway peut fournir "postgres://" (sans "ql") ou "postgresql://"
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql+pg8000://", 1)
    connect_args = {}
elif url.startswith("postgresql://"):
    # On remplace par pg8000 pour éviter les erreurs de compilation psycopg2
    url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    connect_args = {}
else:
    # --- Gestion SQLite (Local) ---
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

def create_tables():
    """Crée toutes les tables en ignorant les erreurs de collision SQLite."""
    try:
        # On tente la création normale
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as e:
        # Si une erreur survient (ex: "table users already exists")
        # On vérifie si c'est juste un problème de table déjà existante
        if "already exists" in str(e).lower():
            pass # C'est ce qu'on veut, on ignore l'erreur
        else:
            # Si c'est une autre erreur, on veut quand même le savoir
            print(f"Note DB: {e}")
    