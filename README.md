# LogiAI — API REST de prédiction du risque de retard

Une société de transport veut prévenir ses dispatchers quand une livraison risque d'arriver en retard.
Le modèle de machine learning est exposé par une API REST (FastAPI) : un client envoie les
caractéristiques d'une livraison en JSON et reçoit une probabilité de retard, avec une alerte au-delà
du seuil de 0,4.

**Binôme :** Aymen Ichqarrane, Ihssane Moutchou — **Groupe :** G3
**Module :** Développement et déploiement d'applications intelligentes — EMSI, 4e année IA & Data Science

## Sommaire

- [Fonctionnement](#fonctionnement)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Données et modèle](#données-et-modèle)
- [Lancer l'API](#lancer-lapi)
- [Tester l'API](#tester-lapi)
- [Client Streamlit](#client-streamlit)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Contrat de l'API](#contrat-de-lapi)
- [Routes](#routes)
- [Auteurs](#auteurs)

## Fonctionnement

```
[ Streamlit ] --\
[ curl      ] ---- HTTP/JSON --> [ API FastAPI + modèle ] --> { probabilite_retard, alerte, ... }
[ Swagger   ] --/
```

Le modèle est chargé **une seule fois** au démarrage de l'API (fonction `lifespan`), puis partagé par
toutes les requêtes. Les clients ne contiennent pas le modèle : ils appellent `/v1/predict`.

## Prérequis

- Python 3.10 ou plus récent
- Git
- Windows, macOS ou Linux

## Installation

Depuis la racine du projet :

```bash
python -m venv .venv
```

Activer l'environnement virtuel :

```bash
# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux / Git Bash
source .venv/Scripts/activate   # Git Bash
source .venv/bin/activate       # macOS / Linux
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Données et modèle

Le jeu de données et le modèle ne sont pas versionnés (voir `.gitignore`) : ils se régénèrent.

```bash
python -m logiai.dataset     # écrit data/livraisons.csv (5000 lignes synthétiques)
python -m logiai.train       # écrit models/model.joblib et models/model_info.json
```

Métriques obtenues à l'entraînement :

| Métrique | Valeur |
|---|---|
| Accuracy baseline (« toujours à l'heure ») | 0,726 |
| Accuracy du modèle | 0,774 |
| Rappel | 0,464 |
| Précision | 0,617 |
| AUC | 0,769 |

## Lancer l'API

```bash
python -m uvicorn logiai.api.main:app --reload
```

- Documentation interactive : <http://localhost:8000/docs>
- Santé du service : <http://localhost:8000/health>

`/health` renvoie `{"status": "ok", "model_loaded": true}` quand le modèle est chargé. Si
`models/model.joblib` est absent, l'API démarre quand même, `/health` indique `model_loaded: false`
et `/v1/predict` répond **503** avec un message explicite.

## Tester l'API

Le plus simple est Swagger : ouvrir <http://localhost:8000/docs>, déplier `POST /v1/predict`, cliquer
sur *Try it out*, coller le JSON ci-dessous puis *Execute*.

```json
{"distance_km": 120, "poids_kg": 450, "heure_depart": 17, "pluie_mm": 8, "trafic_index": 7.5, "nb_arrets": 4, "type_vehicule": "camion"}
```

En ligne de commande, sous Git Bash / macOS / Linux :

```bash
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"distance_km":120,"poids_kg":450,"heure_depart":17,"pluie_mm":8,"trafic_index":7.5,"nb_arrets":4,"type_vehicule":"camion"}'
```

Sous Windows (cmd ou PowerShell), mettre le JSON dans `livraison.json` puis :

```bat
curl.exe -X POST http://localhost:8000/v1/predict -H "Content-Type: application/json" --data-binary @livraison.json
```

Réponse attendue (HTTP 200) :

```json
{"probabilite_retard": 0.732, "alerte": true, "seuil": 0.4, "model_version": "1.0"}
```

Une pluie de 500 mm renvoie **422** : la valeur dépasse la borne `le=100` du schéma Pydantic.

## Client Streamlit

L'API doit tourner dans un terminal. Dans un second terminal :

```bash
python -m streamlit run streamlit_app.py
```

L'interface s'ouvre sur <http://localhost:8501>. Elle ne contient ni scikit-learn ni le modèle : elle
envoie les 7 valeurs à l'API et affiche la probabilité, l'alerte, ou un message si l'API est
injoignable.

## Tests

```bash
python -m pytest
```

Résultat attendu : **15 passed** (13 tests du starter + 2 tests ajoutés : heure de départ 24 refusée,
cohérence de l'alerte avec le seuil).

## Structure du projet

```
.
├── logiai/
│   ├── config.py           # chemins, seuil 0,4, noms des variables
│   ├── dataset.py          # fabrique les données synthétiques
│   ├── train.py            # entraîne et sauvegarde le modèle
│   ├── predict.py          # charge le modèle et calcule une prédiction
│   └── api/
│       ├── main.py         # application FastAPI, routes /health et /v1/predict
│       └── schemas.py      # schémas Pydantic (Livraison, PredictionOut)
├── tests/
│   └── test_api.py         # banc d'essai de l'API
├── data/                   # livraisons.csv (généré, non versionné)
├── models/                 # model.joblib, model_info.json (générés, non versionnés)
├── streamlit_app.py        # client Streamlit
├── COMPTE_RENDU.md         # compte rendu du TP
├── requirements.txt
└── README.md
```

## Contrat de l'API

### Entrée : `Livraison` (7 champs)

| Variable | Type | Bornes | Sens |
|---|---|---|---|
| `distance_km` | nombre | 1 à 1000 | distance du trajet (km) |
| `poids_kg` | nombre | 0,1 à 5000 | poids transporté (kg) |
| `heure_depart` | entier | 0 à 23 | heure de départ |
| `pluie_mm` | nombre | 0 à 100 | pluie prévue sur le trajet (mm) |
| `trafic_index` | nombre | 0 à 10 | 0 = fluide, 10 = saturé |
| `nb_arrets` | entier | 0 à 30 | nombre d'arrêts de livraison |
| `type_vehicule` | texte | `moto`, `fourgon`, `camion` | type de véhicule |

Les champs inconnus sont refusés (`extra="forbid"`). Seuil d'alerte : **0,4**.

### Sortie : `PredictionOut`

| Champ | Type | Sens |
|---|---|---|
| `probabilite_retard` | nombre | probabilité de retard, entre 0 et 1 |
| `alerte` | booléen | `true` si la probabilité atteint le seuil |
| `seuil` | nombre | seuil utilisé (0,4) |
| `model_version` | texte | version du modèle |

## Routes

| Méthode | Route | Rôle | Codes |
|---|---|---|---|
| GET | `/health` | état du service et du modèle | 200 |
| POST | `/v1/predict` | prédiction pour une livraison | 200, 422, 503 |
| GET | `/docs` | documentation interactive (Swagger) | 200 |

- **422** : requête invalide (champ manquant, valeur hors bornes, véhicule inconnu).
- **503** : modèle non chargé ; lancer `python -m logiai.train` puis redémarrer l'API.

## Auteurs

- Aymen Ichqarrane
- Ihssane Moutchou

Groupe G3 — EMSI, 4e année IA & Data Science, 2026-2027.
