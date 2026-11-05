"""Point d'entrée du serveur MCP JobScout (transport stdio).

Lancé par Claude Desktop ou l'inspecteur MCP avec le Python du .venv :
    .venv/bin/python serveur.py
"""

from jobscout_mcp.serveur import main, mcp  # noqa: F401  (mcp sert à « mcp dev serveur.py »)

if __name__ == "__main__":
    main()
