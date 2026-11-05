"""Logique de recherche reprise de JobScout : on vérifie que la copie se comporte pareil."""

from jobscout_mcp import offres
from tests.conftest import OFFRES

PARIS, LONDRES, REMOTIVE = OFFRES


def test_lieu_par_ville_ou_par_pays():
    # Le lieu de l'offre ne dit que « Paris » : le pays vient du site d'origine (.fr).
    assert offres._au_bon_endroit(PARIS, "paris")
    assert offres._au_bon_endroit(PARIS, "France")
    assert offres._au_bon_endroit(LONDRES, "Royaume-Uni")
    assert not offres._au_bon_endroit(LONDRES, "France")


def test_recherche_classe_par_nombre_de_mots_cles_trouves():
    resultats = offres.chercher_offres("python fastapi")
    assert [r["id"] for r in resultats] == [REMOTIVE["id"], PARIS["id"]]


def test_recherche_teletravail_seulement():
    assert [r["id"] for r in offres.chercher_offres("python", teletravail_seulement=True)] == [REMOTIVE["id"]]


def test_mot_entier_seulement():
    assert not offres._contient("maintain the roadmap", "ai")


def test_lire_offre_inconnue():
    assert "erreur" in offres.lire_offre("arbeitnow:inexistante")
