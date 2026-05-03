Un protocole est un moyen d'envoyé une information structuré à travers un medium
ici c'est un signal audio donc le programme va découper le signal en échantillons et l'encapsulé dans un protocole et l'ordinateur cible va pouvoir le remettre dans l'ordre en suivant les infos reçus.

L'étude ici à été de rechercher le protocole le plus adapté à notre projet, pour ce faire nous avons rechercher sur internet les protocoles lier à la diffusion de signaux en temps réel et nous avons retenue la liste suivante :

* TCP  
* UDP  
* RTP  
* RTSP  
* ICECAST  

Il existe d'autres protocoles mais nous les traiterons pas ici, la selection sont les plus connues pour ce type de projet

<style>
.protocol-buttons {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.protocol-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #444 0%, #333 100%);
  border: 1px solid #555;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
  cursor: pointer;
}

.protocol-button:hover {
  background: linear-gradient(135deg, #555 0%, #444 100%);
}

.protocol-button h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}
</style>

<div class="protocol-buttons">

<a href="./tcp" class="protocol-button">
  <h3>TCP</h3>
</a>

<a href="./udp" class="protocol-button">
  <h3>UDP</h3>
</a>

<a href="./rtp" class="protocol-button">
  <h3>RTP</h3>
</a>

<a href="./rtsp" class="protocol-button">
  <h3>RTSP</h3>
</a>

<a href="./icecast" class="protocol-button">
  <h3>ICECAST</h3>
</a>

</div>