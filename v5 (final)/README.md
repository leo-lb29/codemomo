# Application pour système de conférence

## Table des matières

- [Application pour système de conférence](#application-pour-système-de-conférence)
  - [Table des matières](#table-des-matières)
  - [Arborescence du projet](#arborescence-du-projet)
  - [Installation](#installation)
    - [Minimum requis](#minimum-requis)
    - [Créer un environnement python](#créer-un-environnement-python)
    - [Lancer l'environnement virtuel](#lancer-lenvironnement-virtuel)
    - [Installer les dépendances](#installer-les-dépendances)
    - [Lancer l'host](#lancer-lhost)
    - [Lancer le client](#lancer-le-client)
  - [Configurations](#configurations)
  - [Licence](#licence)

## Arborescence du projet

```bash
├── app
│   ├── functions 
│   │   ├── client 
│   │   │   └── main.py
│   │   └── server
│   │       └── main.py
│   ├── main 
│   │   ├── client
│   │   │   └── main.py
│   │   └── server
│   │       └── main.py
│   └── utils
│       └── log.py
├── README.md
├── client.py 
├── config.py
├── host.py
└── requirement.txt
```

## Installation

### Minimum requis

* OS : Linux, Windows
* Une connexion internet entre les clients et l'host (Ethernet, WIFI...)
* Python
* Entrer et sortie audio
* Clavier

### Créer un environnement python

Linux :

```bash
python3 -m venv .venv
```

Windows : 

```bash
python -m venv .venv
```

### Lancer l'environnement virtuel

Linux :

```bash
source .venv/bin/activate
```

Windows : 

```bash
.venv\Scripts\activate
```

### Installer les dépendances

```bash
pip install -r requirement.txt
```

### Lancer l'host

```bash
python host.py
```

### Lancer le client

```bash
python client.py <@IP du serveur>
```

## Configurations

Pour modifier les configurations global, elle ce trouve dans config.py

## Licence

```
(c) Université Bretagne Sud - Léo Le Bigot

Exploitable exclusivement dans le cadre de l'éducation à l'Université Bretagne Sud.
```
