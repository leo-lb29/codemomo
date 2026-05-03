---
title: Configuration Serveur
editLink: true
outline: [2, 3]
lastUpdated: true
prev:
  text: 'Accueil'
  link: '/'
next:
  text: 'Configuration Client'
  link: '/guide/client/installation'
---

# Installation du Système
Le guide suivant permet de mettre en place les Raspberry pi pour le projet.
## 1. Préparation de l'OS
On commence par préparer l'OS
### Chargement de l'OS sur la cardSD:

Pour chacun des Raspberry pi il faudra charger un Raspbian nous allons ici utilisé (Trixy qui est la version LTS : x.x.x de Raspbian dans sa version Lite "NO-DESKTOP" pour alléger les processus)

#### TUTORIEL

:::danger
TODO: Rajouter le tuto installation avec RPI-Imager et tt comme pour le prj réseau du sem 1
:::

### Préparation des environnements

#### Installation des dépendances

> - GNU Radio

:::code-group
```bash [SERVER]
sudo apt update 
sudo apt-get install gnuradio
```

```bash [CLIENT]
sudo apt update 
sudo apt-get install gnuradio
```
:::

## 2. Configuration Réseau (Statique)

Dans le cas où il n'y a pas de routeur il faut configurer pour le serveur une ip statique pour que ce soit stable, ici on va utiliser le NetworkManager pour relier une ip static à l'interface `eth0` (ethernet).

```bash
# Configuration de l'interface "Wired connection 1" qui est "eth0"
sudo nmcli con mod "Wired connection 1" \ 
  ipv4.addresses 192.168.10.254/24 \ 
  ipv4.method manual
# On applique la configuration
sudo nmcli con up "Wired connection 1"
```

:::danger
Vous devez remplacer `X` par un numéro strictement différent des autres raspberry pi et différent de 0, 254 et 255 qui sont des resolver réservé au réseau, hub et passerrelle.
:::

:::danger
Dans le cas où vous utilisé une carte son: IQAudio Zero Codec, vous devez suivre les informations via ce lien: [IQAudio Installation](/guide/module/carte-son/installation)
:::

## 3. Installation du service client

Placer à la racine le fichier server.py et les fichiers lié au server

### Lancement automatique au démarrage avec pm2 <Badge type="tip" text="production" />

#### 1. Installation

On commence par installer pm2

```bash
pm2 start server.py --interpreter python3
```

#### 2. Consulté le status avec

```bash
pm2 status
```

#### 3. Lancement au démmarrage du client

```bash
pm2 startup
```

### Lancement manuel <Badge type="tip" text="debug" />

Executer le fichier `server.py` avec

```bash
python3 server.py
```
