import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Analysis, Company, User
from backend.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.services.clerk_auth import verify_clerk_token
from backend.services.analytics_service import ph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Valeur sentinelle pour le champ password_hash des comptes gérés par Clerk :
# ce n'est pas un hash bcrypt valide, donc la connexion locale échouera toujours.
_CLERK_MANAGED_PASSWORD = "clerk-managed"


def _get_or_create_clerk_user(db: Session, payload: dict) -> User:
    """
    Récupère le compte lié à un identifiant Clerk, ou le crée à la volée.

    Le frontend Next.js gère l'inscription via Clerk : la première requête API
    d'un nouvel utilisateur déclenche la création de son compte côté backend.
    """
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide")

    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if user is not None:
        return user

    # L'e-mail et le nom ne sont présents que si le template de jeton de session
    # Clerk les expose. On prévoit donc un repli propre.
    email = payload.get("email") or payload.get("email_address") or f"{clerk_id}@clerk.local"
    full_name = payload.get("name") or payload.get("full_name")

    # Si un compte existe déjà avec cet e-mail, on le retourne directement
    # (qu'il ait déjà un clerk_id ou non) pour éviter les doublons.
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        if existing.clerk_id is None:
            existing.clerk_id = clerk_id
        if full_name and not existing.full_name:
            existing.full_name = full_name
        try:
            db.commit()
            db.refresh(existing)
        except Exception:
            db.rollback()
            db.refresh(existing)
        return existing

    user = User(
        clerk_id=clerk_id,
        email=email,
        full_name=full_name,
        password_hash=_CLERK_MANAGED_PASSWORD,
        plan="discovery",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Compte créé via Clerk - user=%d, clerk_id=%s", user.id, clerk_id)
    return user


# Dépendance : extraire le user courant depuis le jeton d'authentification.
# Deux formats sont acceptés :
#  1. jeton de session Clerk (RS256) envoyé par le frontend Next.js
#  2. JWT interne (HS256) envoyé par le frontend Streamlit historique
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    clerk_payload = verify_clerk_token(token)
    if clerk_payload is not None:
        return _get_or_create_clerk_user(db, clerk_payload)

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user


# POST /auth/register
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        company_name=body.company_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.email)

    logger.info("Inscription réussie - user=%d, email=%s", user.id, user.email)

    # PostHog : identifier le nouvel utilisateur
    ph.identify(user.id, email=user.email, plan=user.plan, company_name=user.company_name or "")
    ph.capture(user.id, "user_signed_up", {"plan": user.plan})

    return RegisterResponse(user=UserResponse.model_validate(user), access_token=token)


# POST /auth/login
@router.post("/login", response_model=TokenResponse)
def login(body: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, token_type="bearer")


# GET /auth/me
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# PATCH /auth/profile
@router.patch("/profile", response_model=UserResponse)
def update_profile(
    full_name: str | None = None,
    company_name: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Met à jour le profil utilisateur (nom, entreprise) depuis le questionnaire d'onboarding.
    """
    if full_name is not None:
        current_user.full_name = full_name.strip()
    if company_name is not None:
        current_user.company_name = company_name.strip()
    db.commit()
    db.refresh(current_user)
    logger.info("update_profile: user=%d, full_name=%s, company_name=%s", current_user.id, full_name, company_name)
    return UserResponse.model_validate(current_user)


# PATCH /auth/sync-email
# Le frontend Next.js appelle cet endpoint après connexion pour s'assurer
# que l'email stocké dans la DB correspond à l'email Clerk réel.
# Utile quand le token Clerk ne contient pas le champ "email" dans le payload.
@router.patch("/sync-email")
def sync_email(
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Met à jour l'email de l'utilisateur si c'est un email @clerk.local (généré par défaut).
    Fusionne aussi avec un compte existant ayant cet email si nécessaire.
    """
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide.")

    email = email.strip().lower()

    # Si l'email est déjà correct, rien à faire
    if current_user.email.lower() == email:
        return UserResponse.model_validate(current_user)

    # Chercher si un compte avec ce vrai email existe déjà (compte Streamlit historique)
    existing = db.query(User).filter(User.email == email, User.id != current_user.id).first()
    if existing and existing.clerk_id is None:
        # Fusionner : transférer les analyses du compte Streamlit vers le compte Clerk
        db.query(Analysis).filter(Analysis.user_id == existing.id).update(
            {"user_id": current_user.id}, synchronize_session=False
        )
        # Transférer les companies
        db.query(Company).filter(Company.user_id == existing.id).update(
            {"user_id": current_user.id}, synchronize_session=False
        )
        db.commit()
        # Supprimer l'ancien compte doublon (plan, quota -> copier si plus avantageux)
        if existing.plan not in ("discovery", "free"):
            current_user.plan = existing.plan
        current_user.analyses_this_month = max(
            current_user.analyses_this_month, existing.analyses_this_month
        )
        db.delete(existing)
        logger.info(
            "sync-email: fusion compte Streamlit user=%d (email=%s) -> clerk user=%d",
            existing.id, email, current_user.id,
        )

    # Mettre à jour l'email du compte courant
    current_user.email = email
    db.commit()
    db.refresh(current_user)
    logger.info("sync-email: user=%d email mis à jour -> %s", current_user.id, email)
    return UserResponse.model_validate(current_user)