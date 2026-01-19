# Intent

## gnsAutoConfig

| Nom propriété | Type | Description | Valeur par défaut |
| - | - | - | - |
| enable | boolean | Connexion au serveur GNS | false |
| port | string | Port du serveur GNS | "4000" |
| project_name | string | Nom du projet dans GNS | **Requis** |
| create_routers | boolean | Création automatique des routeurs dans le projet | false |
| create_links | boolean | Création automatique des liens entre routeurs | false |
| arrange_in_circle | boolean | Placer tous les routeurs en cercle | false |
| auto_fetch_router_ip | boolean | Récupère automatiquement l'ip et le port de chaque routeur. Si désactivé, il faut préciser ces informations dans la config de chaque routeur | true |