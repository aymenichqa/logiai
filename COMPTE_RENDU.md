# Compte rendu : TP API LogiAI

**Noms :** ............................  **Groupe :** ........

## 1. Environnement et premiers tests
- Sortie de `python -m pytest` au départ (après `python -m logiai.train`, avant d'écrire le schéma et `predict()`) :

(à coller)

- Accuracy baseline / modèle, rappel du modèle :
- Pourquoi certains tests qui attendent un 422 passent-ils déjà ?

## 2. Mon schéma
| Variable | Min | Max | Pourquoi |
|---|---|---|---|

## 3. Ma fonction predict()
(à coller)

## 4. Quatre requêtes
| Requête | Code obtenu | Pourquoi |
|---|---|---|
| livraison normale | | |
| distance_km = -5 | | |
| type_vehicule = "avion" | | |
| modèle absent | | |

## 5. Questions de compréhension
1. Pourquoi charge-t-on le modèle au démarrage et pas à chaque requête ?
2. Qui écrit le contrôle « pluie <= 100 », et où ?
3. Différence entre 422 et 503 ?
4. Pourquoi `/v1/predict` plutôt que `/predict` ?
5. Que se passerait-il si la distance était déclarée `int` ?

## 6. Décision : modèle absent (A : 503 / B : refuser de démarrer)

## 7. Lien de la pull request
