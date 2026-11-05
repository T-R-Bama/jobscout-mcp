"""Données de test communes : quelques offres fictives, sans réseau ni LLM."""

import pytest
import requests

from jobscout_mcp import config, offres

OFFRES = [
    {"id": "arbeitnow:dev-python-paris", "source": "Arbeitnow", "titre": "Développeur Python",
     "entreprise": "Margo", "lieu": "Paris", "teletravail": False, "date": "2026-11-01",
     "tags": ["python", "django"], "url": "https://www.arbeitnow.fr/jobs/margo/dev-python-paris",
     "description": "Backend Python, Django et PostgreSQL."},
    {"id": "arbeitnow:devops-london", "source": "Arbeitnow", "titre": "DevOps Engineer",
     "entreprise": "Acme", "lieu": "London", "teletravail": False, "date": "2026-10-30",
     "tags": ["kubernetes"], "url": "https://www.arbeitnow.co.uk/jobs/acme/devops-london",
     "description": "Kubernetes, Terraform, AWS."},
    {"id": "remotive:42", "source": "Remotive", "titre": "Senior Python Developer",
     "entreprise": "Remote Co", "lieu": "Worldwide", "teletravail": True, "date": "2026-11-02",
     "tags": ["python", "fastapi"], "url": "https://remotive.com/remote-jobs/software-dev/senior-python-42",
     "description": "Python et FastAPI, 100 % à distance."},
]


@pytest.fixture(autouse=True)
def offres_fictives(monkeypatch):
    """Remplace les vraies sources par les offres ci-dessus, désactive Adzuna et interdit le réseau."""
    monkeypatch.setattr(offres, "_toutes_les_offres", lambda: [dict(o) for o in OFFRES])
    monkeypatch.setattr(config, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(config, "ADZUNA_APP_KEY", "")

    def pas_de_reseau(*args, **kwargs):
        raise AssertionError("Les tests ne doivent pas appeler Internet.")

    monkeypatch.setattr(requests, "get", pas_de_reseau)
    return OFFRES


@pytest.fixture
def anyio_backend():
    # Les tests asynchrones (client MCP) tournent avec asyncio, via le greffon pytest d'anyio.
    return "asyncio"
