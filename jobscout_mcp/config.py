"""Lecture de la configuration depuis le fichier .env (ou les variables d'environnement).

Les chemins sont absolus : Claude Desktop lance le serveur depuis un dossier
quelconque, un chemin relatif au dossier courant ne marcherait pas.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()

# Un chemin absolu est gardé tel quel, un chemin relatif part de la racine du projet.
CV_PATH = RACINE / os.path.expanduser(os.getenv("CV_PATH", "data/cv.pdf"))

# Les offres téléchargées sont gardées 6 h (Remotive demande max. 4 appels par jour).
CACHE_DIR = RACINE / "data" / "cache"
CACHE_DUREE_SECONDES = 6 * 60 * 60
