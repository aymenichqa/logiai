# Compte rendu : tester, sécuriser et appeler l'API LogiAI

**Noms :** Aymen Ichqarrane, Ihssane Moutchou  **Groupe :** G3

## 1. Casser son API (activité 1)
| Cas | Requête (corps ou URL) | Prévu | Obtenu |
|---|---|---|---|
| champ manquant | POST `/v1/predict`, corps `VALID` sans `poids_kg` | 422 | **422** (`Field required` sur `body.poids_kg`) |
| valeur absurde | POST `/v1/predict`, `poids_kg = 99999` | 422 | **422** (`less_than_equal`, maximum 3500) |
| texte au lieu d'un nombre | POST `/v1/predict`, `distance_km = "loin"` | 422 | **422** (`float_parsing`) |
| champ en trop | POST `/v1/predict`, `couleur = "rouge"` | 422 | **422** (`extra_forbidden`) |
| mauvaise route | POST `/v1/predire` | 404 | **404** (`Not Found`) |

- Une requête acceptée alors qu'elle devait être refusée ? Laquelle ?
  Sur ces cinq cas, non : les cinq codes prévus ont été obtenus. En revanche l'activité 2 montre que le
  schéma acceptait deux valeurs impossibles qui ne figuraient pas dans ces cinq requêtes (une heure de
  24 et des arrêts négatifs) : cinq cas ne suffisent pas à couvrir un contrat.

## 2. Les 2 bugs (activité 2)
| Bug | Test qui l'a révélé | Comportement avant | Correction |
|---|---|---|---|
| 1 | `test_valeurs_limites[heure_depart-24-422]` | `heure_depart = 24` accepté (200) alors que la description dit « 0 à 23 » : la borne était `le=24` | `le=23` |
| 2 | `test_valeurs_limites[nb_arrets--1-422]` | `nb_arrets = -1` accepté (200) : la borne basse manquait (`Field(le=15)` seulement) | ajout de `ge=0`, `le=15` conservé |

- Sortie de `python -m pytest` à la fin de l'activité 2 :
  Avant correction, `python -m pytest tests/test_limites.py tests/test_casser.py` donnait
  `2 failed, 30 passed` avec exactement `heure_depart=24 : attendu 422, obtenu 200` et
  `nb_arrets=-1 : attendu 422, obtenu 200`. Après correction des deux bornes, les mêmes fichiers
  donnent `32 passed`.

## 3. La clé API (sprint 1)
- Ma fonction `verify_api_key()` (collez le code) :

```python
def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Authentification : renvoie le rôle ('user' ou 'admin') ou lève une 401."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Clé API absente : en-tête X-API-Key requis.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # l'admin d'abord : les deux clés sont distinctes, mais l'ordre rend le rôle explicite
    if _egal(x_api_key, config.ADMIN_KEY):
        return "admin"
    if _egal(x_api_key, config.API_KEY):
        return "user"
    raise HTTPException(
        status_code=401,
        detail="Clé API invalide.",
        headers={"WWW-Authenticate": "ApiKey"},
    )
```

| Requête | Code obtenu |
|---|---|
| `/v1/predict` sans clé | **401** |
| `/v1/predict` fausse clé | **401** |
| `/v1/predict` clé utilisateur | **200** `{"probabilite_retard":0.732,"alerte":true,"seuil":0.4,"model_version":"1.0"}` |
| `/v1/model-info` clé utilisateur | **403** `{"detail":"Accès réservé à l'administrateur."}` |
| `/v1/model-info` clé administrateur | **200** `{"version":"1.0","seuil":0.4,"variables":[...]}` |
| `/health` sans clé | **200** `{"status":"ok","model_loaded":true,"auth_configured":true}` |

- Preuve que `.env` n'est pas dans Git (sortie de `git status`) :
  `git status --short -uall` liste les fichiers du starter et ne contient **aucune** ligne `.env` ;
  `.gitignore` contient la ligne `.env`.

## 4. Le client web (sprint 2)
- Mon `fetch` (collez le code) :

```javascript
async function appelerApi(livraison, cle) {
  const reponse = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": cle,
    },
    body: JSON.stringify(livraison), // l'objet devient du texte JSON
  });
  const corps = await reponse.json(); // la réponse, en objet
  return { status: reponse.status, corps };
}
```

- Ce qui s'affiche : livraison normale / pluie de 500 mm / fausse clé :
  TODO (à compléter dans le navigateur, port 5500)
- Expérience CORS (page servie sur le port 5501) : que disent la page et la console (F12) ? Pourquoi `curl` marche-t-il quand même ?
  TODO (à compléter après l'expérience sur 5501)
- Où voyez-vous la clé dans F12 ?
  TODO (F12 > Network > predict > en-têtes de la requête)

## 5. Questions de compréhension
1. Quelle différence entre 401, 403 et 422 ?
   TODO
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ?
   TODO
3. Pourquoi comparer avec `compare_digest` plutôt qu'avec `==` ?
   TODO
4. Pourquoi `curl` fonctionne-t-il alors que la page du port 5501 est bloquée ?
   TODO
5. Pourquoi la validation faite par le navigateur ne remplace-t-elle pas celle de l'API ?
   TODO

## 6. Lien de la pull request

TODO (lien de la PR, après relecture par le binôme)

## 7. Ticket de sortie (à remplir sur papier)

- 401 vs 422 : TODO
- La clé hors du code et hors de Git : TODO
- `curl` face au port 5501 : TODO
- Ce qui reste flou : TODO
