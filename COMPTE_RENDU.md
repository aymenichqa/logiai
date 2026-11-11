# Compte rendu : TP API LogiAI

**Noms :** TODO  **Groupe :** TODO

## 1. Environnement et premiers tests

Sortie de `python -m pytest` au départ, après `python -m logiai.train`, avant d'écrire `schemas.py` et `predict()` :

```
FAILED tests/test_api.py::test_predict_valide_renvoie_200 - assert 422 == 200
FAILED tests/test_api.py::test_predict_forme_de_la_reponse - AssertionError: ...
FAILED tests/test_api.py::test_predict_probabilite_entre_0_et_1 - KeyError: '...'
FAILED tests/test_api.py::test_predict_trajet_risque_plus_eleve_que_trajet_facile
FAILED tests/test_api.py::test_modele_absent_renvoie_503 - assert 422 == 503
=================== 5 failed, 8 passed, 1 warning in 4.76s ====================
```

Après avoir complété le schéma seul, les 5 mêmes tests échouent encore, mais avec `NotImplementedError` au lieu de 422 : la requête valide traverse maintenant la validation et arrive jusqu'à `predict()`. Après avoir écrit `predict()`, on obtient `13 passed`, puis `15 passed` avec les deux tests personnels.

Métriques obtenues avec `python -m logiai.train` (jeu de 5000 lignes, 27,4 % de retards) :

- Baseline « toujours à l'heure » : **0,726** (72,6 % d'accuracy en répondant toujours « à l'heure », soit la proportion de livraisons à l'heure dans le jeu de test).
- Modèle : **0,774** d'accuracy, **0,617** de précision, **0,769** d'AUC.
- Rappel : **0,464** — sur 100 livraisons réellement en retard, le modèle en détecte environ 46.

Pourquoi certains tests qui attendent un 422 passent-ils déjà ? Le schéma de départ ne déclare que `distance_km`, avec `extra="forbid"`. Toutes les requêtes de test contiennent les autres champs (`poids_kg`, `pluie_mm`, `type_vehicule`, etc.), qui sont donc des champs inconnus : Pydantic répond 422 pour tous, même pour une livraison correcte. Ces tests sont verts **pour la mauvaise raison**. Le test qui démasque ce faux vert est le test de succès `test_predict_valide_renvoie_200` : il attend un 200 et reçoit 422, ce qui prouve que le schéma refuse une requête pourtant valide. Un test vert ne suffit pas : il faut savoir pourquoi il passe.

À quoi sert l'API si le rappel est faible ? Qu'est-ce qu'un dispatcher y gagne quand même ?

TODO (réponse personnelle)

## 2. Mon schéma

| Variable | Min | Max | Pourquoi |
|---|---|---|---|
| distance_km | 1 | 1000 | Donné dans le starter. En dessous de 1 km, ce n'est pas une livraison planifiée ; au-delà de 1000 km, on sort du transport routier régional (le jeu de données s'arrête à 800 km). |
| poids_kg | 0,1 | 5000 | Un colis a un poids strictement positif (100 g minimum). 5000 kg couvre largement un camion chargé (3000 kg maximum dans les données), avec une marge pour un véhicule réel. |
| heure_depart | 0 | 23 | Une heure de la journée est un entier de 0 à 23. 24 est refusé. |
| pluie_mm | 0 | 100 | Pas de pluie négative. 100 mm est déjà un cumul d'orage exceptionnel ; 500 mm est physiquement irréaliste et refusé. |
| trafic_index | 0 | 10 | Échelle du contrat : 0 = fluide, 10 = saturé. |
| nb_arrets | 0 | 30 | Nombre d'arrêts entier, positif ou nul. 30 reste très au-dessus des 12 arrêts maximum observés, sans accepter de valeurs absurdes. |
| type_vehicule | — | — | `Literal["moto", "fourgon", "camion"]` : seules les trois valeurs connues du modèle. |

`model_config = ConfigDict(extra="forbid")` est conservé : un champ inconnu est refusé en 422. Les bornes du schéma restent compatibles avec les sliders Streamlit (distance 1–800, poids 1–3000, pluie 0–60, trafic 0–10, arrêts 0–12).

## 3. Ma fonction predict()

```python
@app.post("/v1/predict", response_model=PredictionOut)
def predict(livraison: Livraison):
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez `python -m logiai.train` puis redémarrez l'API.",
        )
    return PredictionOut(**predictor.predict(livraison.model_dump()))
```

## 4. Quatre requêtes

Réalisées avec `curl.exe` sur l'API lancée par `python -m uvicorn logiai.api.main:app --port 8000`.

