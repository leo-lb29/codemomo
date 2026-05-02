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
PORT_AUDIO_OUT = 5002
PORT_AUDIO_IN = 5003


class Serveur:
    def __init__(self):
        self.socket = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.socket_audio_out = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_in = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.port_control = PORT_CONTROL
        self.port_audio_out = PORT_AUDIO_OUT
        self.port_audio_in = PORT_AUDIO_IN
        self.clients = []
        self.clients_demandes_parole = []
        self.speaker_id = None
        self.host_is_speaking = False
        self.client_id_counter = 0
        self.audio_queue = []
        self.receiving_audio = False

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
            threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()

    def _handle_client(self, conn, addr):
        try:
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

                while True:
                    try:
                        data = conn.recv(1024).decode()
                        if data == "REQUEST_TO_SPEAK":
                            self.clients_demandes_parole.append((client_id, prenom))
                            print(f"Demande de parole: {prenom}")
                    except:
                        break

                self.clients = [c for c in self.clients if c["id"] != client_id]
                self.clients_demandes_parole = [(cid, p) for cid, p in self.clients_demandes_parole if cid != client_id]
                print(f"Client {prenom} déconnecté")
            else:
                conn.close()
        except Exception as e:
            print(f"Erreur client: {e}")

    def on_demande_la_parole(self):
        pass

    def accepter_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAK_ACCEPTED")
            self.clients_demandes_parole = [(cid, p) for cid, p in self.clients_demandes_parole if cid != id_client]
        self.donner_la_parole(id_client)

    def refuser_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self._envoyer_message(client, "SPEAK_REJECTED")

    def reset_speak(self):
        for client in self.clients:
            self._envoyer_message(client, "RESET_SPEAK")
        self._nettoyer_clients_disconnected()
        self.clients_demandes_parole = []
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

    def demarrer_reception_audio(self):
        try:
            self.socket_audio_in.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
            self.socket_audio_in.bind(("0.0.0.0", self.port_audio_in))
            self.receiving_audio = True
            threading.Thread(target=self._recevoir_et_rediffuser_audio, daemon=True).start()
        except Exception as e:
            print(f"Erreur lors du démarrage de la réception audio: {e}")

    def _recevoir_et_rediffuser_audio(self):
        self.socket_audio_out.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_BROADCAST, 1)
        while self.receiving_audio:
            try:
                data, addr = self.socket_audio_in.recvfrom(65535)
                if data:
                    self.socket_audio_out.sendto(data, ("192.168.1.255", self.port_audio_out))
            except Exception as e:
                if self.receiving_audio:
                    pass



