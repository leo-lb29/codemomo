from textual.widgets import Static, Button as DialogButton
from textual.containers import Vertical as VerticalContainer
from textual.screen import Screen
from textual.widgets import Button, DataTable, Header, Footer, RichLog
from textual.containers import Horizontal, Vertical
from textual.app import App, ComposeResult
import threading
import socket as socket_module
import time

PORT_CONTROL = 5000
PORT_AUDIO = 5002


class Serveur:
    def __init__(self):
        self.socket = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.socket_audio = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.port_control = PORT_CONTROL
        self.port_audio = PORT_AUDIO
        self.clients = []
        self.clients_demandes_parole = []
        self.speaker_id = None
        self.host_is_speaking = False
        self.client_id_counter = 0

    def _nettoyer_clients_disconnected(self):
        self.clients = [c for c in self.clients if self._socket_connected(c["socket"])]

    def _socket_connected(self, sock):
        try:
            sock.getpeername()
            return True
        except:
            return False

    def _envoyer_message(self, client, message_text):
        try:
            message = message_text.encode()
            client["socket"].send(message)
            print(f"Message '{message_text}' envoyé à {client['prenom']}")
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            if client in self.clients:
                self.clients.remove(client)

    def demarrer_serveur(self):
        self.socket.bind(("0.0.0.0", self.port_control))
        self.socket.listen(5)

        while True:
            conn, addr = self.socket.accept()
            print(f"Connexion reçue de {addr}")
            data = conn.recv(1024).decode()
            print(f"Message reçu: {data}")

            if data.startswith("PRENOM:"):
                prenom = data.split(":")[1]
                client_id = self.client_id_counter
                self.client_id_counter += 1
                self.clients.append(
                    {"id": client_id, "addr": addr, "prenom": prenom, "socket": conn})
                print(f"Prénom: {prenom}")
                print(f"Clients connectés: {[c['prenom'] for c in self.clients]}")
            else:
                conn.close()

    def on_demande_la_parole(self):
        pass

    def accepter_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAK_ACCEPTED")
        self.donner_la_parole(id_client)

    def refuser_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAK_REJECTED")

    def reset_speak(self):
        for client in self.clients:
            self._envoyer_message(client, "RESET_SPEAK")
        self._nettoyer_clients_disconnected()
        self.host_is_speaking = False
        self.speaker_id = None

    def arreter_de_parler(self):
        pass

    def prendre_la_parole(self):
        pass

    def couper_le_micro(self):
        pass

    def retirer_la_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAKER:0")
        self.speaker_id = None

    def donner_la_parole(self, id_client):
        self.speaker_id = id_client
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAKER:1")

    def host_start_speaking(self):
        self.host_is_speaking = True
        self.speaker_id = -1

    def host_stop_speaking(self):
        self.host_is_speaking = False
        self.speaker_id = None