| Requête | Code obtenu | Pourquoi |
|---|---|---|
| livraison normale | **200** — `{"probabilite_retard":0.732,"alerte":true,"seuil":0.4,"model_version":"1.0"}` | Les 7 valeurs respectent le schéma et le modèle est chargé. 0,732 ≥ 0,4, donc `alerte` vaut `true`. |
| distance_km = -5 | **422** — `Input should be greater than or equal to 1` sur `body.distance_km` | Pydantic refuse la valeur avant l'exécution de `predict()` (borne `ge=1`). |
| type_vehicule = "avion" | **422** — `Input should be 'moto', 'fourgon' or 'camion'` sur `body.type_vehicule` | Valeur hors du `Literal` autorisé. |
| modèle absent | **503** — `{"detail":"Modèle non chargé : lancez python -m logiai.train puis redémarrez l'API."}` ; `/health` répond **200** avec `{"status":"ok","model_loaded":false}` | Le dossier `models/` a été supprimé puis le serveur relancé. La requête est valide, mais `state` ne contient pas de predictor. Après `python -m logiai.train` et redémarrage, `/health` repasse à `model_loaded:true` et la prédiction répond 200. |

## 5. Questions de compréhension

1. **Pourquoi charge-t-on le modèle au démarrage et pas à chaque requête ?** Charger `model.joblib` lit le disque et désérialise tout l'objet (pipeline scikit-learn). Le faire à chaque requête ajouterait ce coût à chaque appel et multiplierait les accès disque, alors que le modèle est identique pour toutes les requêtes. Le charger une fois dans `lifespan` le garde en mémoire, partagé par toutes les requêtes : les réponses sont rapides. Cela permet aussi à `/health` de dire si le modèle est disponible dès le démarrage.
2. **Qui écrit le contrôle « pluie <= 100 », et où ?** C'est nous, dans le schéma Pydantic (`logiai/api/schemas.py`), avec `Field(ge=0, le=100)`. FastAPI l'applique automatiquement avant d'appeler `predict()` : la logique métier n'a pas à le refaire, et le contrôle apparaît aussi dans `/docs`.
3. **Différence entre 422 et 503 ?** 422 : la requête est invalide (erreur du client), par exemple une pluie de 500 mm ou une heure de 24 ; renvoyer la même requête ne changera rien. 503 : la requête est correcte mais le service n'est pas en état de la traiter (modèle non chargé) ; c'est une indisponibilité côté serveur, qui peut disparaître après entraînement et redémarrage.
4. **Pourquoi `/v1/predict` plutôt que `/predict` ?** Pour versionner le contrat. Si les champs ou la réponse changent, on publie `/v2/predict` et les clients existants continuent d'utiliser `/v1` sans être cassés.
5. **Que se passerait-il si la distance était déclarée `int` ?** Une distance décimale comme `12.5` serait refusée en 422 (partie fractionnaire interdite), alors qu'elle est réaliste : les distances du jeu de données ont une décimale. Seules les valeurs entières (ou comme `120.0`, acceptée par Pydantic) passeraient.

### Rappel du faux vert (bloc 6.2)

Au départ, les tests qui attendent un 422 étaient verts alors que le schéma était presque vide : avec `extra="forbid"`, les champs non déclarés (`poids_kg`, `pluie_mm`, `type_vehicule`, etc.) étaient tous considérés comme inconnus, donc toute requête était refusée. Le contrôle portait sur la mauvaise cause. Le test de succès `test_predict_valide_renvoie_200` démasque ce faux vert : il attend 200 et reçoit 422. Cela montre qu'un résultat de test se lit avec sa raison, pas seulement avec sa couleur.

Pour vérifier que le test `test_heure_24_refusee` est utile, la borne a été cassée temporairement (`heure_depart` avec `le=24`) : le test est devenu rouge (`assert 200 == 422`), puis la borne `le=23` a été restaurée et les 15 tests sont repassés au vert.

## 6. Décision : modèle absent

**Option A — démarrer quand même et répondre 503 (choix actuel).**
Ce qu'on gagne : l'API reste observable (documentation `/docs`, `/health` indique `model_loaded: false`), on peut diagnostiquer un déploiement partiel, et les autres routes continuent de répondre. Ce qu'on perd : le service a l'air vivant alors qu'il ne peut pas prédire ; si personne ne surveille `/health`, l'erreur n'apparaît qu'à la première requête réelle.

**Option B — refuser de démarrer.**
Ce qu'on gagne : le problème est visible immédiatement au déploiement (échec rapide), et aucun client n'est jamais servi par une API sans modèle. Ce qu'on perd : tout le service tombe, y compris `/health` et `/docs`, ce qui complique le diagnostic ; dans un orchestrateur, cela peut provoquer des redémarrages en boucle.

Recommandation : **option A** pour ce TP, car elle garde `/health` utile et permet de constater puis corriger le problème sans arrêter le service. En production, on peut combiner les deux : refuser de démarrer si le modèle est absent, tout en gardant une sonde de santé distincte.

Décision finale : TODO (à trancher par toi)

## 7. Lien de la pull request

TODO (lien de la PR à ouvrir par toi, après relecture par ton binôme)
