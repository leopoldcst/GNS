<h2 align="center">Projet 3TC G33 - GNS3</h2>

<div align="center">
  <img src="./assets/GNS3_logo.png" alt="GNS3 Logo" width="100px" />
</div>

<p>
  Le projet GNS3 vise à simuler le routage entre plusieurs AS et leurs relations (client, fournisseur, peer).
Il utilise des protocoles de routage internes (RIP, OSPF) et inter-domaines (BGP) pour assurer la connection entre les réseaux.
Le projet utilise des fichiers d'intentions pour construire le réseau.
Les politiques BGP et l’optimisation OSPF sont intégrées afin de reproduire des scénarios réalistes de routage inter-AS. 
</p>

# Installation

Le code est entièrement écrit en Python et sera donc exécuté dans un environnement correspondant.
Il est impératif d’avoir Python installé sur sa machine pour pouvoir l’exécuter.

1. Créer un dossier projet 

```bash
mkdir GNS_Project
cd GNS_Project
```

2. Cloner le repo Github
```bash
git clone https://github.com/leopoldcst/GNS.git
```

# Execution

En l’absence de paramètre, le script exécute automatiquement l’intention définie par défaut dans le main.

```bash
python main.py <intent_file>

# Exemple
python main.py intents/intent_2_AS_OSPF_RIP.json

```

