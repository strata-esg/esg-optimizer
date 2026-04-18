"""
ESG Optimizer MVP — Modèles SQLAlchemy (4 tables : users, companies, analyses, public_analyses).
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    plan = Column(String(20), default="discovery")  # 'discovery' | 'essential' | 'pro' | 'enterprise'
    analyses_this_month = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    # Relations
    companies = relationship("Company", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# COMPANIES
# ──────────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_company_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    # Relations
    owner = relationship("User", back_populates="companies")
    analyses = relationship("Analysis", back_populates="company", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# ANALYSES
# ──────────────────────────────────────────────
class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_year = Column(Integer, nullable=True)

    # Fichier source
    source_filename = Column(String(255), nullable=False)
    source_format = Column(String(10), nullable=True)  # pdf, docx, xlsx

    # Scores ESG (0-100)
    score_env = Column(Float, nullable=True)
    score_social = Column(Float, nullable=True)
    score_gov = Column(Float, nullable=True)
    score_global = Column(Float, nullable=True)

    # Conformité CSRD
    csrd_ready = Column(Boolean, nullable=True)
    csrd_coverage_pct = Column(Float, nullable=True)
    missing_disclosures = Column(Text, nullable=True)  # JSON array

    # Résultats détaillés (stockés en JSON strings)
    kpis_detected = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    esrs_coverage = Column(Text, nullable=True)  # JSON {E1: bool, ...}
    executive_summary = Column(Text, nullable=True)
    raw_llm_response = Column(Text, nullable=True)

    # Deltas (vs analyse précédente)
    delta_env = Column(Float, nullable=True)
    delta_social = Column(Float, nullable=True)
    delta_gov = Column(Float, nullable=True)
    delta_global = Column(Float, nullable=True)
    delta_narrative = Column(Text, nullable=True)

    # Métadonnées
    processing_time_s = Column(Float, nullable=True)
    status = Column(String(20), default="pending")  # pending | processing | success | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    # Relations
    company = relationship("Company", back_populates="analyses")
    user = relationship("User", back_populates="analyses")


# ──────────────────────────────────────────────
# PUBLIC ANALYSES (quick-check sans auth)
# ──────────────────────────────────────────────
def _token_default() -> str:
    return str(uuid.uuid4())


def _expiry_default() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=72)


class PublicAnalysis(Base):
    __tablename__ = "public_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(36), unique=True, nullable=False, default=_token_default, index=True)
    ip_hash = Column(String(64), nullable=False, index=True)  # SHA-256 de l'IP

    # Résultats quick-check (limités)
    score_global = Column(Float, nullable=True)
    csrd_ready = Column(Boolean, nullable=True)
    teaser_strengths = Column(Text, nullable=True)   # JSON array (top 3)
    teaser_weaknesses = Column(Text, nullable=True)  # JSON array (top 3)

    # Résultats complets (stockés pour claim post-inscription)
    full_response = Column(Text, nullable=True)      # JSON complet du LLM

    # Métadonnées
    source_filename = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")    # pending | processing | success | failed
    error_message = Column(Text, nullable=True)
    processing_time_s = Column(Float, nullable=True)
    expires_at = Column(DateTime, default=_expiry_default)
    claimed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
