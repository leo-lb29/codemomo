---
title: Module IQAudio
editLink: true
outline:
  + 2
  + 3
lastUpdated: true
prev:
  text: Configuration Client
  link: /guide/client/installation
next:
  text: Monitoring
  link: /guide/monitoring
---

# Préparation de IQAudio Zero Codec

:::danger
TODO: Rajouter c quoi IQAudio
:::

IQAudio est une carte son destiné à être installer sur les ports GPIO de la carte raspberry pi elle permet de gérer le son avec une haute définition

## Installation sur le CLIENT

Avant de branché la carte son sur les GPIOS il faut activé dans le boot I2S + I2C qui va permettre la communication audio avec la carte

### Ouvrir le fichier 

`/boot/firmware/config.txt`

```bash
sudo nano /boot/firmware/config.txt
```

Décommenter les lignes suivantes  
TODO: A corriger en vérfiiant les bon params dans le fichier boot

```js
# dtparam = i2c_arm = on //[!code --]
dtparam = i2c_arm = on // [!code ++]

dtoverlay = iqaudio - codec // [!code ++]
```

### Eteigner la rasperry pi

```bash
sudo shutdown now
```

### Branché la carte son sur les GPIOS

Le branchement de la carte ce fait sur les port GPIO (la bande de 40broches)

Vers l'interieur de la carte

Une fois fait remetter la carte sous tension

### Modification sortie audio

```bash
sudo raspi-config
```

:::danger RAJOUTER
TODO: Rajouter les images pour set la carte son comme sortie audio et non la prise jack de base de la rpi client)
:::

# Rapport d'installation - IQAudio Codec Zero sur Raspberry Pi 3

## Configuration actuelle

* **Matériel** : Raspberry Pi 3 + IQAudio Codec Zero
* **OS** : Raspbian Trixie (sans interface graphique)
* **Sortie audio** : Haut-parleur mono sur connecteur screw terminal
* **Problème** : Erreur I/O lors de la lecture avec `aplay`

---

## Procédure d'installation complète

### Vérification de la configuration système

```bash
# Vérifier que le codec est détecté
aplay -l

# Vérifier la configuration device tree
cat /boot/firmware/config.txt | grep iqaudio
```

**Configuration attendue dans `/boot/firmware/config.txt` ** :

```
dtoverlay=iqaudio-codec
#dtparam=audio=on   # <- Cette ligne DOIT être commentée
```

Si nécessaire, éditez le fichier :

```bash
sudo nano /boot/firmware/config.txt

#dtparam=audio=off
dtoverlay=iqaudio-codec
```

### 2Installation des outils ALSA

```bash
sudo apt update
sudo apt install -y alsa-utils
```

### Configuration du Codec pour sortie mono speaker

IQAudio fournit des scripts préconfigurés. Téléchargez-les :

```bash
cd ~
git clone https://github.com/iqaudio/Pi-Codec.git
cd Pi-Codec
```

**Pour votre cas d'usage** (lecture mono sur speaker), utilisez :

```bash
# Charger la configuration "Mono speaker playback"
sudo alsactl restore -f Codec_Zero_OnboardMIC_record_and_SPK_playback.state
```

### Vérification avec alsamixer

```bash
alsamixer
```

**Paramètres critiques à vérifier** :
* **Mixer Out FilterL/R** : > 0 (typiquement 50-80%)
* **Out FilterL/R** : > 0 (typiquement 60-90%)
* **Mixout Left/Right** : activé
* **SPK** (speaker) : > 0 (typiquement 70-100%)

Naviguez avec les flèches et ajustez avec ↑/↓. Appuyez sur `M` pour unmute si nécessaire.

### Test de lecture

```bash
# Test avec un fichier audio mono si possible
speaker-test -t wav -c 1

# Ou avec votre fichier (forcé en mono)
aplay -Dplughw:0,0 tetris99.wav
```

### Sauvegarde de la configuration

Une fois que ça fonctionne :

```bash
sudo alsactl store
```

### Configuration automatique au démarrage

Créez un script de démarrage :

```bash
sudo nano /etc/rc.local
```

Ajoutez **avant** la ligne `exit 0` :

```bash
# Restaurer la configuration Codec Zero
alsactl restore -f /home/bob/Pi-Codec/Codec_Zero_OnboardMIC_record_and_SPK_playback.state
```

Rendez-le exécutable :

```bash
sudo chmod +x /etc/rc.local
```

---

## Diagnostic si ça ne fonctionne toujours pas

```bash
# 1. Vérifier les périphériques audio
cat /proc/asound/cards

# 2. Vérifier les contrôles disponibles
amixer -c 0 controls

# 3. Voir l'état actuel des mixers
amixer -c 0 contents

# 4. Tester avec des paramètres explicites
aplay -D hw:0,0 -f S16_LE -r 44100 -c 2 tetris99.wav
```

---

## Checklist finale

* [ ] `dtoverlay=iqaudio-codec` présent dans `/boot/firmware/config.txt`
* [ ] Audio onboard Raspberry Pi désactivé (`#dtparam=audio=on`)
* [ ] Scripts Pi-Codec téléchargés
* [ ] Configuration ALSA chargée avec `alsactl restore`
* [ ] Volumes vérifiés dans `alsamixer` (SPK > 0, Out Filter > 0)
* [ ] Configuration sauvegardée avec `alsactl store`
* [ ] Script de démarrage créé dans `/etc/rc.local`
* [ ] Redémarrage effectué

---

## Notes importantes

1. **Le Codec Zero ne peut pas lire directement du stéréo sur sortie mono** sans configuration. Le mixer doit combiner L+R.

2. **Les niveaux de sortie** : La sortie speaker mono délivre 1.2W @ 8Ω. Attention à ne pas saturer.

3. **Fichier stéréo** : Pour un fichier stéréo comme `tetris99.wav`, utilisez plutôt :

```bash
   aplay -Dplug:dmix tetris99.wav
```

4. **GPIO utilisés** : GPIO18/19/20/21 (I2S), GPIO23/24 (LED), GPIO27 (bouton) - ne pas utiliser pour autre chose.

---

**Prochaine étape** : Démarrez par l'étape 1 et confirmez-moi la sortie de `aplay -l` et le contenu de votre `/boot/firmware/config.txt` .

### RPI 1

sudo nmcli con mod "Wired connection 1" \
  ipv4.addresses 192.168.10.1/24 \
  ipv4.method manual

sudo nmcli con up "Wired connection 1"

### PI 2

sudo nmcli con mod "Wired connection 1" \
  ipv4.addresses 192.168.10.2/24 \
  ipv4.method manual

sudo nmcli con up "Wired connection 1"
