"""Le serveur MCP : expose la recherche d'offres de JobScout à n'importe quel client MCP.

Dans JobScout, c'est ma propre boucle d'agent qui décrivait les outils au modèle
(schémas JSON écrits à la main) et les exécutait. Ici, le SDK MCP officiel fait
ce travail : il lit la signature et la docstring de chaque fonction, en déduit le
schéma, et c'est le client (Claude Desktop, l'inspecteur MCP…) qui choisit quand
appeler l'outil.

Transport stdio : le client lance ce fichier et lui parle par l'entrée et la
sortie standard. Conséquence importante : ne jamais écrire avec print() dans ce
serveur, la sortie standard est réservée aux messages du protocole.
"""

from typing import Annotated

import requests
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from jobscout_mcp import config, offres

mcp = MCPServer(
    "JobScout",
    version="0.1.0",
    instructions=(
        "Outils de recherche d'offres d'emploi (Arbeitnow, Remotive). Les offres sont surtout en anglais : "
        "utilise des mots-clés en anglais. Cite toujours le lien 'url' renvoyé par search_jobs, n'en invente jamais."
    ),
)

# Outils en lecture seule qui interrogent des sites extérieurs : le client peut s'en servir
# pour décider s'il demande une confirmation à l'utilisateur.
LECTURE_WEB = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


def _site_injoignable(erreur: requests.RequestException) -> ToolError:
    # Une ToolError arrive au client comme résultat en erreur (isError) avec ce message lisible ;
    # toute autre exception ne donnerait qu'un « Error executing tool » sans explication.
    return ToolError(f"Site d'offres injoignable, réessaie plus tard ({type(erreur).__name__}).")


def _sources() -> str:
    actives = ["Arbeitnow (Europe, dont la France)", "Remotive (télétravail)"]
    if config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY:
        actives.append("Adzuna (France)")
    return ", ".join(actives)


@mcp.tool(name="search_jobs", title="Chercher des offres d'emploi", annotations=LECTURE_WEB,
          description=(
              f"Cherche des offres d'emploi sur {_sources()}. Les offres sont surtout en anglais : "
              "privilégie des mots-clés en anglais (ex. 'python developer') et réessaie avec d'autres mots "
              "si les résultats sont maigres. Renvoie une liste résumée (id, titre, entreprise, lieu, lien) ; "
              "la description complète s'obtient avec get_job_details."
          ))
def search_jobs(
    mots_cles: Annotated[str, Field(description="Mots-clés, de préférence en anglais.")],
    lieu: Annotated[str, Field(description="Ville ou pays (ex. 'Paris', 'France', 'Royaume-Uni'). Vide = partout.")] = "",
    teletravail_seulement: Annotated[bool, Field(description="true pour ne garder que le télétravail.")] = False,
    max_resultats: Annotated[int, Field(ge=1, le=10, description="Nombre maximum d'offres (1 à 10).")] = 5,
) -> list[dict]:
    try:
        return offres.chercher_offres(mots_cles, lieu, teletravail_seulement, max_resultats)
    except requests.RequestException as erreur:
        raise _site_injoignable(erreur) from erreur


@mcp.tool(name="get_job_details", title="Détail d'une offre", annotations=LECTURE_WEB)
def get_job_details(
    id_offre: Annotated[str, Field(description="L'id renvoyé par search_jobs (ex. 'remotive:123').")],
) -> dict:
    """Renvoie le détail complet d'une offre (description, tags, salaire…) à partir de son id."""
    try:
        detail = offres.lire_offre(id_offre)
    except requests.RequestException as erreur:
        raise _site_injoignable(erreur) from erreur
    if "erreur" in detail:
        raise ToolError(detail["erreur"] + " Utilise d'abord search_jobs pour obtenir un id valide.")
    return detail


@mcp.tool(name="read_cv", title="Lire mon CV", annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def read_cv() -> str:
    """Renvoie le texte du CV de l'utilisateur. À n'appeler que si la demande parle de son profil
    (« pour moi », « mon CV », « qui me correspondent »)."""
    texte = offres.lire_cv()
    if texte.startswith("Erreur"):
        raise ToolError(texte + " Indique le chemin de ton CV dans la variable CV_PATH.")
    return texte


@mcp.prompt(name="offres_pour_mon_cv", title="Offres adaptées à mon CV")
def offres_pour_mon_cv(lieu: str = "France") -> str:
    """Modèle de demande prêt à l'emploi : chercher des offres et les comparer au CV."""
    return (
        f"Lis mon CV avec read_cv, puis cherche avec search_jobs des offres qui me correspondent ({lieu} ou "
        "télétravail). Essaie plusieurs jeux de mots-clés en anglais tirés de mon CV. Pour les 3 meilleures, "
        "lis le détail avec get_job_details et explique ce qui correspond et ce qui manque. "
        "Donne le lien de chaque offre, tel que renvoyé par les outils."
    )


def main() -> None:
    mcp.run()  # transport stdio par défaut


if __name__ == "__main__":
    main()
