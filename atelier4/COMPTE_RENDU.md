# Compte rendu : tester, sécuriser et appeler l'API LogiAI

**Noms :** Aymen Ichqarrane, Ihssane Moutchou  **Groupe :** G3

## 1. Casser son API (activité 1)

On a d'abord écrit ce qu'on attendait pour chaque requête, puis on les a envoyées une par une.

| Cas | Requête (corps ou URL) | Prévu | Obtenu |
|---|---|---|---|
| champ manquant | POST `/v1/predict` sans `poids_kg` | 422 | **422**, `Field required` sur `body.poids_kg` |
| valeur absurde | POST `/v1/predict`, `poids_kg = 99999` | 422 | **422**, `less_than_equal`, maximum 3500 |
| texte au lieu d'un nombre | POST `/v1/predict`, `distance_km = "loin"` | 422 | **422**, `float_parsing` |
| champ en trop | POST `/v1/predict`, `couleur = "rouge"` | 422 | **422**, `extra_forbidden` |
| mauvaise route | POST `/v1/predire` | 404 | **404**, `Not Found` |

Nos cinq prévisions étaient justes, donc aucune de ces requêtes n'a été acceptée alors qu'elle devait
être refusée. Mais ça ne veut pas dire que l'API était solide : les deux bugs de l'activité 2 passaient
justement parce qu'aucune de ces cinq requêtes ne regardait les bornes des champs. Cinq cas ne suffisent
pas à couvrir un contrat.

## 2. Les 2 bugs (activité 2)

On a testé chaque champ juste à l'intérieur et juste à l'extérieur de ses bornes, puis une heure
décimale (11,5). Deux tests sont ressortis rouges, et c'était les deux bugs cherchés.

| Bug | Test qui l'a révélé | Comportement avant | Correction |
|---|---|---|---|
| 1 | `test_valeurs_limites[heure_depart-24-422]` | une heure de 24 était acceptée (200) alors que la description dit « 0 à 23 » : la borne était `le=24` | `le=23` |
| 2 | `test_valeurs_limites[nb_arrets--1-422]` | un nombre d'arrêts de -1 était accepté (200) : il manquait la borne basse (`Field(le=15)` seulement) | ajout de `ge=0`, `le=15` conservé |

Avant correction, `python -m pytest tests/test_limites.py tests/test_casser.py` affichait
`2 failed, 30 passed`, avec exactement `heure_depart=24 : attendu 422, obtenu 200` et
`nb_arrets=-1 : attendu 422, obtenu 200`. Après correction des deux bornes, les mêmes fichiers
donnent `32 passed`. C'est la leçon de l'activité : un test qui passe ne dit pas pourquoi il passe, et
seuls les tests aux bornes ont vu ces deux valeurs impossibles.

## 3. La clé API (sprint 1)

La clé arrive dans l'en-tête `X-API-Key`. On regarde d'abord si c'est la clé admin, puis la clé
utilisateur ; sinon on renvoie 401. Si la clé est bonne mais que la route demande un administrateur,
c'est 403.

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

Pour `.env` : `git status --short -uall` ne montre aucune ligne `.env`, et `.gitignore` contient bien
`.env`. Le fichier existe sur la machine mais Git ne le voit pas.

## 4. Le client web (sprint 2)

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

Ce que la page affiche avec les valeurs par défaut :

- **livraison normale** : « Probabilité de retard : 73.2 %. Alerte : livraison à risque. » (le seuil
  est de 0,4 et le modèle renvoie 0,732) ;
- **pluie de 500 mm** : « Requête invalide — pluie_mm : Input should be less than or equal to 100 » ;
- **fausse clé** : « Clé API absente ou invalide. » (le 401 est traduit par `messageErreur`).

**Expérience CORS sur le port 5501.** La page s'ouvre, mais au moment de l'envoi elle affiche le
message d'erreur prévu pour une API injoignable, et la console (F12) parle de politique CORS : la
réponse ne contient pas d'en-tête `Access-Control-Allow-Origin` pour `http://localhost:5501`. Le
navigateur bloque donc la lecture de la réponse. `curl` continue de fonctionner parce que CORS est une
règle du navigateur : `curl` n'est pas un navigateur et ignore ces en-têtes. L'API, elle, reste
protégée par la clé.

**La clé dans F12.** Pendant un appel réussi : F12 → onglet Network → la requête `predict` → en-têtes
de la requête. La clé apparaît en clair dans `X-API-Key`. Si elle était écrite dans le JavaScript de la
page, n'importe qui pourrait l'y lire ; c'est pour ça qu'on la saisit à chaque visite et qu'elle
n'existe que dans le `.env` du serveur.

## 5. Questions de compréhension

1. **401, 403 et 422.** 401 : je ne sais pas qui vous êtes (clé absente ou fausse). 403 : je sais qui
   vous êtes, mais vous n'avez pas le droit (clé utilisateur sur `/v1/model-info`). 422 : vous êtes
   authentifié et autorisé, mais les données sont invalides (pluie de 500 mm, heure de 24). L'ordre des
   contrôles est route, clé, droits, données, modèle : le premier qui échoue donne la réponse.
2. **La clé ni dans le code ni dans Git.** Une clé écrite dans le code part sur GitHub, et même si on
   la supprime ensuite, elle reste dans l'historique. `.env` reste sur la machine, est lu au démarrage
   et Git l'ignore. `.env.example` montre seulement les noms des variables, avec de fausses valeurs.
3. **`compare_digest` plutôt que `==`.** `==` s'arrête au premier caractère différent : la durée de la
   réponse indique combien de caractères étaient justes, ce qui permet de deviner la clé petit à petit.
   `compare_digest` compare en temps constant.
4. **`curl` passe alors que la page du 5501 est bloquée.** Le navigateur applique CORS et refuse de
   lire la réponse d'une origine non autorisée ; `curl` ne l'applique pas. CORS protège l'utilisateur,
   pas l'API : sans clé, `curl` reçoit 401.
5. **La validation du navigateur ne remplace pas celle de l'API.** Les attributs HTML (`required`,
   `type=number`) sont du confort et se contournent avec `curl` ou F12. Seule la validation du serveur
   (Pydantic, `extra="forbid"`, `Literal`) protège les données et le modèle.

## 6. Lien de la pull request

PR à ouvrir : https://github.com/aymenichqa/logiai/pull/new/tp-securite

## 7. Ticket de sortie

- **401 vs 422** : le 401 parle de la clé, le 422 parle des données. La clé est vérifiée avant le
  schéma, donc une pluie de 500 mm sans clé donne 401, pas 422.
- **La clé hors du code et hors de Git** : elle est dans `.env`, lu au démarrage, ignoré par Git ; le
  code ne contient qu'un nom de variable, et l'historique Git ne garde aucun secret.
- **`curl` face au port 5501** : `curl` n'est pas un navigateur, CORS ne s'applique pas ; la page est
  bloquée parce que l'origine 5501 n'est pas dans `ALLOWED_ORIGINS`.
- **Ce qui reste flou** : le détail du preflight `OPTIONS` (pourquoi le navigateur envoie une requête
  avant la vraie) ; à revoir dans la doc MDN sur CORS.
