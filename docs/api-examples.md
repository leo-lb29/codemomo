---
outline: deep
---

! : Spécifie l'ordre des octets big-endian (format réseau standard). Cela garantit que les données sont sérialisées dans le format attendu pour la transmission réseau, indépendamment de l'architecture de la machine.

B : Représente un unsigned char (1 octet), capable de stocker des valeurs de 0 à 255. Généralement utilisé pour un type de message, un code d'opération, ou un identifiant.

I : Représente un unsigned int (4 octets), capable de stocker des valeurs de 0 à 4 294 967 295. Généralement utilisé pour la taille des données, un identifiant, ou une longueur de charge utile.