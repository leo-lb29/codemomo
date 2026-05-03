from typing import Any

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


class Serveur:
    def __init__(self):
        self.socket = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.port_control = PORT_CONTROL
        self.clients = []
        self.clients_demandes_parole = []
        self.speaker_id = None
        self.host_is_speaking = False
        self.client_id_counter = 0
        self.app_ref: Any = None

    def nettoyer_clients_disconnected(self):
        self.clients = [
            c for c in self.clients if self.socket_connected(c["socket"])]

    def socket_connected(self, sock):
        try:
            sock.getpeername()
            return True
        except:
            return False

    def envoyer_message(self, client, message_text):
        try:
            message = message_text.encode()
            client["socket"].send(message)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            if client in self.clients:
                self.clients.remove(client)

    def demarrer_serveur(self):
        self.socket.bind(("0.0.0.0", self.port_control))
        self.socket.listen(5)

        while True:
            conn, addr = self.socket.accept()
            self.nettoyer_clients_disconnected()
            threading.Thread(target=self.handle_client,
                             args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode()
            if data.startswith("PRENOM:"):
                prenom = data.split(":")[1]
                client_id = self.client_id_counter
                self.client_id_counter += 1
                self.clients.append(
                    {"id": client_id, "addr": addr, "prenom": prenom, "socket": conn})

                while True:
                    try:
                        data = conn.recv(1024).decode()
                        if data == "REQUEST_TO_SPEAK":
                            self.clients_demandes_parole.append(
                                (client_id, prenom, addr))
                    except:
                        break

                self.clients = [
                    c for c in self.clients if c["id"] != client_id]
                self.clients_demandes_parole = [
                    (cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != client_id]
            else:
                conn.close()
        except Exception as e:
            try:
                conn.close()
            except:
                pass

    def on_demande_la_parole(self):
        pass

    def accepter_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAK_ACCEPTED")
            self.clients_demandes_parole = [
                (cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != id_client]
        self.donner_la_parole(id_client)

    def refuser_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAK_REJECTED")
            self.clients_demandes_parole = [
                (cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != id_client]

    def reset_speak(self):
        for client in self.clients:
            self.envoyer_message(client, "RESET_SPEAK")
        self.speaker_id = None

    def arreter_de_parler(self):
        pass

    def prendre_la_parole(self):
        if not self.host_is_speaking:
            for client in self.clients:
                try: 
                    self.envoyer_message(client, "RESET_SPEAK")
                except:
                    pass
            self.host_is_speaking = True
            self.host_is_speaking = True
            self.speaker_id = -1
            if self.app_ref is not None:
                self.app_ref.query_one(
                    "#btn_host_speak", Button).variant = "success"
                self.app_ref.query_one(
                        "#btn_host_speak", Button).label = "Arreter de parler"
        else:
            self.host_is_speaking = False
            self.speaker_id = None
            if self.app_ref is not None:
                self.app_ref.query_one(
                    "#btn_host_speak", Button).variant = "default"
                self.app_ref.query_one("#btn_host_speak",
                                       Button).label = "Prendre la parole"

    def couper_le_micro(self):
        pass

    def retirer_la_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAKER:0")
        self.speaker_id = None

    def donner_la_parole(self, id_client):
        self.speaker_id = id_client
        self.host_is_speaking = False
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAKER:1")
