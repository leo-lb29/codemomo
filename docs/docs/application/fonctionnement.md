# Fonctionnement

## La librairie Socket

la librairie socket nous python permet un accès à l'interface réseau bas niveau de façon plus simplifié, elle est très complète et ici très intéressante car on vas pouvoirs créer nos propre paquet pour l'application pour la communication client <-> host

il existe plusieurs famille de socket

AF_BLUETOOTH : communication péréripque bluetooth

AF_HYPERV : communication avec les hôte windows

et plein d'autres dont celui que nous utilisons, la famille INET car on veut communiqué avec l'interface réseau avec une IP

il existe INET et INET6 nous somme sur un format d'ip V4 ici donc nous allons utilsié INET

une fois la camille AF défini il nous faut le type de socket, il existe plusieurs type

STREAM
DGRAM
RW
RDM
SEQPACKET

## contrôle

on vient créer un objet :

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
print(sock)

>>> <socket.socket fd=3, family=2, type=1, proto=6, laddr=('0.0.0.0', 0)>
```

on vas pouvoir définir des options avec la méthode

sock.setsockopt de type SO_ qui va nous permettre de définir un buffer
## signal

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
print(sock)

>>> <socket.socket fd=3, family=2, type=2, proto=17, laddr=('0.0.0.0', 0)>
```
