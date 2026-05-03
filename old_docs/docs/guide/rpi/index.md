# Configuration des services

## Pré-requis

### PC (server) <-> Raspberry Pi (client) <Badge>V1 du projet</Badge>

Un ordinateur avec GNU radio d'installer, python, c++ redistribuable

Un rapsberry pi 3
Carte SD minimum 8Go de stockage  

:::warning
Si vous choisisser cette option, il vous suffit de configurer le client et suivre les indications ensuite pour le PC juste ici : [configuration PC comme client](/guide/client/installation)
:::

### Raspberry Pi (server) <-> Raspberry Pi (client) <Badge>V2 du projet (actuel)</Badge>

2 rapsberry pi 3
2 cartes SD minimum 8Go de stockage

## Choix du service à configuré

Cette section sert de guide dans la mise en place de des raspberry pi en tant que **Client** (recevoir et diffuser l''audio) et **Serveur** (traité et diffuser l'audio sur le réseau).

Choisissez l'une des options ci-dessous pour commencer.

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 2rem; ">
  <a href="./server/installation" class="card-link" style="text-decoration: none; color: inherit; border: 1px solid var(--vp-c-bg-soft); border-radius: 12px; padding: 24px; background-color: var(--vp-c-bg-soft); text-align: center; transition: all 0.25s ease; ">
    <h3 style="margin-top: 0;">Serveur (Raspberry Pi)</h3>
    <p style="font-size: 0.9rem; margin-bottom: 1.5rem;">Configurez le nœud central pour la capture et la diffusion des flux audio.</p>
    <VPButton href="./server/installation" text="Configurer le Serveur" theme="alt" />
  </a>

  <a href="./client/installation" class="card-link" style="text-decoration: none; color: inherit; border: 1px solid var(--vp-c-bg-soft); border-radius: 12px; padding: 24px; background-color: var(--vp-c-bg-soft); text-align: center; transition: all 0.25s ease; ">
    <h3 style="margin-top: 0;">Client (Raspberry Pi)</h3>
    <p style="font-size: 0.9rem; margin-bottom: 1.5rem;">Configurez les récepteurs pour le traitement et la sortie audio locale.</p>
    <VPButton href="./client/installation" text="Configurer le Client" theme="brand" />
  </a>

  <a href="../pc/server/" class="card-link" style="text-decoration: none; color: inherit; border: 1px solid var(--vp-c-bg-soft); border-radius: 12px; padding: 24px; background-color: var(--vp-c-bg-soft); text-align: center; transition: all 0.25s ease; ">
    <h3 style="margin-top: 0;">Client (Ordinateur)</h3>
    <p style="font-size: 0.9rem; margin-bottom: 1.5rem;">Configurez les récepteurs pour le traitement et la sortie audio locale.</p>
    <VPButton href="../pc/server/" text="Configurer le Client" theme="brand" />
  </a>

</div>

  <style>
.card-link:hover {
  border-color: var(--vp-c-brand) !important; 
}
</style>
