"""Le serveur MCP vu par un client : outils annoncés, appels, erreurs.

Le client MCP du SDK se connecte au serveur dans le même processus : on teste
le vrai protocole (liste des outils, schémas, appels) sans réseau ni LLM.
"""

import json
import sys
from pathlib import Path

import pytest
import requests
from mcp import Client, StdioServerParameters

from jobscout_mcp import config, offres, serveur
from tests.conftest import OFFRES

PARIS, LONDRES, REMOTIVE = OFFRES
RACINE = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.anyio


async def test_outils_annonces():
    async with Client(serveur.mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
    assert set(outils) == {"search_jobs", "get_job_details", "read_cv"}
    # Le schéma est déduit de la signature Python : seul mots_cles est obligatoire.
    schema = outils["search_jobs"].input_schema
    assert schema["required"] == ["mots_cles"]
    assert schema["properties"]["max_resultats"]["maximum"] == 10
    # Tous les outils sont en lecture seule.
    assert all(o.annotations.read_only_hint for o in outils.values())


async def test_adzuna_cite_seulement_s_il_est_actif():
    async with Client(serveur.mcp) as client:
        description = {o.name: o for o in (await client.list_tools()).tools}["search_jobs"].description
    assert "Arbeitnow" in description and "Adzuna" not in description


async def test_search_jobs_renvoie_les_vrais_liens():
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("search_jobs", {"mots_cles": "python", "lieu": "France"})
    assert not resultat.is_error
    trouvees = resultat.structured_content["result"]
    assert [o["id"] for o in trouvees] == [PARIS["id"]]
    assert trouvees[0]["url"] == PARIS["url"]


async def test_search_jobs_refuse_max_resultats_hors_limites():
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("search_jobs", {"mots_cles": "python", "max_resultats": 50})
    assert resultat.is_error


async def test_get_job_details():
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("get_job_details", {"id_offre": LONDRES["id"]})
    assert json.loads(resultat.content[0].text)["entreprise"] == "Acme"


async def test_get_job_details_id_inconnu_est_une_erreur():
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("get_job_details", {"id_offre": "remotive:999"})
    assert resultat.is_error
    assert "search_jobs" in resultat.content[0].text


async def test_site_injoignable_donne_un_message_clair(monkeypatch):
    def panne():
        raise requests.ConnectionError("pas de réseau")

    monkeypatch.setattr(offres, "_toutes_les_offres", panne)
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("search_jobs", {"mots_cles": "python"})
    assert resultat.is_error
    assert "injoignable" in resultat.content[0].text


async def test_read_cv(monkeypatch, tmp_path):
    cv = tmp_path / "cv.md"
    cv.write_text("Développeur Python junior, RAG et agents IA.")
    monkeypatch.setattr(config, "CV_PATH", cv)
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("read_cv", {})
    assert "RAG" in resultat.content[0].text


async def test_read_cv_absent_est_une_erreur(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CV_PATH", tmp_path / "absent.pdf")
    async with Client(serveur.mcp) as client:
        resultat = await client.call_tool("read_cv", {})
    assert resultat.is_error
    assert "CV_PATH" in resultat.content[0].text


async def test_prompt_offres_pour_mon_cv():
    async with Client(serveur.mcp) as client:
        prompt = await client.get_prompt("offres_pour_mon_cv", {"lieu": "Lyon"})
    texte = prompt.messages[0].content.text
    assert "read_cv" in texte and "Lyon" in texte


async def test_demarre_en_stdio_comme_dans_claude_desktop():
    # Lance vraiment serveur.py dans un sous-processus, comme le fait Claude Desktop.
    # Lister les outils ne télécharge aucune offre : pas de réseau ici non plus.
    parametres = StdioServerParameters(command=sys.executable, args=[str(RACINE / "serveur.py")])
    async with Client(parametres) as client:
        noms = {o.name for o in (await client.list_tools()).tools}
    assert noms == {"search_jobs", "get_job_details", "read_cv"}
