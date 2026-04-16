"""
ESG Optimizer MVP — Schémas Pydantic (validation request/response).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ══════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    company_name: Optional[str]
    plan: str
    analyses_this_month: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # On supprime la ligne 'user: UserResponse'


class RegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# COMPANY
# ══════════════════════════════════════════════

class CompanyResponse(BaseModel):
    id: int
    name: str
    sector: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════
# ANALYSIS — Upload request
# ══════════════════════════════════════════════

class AnalysisUploadMeta(BaseModel):
    """Métadonnées envoyées avec le fichier (form fields)."""
    company_name: str = Field(min_length=1, max_length=255)
    report_year: int = Field(ge=2000, le=2100)
    sector: Optional[str] = None


# ══════════════════════════════════════════════
# ANALYSIS — Scores & résultats (sous-schémas)
# ══════════════════════════════════════════════

class ESRSCoverage(BaseModel):
    E1_climate_change: bool = False
    E2_pollution: bool = False
    E3_water_marine: bool = False
    E4_biodiversity: bool = False
    E5_circular_economy: bool = False
    S1_own_workforce: bool = False
    S2_value_chain_workers: bool = False
    S3_affected_communities: bool = False
    S4_consumers: bool = False
    G1_business_conduct: bool = False


class KPI(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    esrs_reference: Optional[str] = None
    pillar: str  # E | S | G


class StrengthWeakness(BaseModel):
    pillar: str  # E | S | G
    description: str


class Recommendation(BaseModel):
    priority: int = Field(ge=1, le=5)
    pillar: str
    action: str
    expected_impact: Optional[str] = None
    esrs_reference: Optional[str] = None


# ══════════════════════════════════════════════
# ANALYSIS — Réponse complète
# ══════════════════════════════════════════════

class AnalysisResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    report_year: Optional[int]

    source_filename: str
    source_format: Optional[str]

    # Scores
    score_env: Optional[float]
    score_social: Optional[float]
    score_gov: Optional[float]
    score_global: Optional[float]

    # CSRD
    csrd_ready: Optional[bool]
    csrd_coverage_pct: Optional[float]
    missing_disclosures: Optional[list[str]] = None

    # Détails
    kpis_detected: Optional[list[KPI]] = None
    strengths: Optional[list[StrengthWeakness]] = None
    weaknesses: Optional[list[StrengthWeakness]] = None
    recommendations: Optional[list[Recommendation]] = None
    esrs_coverage: Optional[ESRSCoverage] = None
    executive_summary: Optional[str] = None

    # Deltas
    delta_env: Optional[float] = None
    delta_social: Optional[float] = None
    delta_gov: Optional[float] = None
    delta_global: Optional[float] = None
    delta_narrative: Optional[str] = None

    # Méta
    processing_time_s: Optional[float]
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisCreatedResponse(BaseModel):
    """Réponse immédiate après POST /analysis/upload."""
    analysis_id: int
    status: str = "processing"


# ══════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════

class AnalysisSummary(BaseModel):
    """Version allégée pour les listes d'historique."""
    id: int
    company_name: str
    report_year: Optional[int]
    score_global: Optional[float]
    csrd_ready: Optional[bool]
    status: str
    created_at: datetime


class HistoryResponse(BaseModel):
    analyses: list[AnalysisSummary]
    total: int
    page: int
    per_page: int


class StatsResponse(BaseModel):
    total_analyses: int
    avg_score_env: Optional[float]
    avg_score_social: Optional[float]
    avg_score_gov: Optional[float]
    avg_score_global: Optional[float]
    csrd_ready_pct: Optional[float]


# ══════════════════════════════════════════════
# GENERIC
# ══════════════════════════════════════════════

class ErrorResponse(BaseModel):
    detail: str
