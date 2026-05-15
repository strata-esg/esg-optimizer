"""
ESG Optimizer MVP - Router Stripe.
POST /stripe/webhook         -> Webhook Stripe (checkout.session.completed)
GET  /stripe/upgrade-url     -> Génère l'URL de Payment Link avec prefilled_email
GET  /stripe/my-subscription -> Retourne l'abonnement actif de l'utilisateur
"""

import logging
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Subscription, User
from backend.routers.auth import get_current_user
from backend.services.email_service import send_upgrade_confirmation_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe"])

# Configure Stripe SDK
stripe.api_key = settings.stripe_secret_key


# HELPERS

def _upgrade_user_plan(db: Session, user_id: int, new_plan: str) -> None:
    """Met à jour le plan de l'utilisateur en DB."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.plan = new_plan
        db.commit()
        logger.info("User %d upgraded to plan '%s'", user_id, new_plan)


def _detect_plan_from_session(session: dict) -> str:
    """
    Détecte le plan acheté à partir de la session Stripe.
    Ordre de priorité :
      1. payment_link ID (le plus fiable)
      2. mode/subscription_id (Pro = recurring, Essentiel = payment one-shot)
      3. fallback sur le montant
    """
    payment_link = session.get("payment_link")

    # Extraire l'ID du Payment Link depuis l'URL ou directement
    essentiel_id = _extract_payment_link_id(settings.stripe_link_essentiel)
    pro_id = _extract_payment_link_id(settings.stripe_link_pro)

    if payment_link and essentiel_id and payment_link == essentiel_id:
        return "essential"
    if payment_link and pro_id and payment_link == pro_id:
        return "pro"

    # FIX : un essai gratuit ou un code promo 100% met amount_total=0
    # -> on s'appuie sur le mode/subscription_id pour distinguer Pro (subscription) vs Essential (one-shot)
    mode = session.get("mode")
    subscription_id = session.get("subscription")
    if mode == "subscription" or subscription_id:
        return "pro"
    if mode == "payment":
        return "essential"

    # Fallback : vérifier le montant
    amount = session.get("amount_total", 0) or 0
    if amount:
        if amount <= 5000:  # <= 50€ -> Essentiel (39€)
            return "essential"
        else:  # > 50€ -> Pro (129€/mois)
            return "pro"

    return "essential"  # Default


def _extract_payment_link_id(url: str) -> str | None:
    """Extrait l'ID du Payment Link depuis l'URL Stripe (dernier segment)."""
    if not url:
        return None
    # https://buy.stripe.com/xxx -> xxx
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else None


# POST /stripe/webhook - Webhook Stripe

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """
    Reçoit les événements Stripe (checkout.session.completed).
    Vérifie la signature si STRIPE_WEBHOOK_SECRET est configuré.
    """
    body = await request.body()

    # Vérifier la signature Stripe (si configuré)
    if settings.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=stripe_signature or "",
                secret=settings.stripe_webhook_secret,
            )
        except stripe.SignatureVerificationError:
            logger.warning("Webhook Stripe : signature invalide")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signature webhook invalide.",
            )
        except Exception as e:
            logger.error("Webhook Stripe erreur : %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur webhook : {e}",
            )
    else:
        # En dev sans webhook secret, parser directement le JSON
        import json
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON invalide.",
            )

    # Événements traités :
    #   - checkout.session.completed : paiement classique
    #   - customer.subscription.created/updated : essai gratuit Pro (trial), changement de plan
    #   - customer.subscription.deleted : downgrade vers découverte
    event_type = event.get("type") if isinstance(event, dict) else event.type

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        sub_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        sub_obj_dict = sub_obj if isinstance(sub_obj, dict) else sub_obj.to_dict()
        sub_status_remote = sub_obj_dict.get("status")  # active, trialing, past_due, ...
        customer_id = sub_obj_dict.get("customer")

        # Récupère l'email via Stripe customer
        email_from_cust = None
        try:
            cust = stripe.Customer.retrieve(customer_id)
            email_from_cust = (cust.get("email") if isinstance(cust, dict) else cust.email)
        except Exception as e:
            logger.warning("Stripe Customer.retrieve échec : %s", e)

        if not email_from_cust:
            return {"status": "no_email_on_subscription"}

        target_user = db.query(User).filter(User.email == email_from_cust).first()
        if not target_user:
            return {"status": "user_not_found", "email": email_from_cust}

        # Plan = pro pour toute subscription active/en essai
        if sub_status_remote in ("active", "trialing"):
            _upgrade_user_plan(db, target_user.id, "pro")
            logger.info("Subscription %s -> user %s upgraded to PRO via %s",
                        sub_status_remote, target_user.email, event_type)
            return {"status": "ok", "plan": "pro", "user_id": target_user.id, "via": event_type}
        return {"status": "ignored_subscription_status", "remote_status": sub_status_remote}

    if event_type == "customer.subscription.deleted":
        sub_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        sub_obj_dict = sub_obj if isinstance(sub_obj, dict) else sub_obj.to_dict()
        customer_id = sub_obj_dict.get("customer")
        try:
            cust = stripe.Customer.retrieve(customer_id)
            email = cust.get("email") if isinstance(cust, dict) else cust.email
        except Exception:
            email = None
        if email:
            target_user = db.query(User).filter(User.email == email).first()
            if target_user:
                _upgrade_user_plan(db, target_user.id, "discovery")
                return {"status": "ok", "plan": "discovery", "user_id": target_user.id}
        return {"status": "deleted_no_user"}

    if event_type != "checkout.session.completed":
        return {"status": "ignored", "type": event_type}

    # Extraire la session
    session_data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object

    session_id = session_data.get("id") if isinstance(session_data, dict) else session_data.id
    customer_email = (
        session_data.get("customer_details", {}).get("email")
        if isinstance(session_data, dict)
        else getattr(session_data.get("customer_details", {}), "email", None)
    )
    customer_id = session_data.get("customer") if isinstance(session_data, dict) else session_data.customer
    subscription_id = session_data.get("subscription") if isinstance(session_data, dict) else session_data.subscription
    amount = session_data.get("amount_total", 0) if isinstance(session_data, dict) else session_data.amount_total
    payment_link = session_data.get("payment_link") if isinstance(session_data, dict) else session_data.payment_link

    logger.info(
        "Stripe checkout completed - email=%s, session=%s, amount=%s, payment_link=%s",
        customer_email, session_id, amount, payment_link,
    )

    # Trouver l'utilisateur par email
    if not customer_email:
        logger.warning("Webhook Stripe : pas d'email client dans la session %s", session_id)
        return {"status": "no_email"}

    user = db.query(User).filter(User.email == customer_email).first()
    if not user:
        logger.warning("Webhook Stripe : utilisateur %s introuvable", customer_email)
        return {"status": "user_not_found", "email": customer_email}

    # Vérifier doublon (même session_id déjà traitée)
    existing = db.query(Subscription).filter(Subscription.stripe_session_id == session_id).first()
    if existing:
        logger.info("Webhook Stripe : session %s déjà traitée", session_id)
        return {"status": "already_processed"}

    # Détecter le plan
    detected_plan = _detect_plan_from_session(
        session_data if isinstance(session_data, dict) else session_data.to_dict()
    )

    # Capturer le plan actuel AVANT upgrade - évite de renvoyer l'email si déjà à ce plan
    previous_plan = user.plan

    # Calculer l'expiration
    expires_at = None
    sub_status = "one_time"
    if detected_plan == "pro":
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        sub_status = "active"

    # Créer la subscription en DB
    subscription = Subscription(
        user_id=user.id,
        plan=detected_plan,
        status=sub_status,
        stripe_session_id=session_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        amount_cents=amount,
        expires_at=expires_at,
    )
    db.add(subscription)

    _upgrade_user_plan(db, user.id, detected_plan)

    if detected_plan == "essential":
        user.analyses_this_month = max(0, user.analyses_this_month - 1)
        db.commit()

    db.commit()

    logger.info(
        "Subscription créée - user=%d, plan=%s, session=%s",
        user.id, detected_plan, session_id,
    )

    # N'envoyer l'email que si c'est une vraie première upgrade vers ce plan
    # (évite le spam si Stripe retente le webhook ou si plusieurs sessions coexistent)
    if previous_plan != detected_plan:
        try:
            amount_display = f"{(amount or 0) / 100:.0f}€" if amount else None
            send_upgrade_confirmation_email(customer_email, detected_plan, amount_display)
        except Exception as email_exc:
            logger.warning("Email upgrade non envoyé : %s", email_exc)
    else:
        logger.info("Email upgrade non renvoyé - user %d déjà sur le plan %s", user.id, detected_plan)

    return {"status": "ok", "plan": detected_plan, "user_id": user.id}


@router.get("/upgrade-url")
def get_upgrade_url(
    plan: str,
    current_user: User = Depends(get_current_user),
):
    """Retourne l'URL Stripe Payment Link avec l'email pré-rempli."""
    if plan not in ("essential", "pro"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan invalide. Choisissez 'essential' ou 'pro'.",
        )

    if plan == "essential":
        base_url = settings.stripe_link_essentiel
    else:
        base_url = settings.stripe_link_pro

    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Le lien de paiement pour le plan '{plan}' n'est pas configuré.",
        )

    separator = "&" if "?" in base_url else "?"
    upgrade_url = f"{base_url}{separator}prefilled_email={current_user.email}"

    return {"url": upgrade_url, "plan": plan}


@router.get("/my-subscription")
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne la dernière subscription active de l'utilisateur."""
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["active", "one_time"]),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not sub:
        return {
            "has_subscription": False,
            "plan": current_user.plan,
            "status": None,
        }

    return {
        "has_subscription": True,
        "plan": sub.plan,
        "status": sub.status,
        "activated_at": sub.activated_at,
        "expires_at": sub.expires_at,
        "amount_cents": sub.amount_cents,
    }
