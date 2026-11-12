# LogiAI : starter de la séance « Tester, sécuriser et appeler l'API »

Suite du TP précédent : l'API LogiAI existe. Aujourd'hui vous la testez pour la casser, vous la protégez par une clé, puis une page web l'appelle.

## Installation (une fois)

    python -m venv .venv
    .venv\Scripts\activate.bat        # Windows cmd  (PowerShell : .venv\Scripts\Activate.ps1)
    source .venv/bin/activate         # macOS / Linux
    pip install -r requirements.txt
    python -m logiai.dataset
    python -m logiai.train

## Vos clés (fichier .env, jamais dans Git)

    copy .env.example .env            # macOS / Linux : cp .env.example .env
    # puis ouvrez .env et choisissez vos deux clés

## Lancer

    python -m uvicorn logiai.api.main:app --reload          # l'API, port 8000
    python -m http.server 5500 --directory web              # la page web, dans un 2e terminal
    # ouvrez http://localhost:5500

## Tester

    python -m pytest

## Structure

    atelier4/
    ├── logiai/                 # le paquet Python : config, dataset, train, predict
    │   └── api/                # main.py (routes, CORS), schemas.py (bornes), security.py (clés)
    ├── tests/                  # conftest.py (fixtures) + test_api, test_casser, test_limites, test_securite
    ├── web/index.html          # la page qui appelle l'API
    ├── docs/adr/003-securite.md
    ├── data/ et models/        # générés par dataset.py et train.py, non versionnés
    ├── .env                    # local, jamais versionné
    └── COMPTE_RENDU.md

## Où sont les trous (cherchez les TODO)

- `logiai/api/security.py` : deux fonctions à écrire
- `logiai/api/main.py` : protéger deux routes, ajouter le CORS
- `tests/test_casser.py` (4 cas à ajouter), `tests/test_limites.py` (cas limites à compléter), `tests/test_securite.py` (tests à écrire : ils échouent tant qu'ils ne sont pas écrits)
- `docs/adr/003-securite.md` : deux décisions à justifier
- `web/index.html` : le fetch et trois améliorations d'ergonomie
- Le projet contient **2 bugs volontaires** : vos tests doivent les trouver.
