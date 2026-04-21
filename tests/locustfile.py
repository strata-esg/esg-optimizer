"""
ESG Optimizer MVP — Tests de charge (Sprint 6H).

Simule 10 utilisateurs concurrents qui parcourent le scénario complet :
  1. Register (ou login si existant)
  2. Appel /auth/me (session valide)
  3. Appel /history
  4. Quick-check public (endpoint le plus exposé au trafic)
  5. Healthcheck

Lancement :
  # 1. Backend tourne sur http://localhost:8000
  # 2. Dans un autre terminal :
  locust -f tests/locustfile.py --host http://localhost:8000

  # Puis ouvrir http://localhost:8089 et lancer :
  #   Number of users = 10
  #   Spawn rate      = 2 users/s
  #   Run time        = 5m

Critères d'acceptation :
  - 0 erreur 500
  - p95 < 2 s sur /auth/me et /history
  - p95 < 5 s sur le quick-check (contient un appel OpenAI)
  - Si SQLite lock errors → migrer vers Postgres avant prod

Mode headless (CI) :
  locust -f tests/locustfile.py --host http://localhost:8000 \
         --users 10 --spawn-rate 2 --run-time 3m --headless \
         --csv results/load_test
"""

import io
import random
import string
import time
from pathlib import Path

from locust import HttpUser, between, task, events


# --- Utilitaires --------------------------------------------------------
def random_email() -> str:
    """Génère un email unique pour chaque user virtuel."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{suffix}@esg-optimizer.test"


def fake_pdf_bytes() -> bytes:
    """Génère un mini PDF valide de ~2 Ko pour simuler un upload.
    On n'utilise PAS le vrai rapport_2023.pdf (25+ Mo) : trop coûteux en bande passante.
    """
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 76>>stream\nBT /F1 12 Tf 72 720 Td "
        b"(Rapport de durabilite 2024 - Scope 1 2 3 GHG) Tj ET\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f\ntrailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n0\n%%EOF\n"
    )


# --- User virtuel : parcours complet ------------------------------------
class ESGOptimizerUser(HttpUser):
    """Simule un utilisateur PME qui découvre le produit."""

    # Temps entre 2 actions : entre 1 et 3 secondes (comportement réaliste)
    wait_time = between(1, 3)

    def on_start(self):
        """Chaque user virtuel crée un compte au démarrage."""
        self.email = random_email()
        self.password = "LoadTest!2026"
        self.token = None

        # Register
        r = self.client.post(
            "/auth/register",
            json={"email": self.email, "password": self.password, "company": "Loadtest Co"},
            name="POST /auth/register",
        )
        if r.status_code in (200, 201):
            self.token = r.json().get("access_token")
        elif r.status_code == 409:
            # Compte déjà existant → login
            r2 = self.client.post(
                "/auth/login",
                data={"username": self.email, "password": self.password},
                name="POST /auth/login",
            )
            if r2.status_code == 200:
                self.token = r2.json().get("access_token")

        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(5)
    def health(self):
        """Endpoint le plus appelé (railway healthcheck + front polling)."""
        self.client.get("/health", name="GET /health")

    @task(3)
    def me(self):
        """Vérifie que la session est valide — proxy pour toute action authentifiée."""
        self.client.get("/auth/me", name="GET /auth/me")

    @task(2)
    def history(self):
        """Dashboard historique."""
        self.client.get("/history", name="GET /history")

    @task(1)
    def public_quick_check(self):
        """Endpoint public (quick-check) — le plus sensible car sans auth + appel OpenAI."""
        files = {
            "file": ("rapport_test.pdf", io.BytesIO(fake_pdf_bytes()), "application/pdf"),
        }
        data = {"email": self.email, "company": "Loadtest Co"}
        with self.client.post(
            "/public/quick-check",
            files=files,
            data=data,
            name="POST /public/quick-check",
            catch_response=True,
        ) as resp:
            # On tolère 429 (rate limit) : c'est le comportement attendu
            if resp.status_code == 429:
                resp.success()
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")


# --- Hooks : rapport de fin -------------------------------------------
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Affiche un résumé santé à la fin du run."""
    stats = environment.stats.total
    print("\n" + "=" * 70)
    print("SPRINT 6H — TESTS DE CHARGE — RÉSUMÉ")
    print("=" * 70)
    print(f"  Requêtes totales   : {stats.num_requests}")
    print(f"  Échecs             : {stats.num_failures} ({stats.fail_ratio * 100:.2f} %)")
    print(f"  RPS moyen          : {stats.total_rps:.2f}")
    print(f"  Latence médiane    : {stats.median_response_time} ms")
    print(f"  Latence p95        : {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Latence p99        : {stats.get_response_time_percentile(0.99):.0f} ms")

    verdict_ok = (
        stats.fail_ratio < 0.01
        and stats.get_response_time_percentile(0.95) < 5000
    )
    if verdict_ok:
        print("\n  ✅ VERDICT : SQLite tient la charge → OK pour déployer")
    else:
        print("\n  ❌ VERDICT : Migrer vers Postgres AVANT de déployer en prod")
        print("     (Railway offre un addon Postgres managed en 5 min)")
    print("=" * 70 + "\n")
