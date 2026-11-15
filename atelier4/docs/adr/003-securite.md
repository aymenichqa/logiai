# ADR 003 : sécurité de l'API LogiAI

## Décision 1 : où transmettre la clé (en-tête, URL ou corps) ?

- **Votre choix :** l'en-tête HTTP `X-API-Key`, une clé différente pour l'utilisateur et pour l'administrateur.
- **Ce que l'autre option ferait perdre :** dans l'URL, la clé est recopiée partout où l'URL l'est
  (journaux du serveur, historique du navigateur, proxys, lien partagé) ; elle apparaîtrait en clair
  dans `F12 > Network`. Dans le corps, le secret se mélangerait aux données métier, compliquerait la
  validation du schéma (`extra="forbid"`) et se retrouverait dans les journaux de requête. L'en-tête
  la garde séparée des données, facile à retirer d'un journal et à faire évoluer sans changer le contrat.

## Décision 2 : quelles origines autoriser (CORS) ? Une liste précise ou « * » ?

- **Votre choix :** une liste précise, `http://localhost:5500` et `http://127.0.0.1:5500`, lue au démarrage.
- **Ce que l'autre option ferait perdre :** avec `*`, n'importe quel site ouvert dans le navigateur
  pourrait appeler l'API et lire la réponse, y compris avec la clé saisie par l'utilisateur ; le
  navigateur ne jouerait plus son rôle de garde-fou. Une liste précise coûte un redémarrage de l'API
  quand on ajoute une origine (c'est ce qu'on observe en passant de 5500 à 5501), mais elle limite les
  pages autorisées à celles qu'on contrôle. La clé reste indispensable : CORS ne protège pas l'API,
  il protège l'utilisateur.
